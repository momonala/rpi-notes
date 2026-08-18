"""Cloudflare R2 usage for the current billing month, against R2's free tier.

Storage comes from R2's REST usage endpoint (one call per bucket, current point-in-time size).
Class A/B request counts come from the GraphQL Analytics API (`r2OperationsAdaptiveGroups`),
summed across the account for the current calendar month — R2 bills by calendar month, so that's
the window that matters. This app has no R2 access of its own; it only reports usage against
Cloudflare's published free tier (https://developers.cloudflare.com/r2/pricing/) so a runaway
process shows up here before it shows up on a bill.
"""

import logging
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timezone

import requests

from src.values import CLOUDFLARE_ACCOUNT_ID, CLOUDFLARE_API_TOKEN

logger = logging.getLogger(__name__)

API_BASE = "https://api.cloudflare.com/client/v4"
GRAPHQL_URL = f"{API_BASE}/graphql"
# Every bucket on this account was created in the EU jurisdiction; the default (no-jurisdiction)
# bucket listing returns empty, so this header is required to see any of them.
R2_JURISDICTION_HEADER = {"cf-r2-jurisdiction": "eu"}
REQUEST_TIMEOUT_SECONDS = 15
MAX_USAGE_WORKERS = 8
CACHE_TTL_SECONDS = 300.0

# Standard storage only — https://developers.cloudflare.com/r2/pricing/. "GB" here is decimal
# (1e9 bytes), matching how cloud storage billing is usually quoted; treat the percentages below
# as close approximations, not the exact figure Cloudflare bills.
FREE_TIER_STORAGE_BYTES = 10 * 1_000_000_000  # 10 GB-month
FREE_TIER_CLASS_A_REQUESTS = 1_000_000
FREE_TIER_CLASS_B_REQUESTS = 10_000_000

# https://developers.cloudflare.com/r2/platform/pricing/#operations — DeleteObject, DeleteBucket,
# and AbortMultipartUpload are free and deliberately excluded from both classes.
CLASS_A_ACTIONS = frozenset(
    {
        "ListBuckets",
        "PutBucket",
        "ListObjects",
        "PutObject",
        "CopyObject",
        "CompleteMultipartUpload",
        "CreateMultipartUpload",
        "LifecycleStorageTierTransition",
        "ListMultipartUploads",
        "UploadPart",
        "UploadPartCopy",
        "ListParts",
        "PutBucketEncryption",
        "PutBucketCors",
        "PutBucketLifecycleConfiguration",
    }
)
CLASS_B_ACTIONS = frozenset(
    {
        "HeadBucket",
        "HeadObject",
        "GetObject",
        "UsageSummary",
        "GetBucketEncryption",
        "GetBucketLocation",
        "GetBucketCors",
        "GetBucketLifecycleConfiguration",
    }
)

_OPERATIONS_QUERY = """
query R2Operations($accountTag: string!, $startDate: Time, $endDate: Time) {
  viewer {
    accounts(filter: {accountTag: $accountTag}) {
      r2OperationsAdaptiveGroups(
        limit: 10000
        filter: {datetime_geq: $startDate, datetime_leq: $endDate}
      ) {
        sum { requests }
        dimensions { actionType }
      }
    }
  }
}
"""

_cache: tuple[float, "R2UsageSummary | None"] | None = None


@dataclass
class R2UsageSummary:
    storage_bytes: int
    storage_pct: float
    class_a_requests: int
    class_a_pct: float
    class_b_requests: int
    class_b_pct: float


def _api_get(path: str) -> dict | None:
    try:
        response = requests.get(
            f"{API_BASE}{path}",
            headers={"Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}", **R2_JURISDICTION_HEADER},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.warning("Cloudflare API request failed (%s): %s", path, exc)
        return None
    payload = response.json()
    if not payload.get("success"):
        logger.warning("Cloudflare API returned an error for %s: %s", path, payload.get("errors"))
        return None
    return payload["result"]


def _list_bucket_names() -> list[str] | None:
    result = _api_get(f"/accounts/{CLOUDFLARE_ACCOUNT_ID}/r2/buckets?per_page=1000")
    if result is None:
        return None
    return [bucket["name"] for bucket in result.get("buckets", [])]


def _fetch_bucket_storage_bytes(bucket_name: str) -> int | None:
    """Current stored bytes (Standard + Infrequent Access, payload + metadata) for one bucket."""
    result = _api_get(f"/accounts/{CLOUDFLARE_ACCOUNT_ID}/r2/buckets/{bucket_name}/usage")
    if result is None:
        return None
    size_fields = (
        "payloadSize",
        "metadataSize",
        "infrequentAccessPayloadSize",
        "infrequentAccessMetadataSize",
    )
    return sum(int(result[field]) for field in size_fields)


def _fetch_total_storage_bytes() -> int | None:
    """Sum of every bucket's current size.

    None (not a partial sum) if any bucket's usage is unreachable — a partial total would look
    like real headroom against the free tier when it might not be.
    """
    bucket_names = _list_bucket_names()
    if bucket_names is None:
        return None
    if not bucket_names:
        return 0
    with ThreadPoolExecutor(max_workers=min(MAX_USAGE_WORKERS, len(bucket_names))) as pool:
        per_bucket_bytes = list(pool.map(_fetch_bucket_storage_bytes, bucket_names))
    if any(size is None for size in per_bucket_bytes):
        return None
    return sum(per_bucket_bytes)


def _fetch_operation_counts_this_month() -> dict[str, int] | None:
    """{actionType: request count} for the account, from the 1st of this month to now."""
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    try:
        response = requests.post(
            GRAPHQL_URL,
            headers={"Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}"},
            json={
                "query": _OPERATIONS_QUERY,
                "variables": {
                    "accountTag": CLOUDFLARE_ACCOUNT_ID,
                    "startDate": month_start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "endDate": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
                },
            },
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.warning("Cloudflare GraphQL request failed: %s", exc)
        return None
    payload = response.json()
    if payload.get("errors"):
        logger.warning("Cloudflare GraphQL returned errors: %s", payload["errors"])
        return None
    groups = payload["data"]["viewer"]["accounts"][0]["r2OperationsAdaptiveGroups"]
    return {group["dimensions"]["actionType"]: group["sum"]["requests"] for group in groups}


def fetch_r2_usage_summary() -> R2UsageSummary | None:
    """Month-to-date R2 usage against the free tier, or None if unconfigured/unreachable.

    Cached for CACHE_TTL_SECONDS: a fresh read costs one bucket-list call, one usage call per
    bucket (parallelized), and one GraphQL call.
    """
    global _cache
    now_monotonic = time.monotonic()
    if _cache is not None:
        cached_at, cached_value = _cache
        if now_monotonic - cached_at < CACHE_TTL_SECONDS:
            return cached_value

    summary = None
    if CLOUDFLARE_API_TOKEN:
        storage_bytes = _fetch_total_storage_bytes()
        operation_counts = _fetch_operation_counts_this_month()
        if storage_bytes is not None and operation_counts is not None:
            class_a = sum(count for action, count in operation_counts.items() if action in CLASS_A_ACTIONS)
            class_b = sum(count for action, count in operation_counts.items() if action in CLASS_B_ACTIONS)
            summary = R2UsageSummary(
                storage_bytes=storage_bytes,
                storage_pct=round(storage_bytes / FREE_TIER_STORAGE_BYTES * 100, 2),
                class_a_requests=class_a,
                class_a_pct=round(class_a / FREE_TIER_CLASS_A_REQUESTS * 100, 2),
                class_b_requests=class_b,
                class_b_pct=round(class_b / FREE_TIER_CLASS_B_REQUESTS * 100, 2),
            )

    _cache = (now_monotonic, summary)
    return summary
