"""Tests for r2_usage.py module."""

from unittest.mock import patch

import pytest

import src.r2_usage as r2_usage_module
from src.r2_usage import (
    CLASS_A_ACTIONS,
    CLASS_B_ACTIONS,
    _fetch_bucket_storage_bytes,
    _fetch_total_storage_bytes,
    _list_bucket_names,
    fetch_r2_usage_summary,
)


@pytest.fixture(autouse=True)
def reset_r2_usage_cache():
    r2_usage_module._cache = None
    yield


def test_class_a_and_class_b_actions_do_not_overlap():
    """A class A action being misclassified as class B (or vice versa) would silently corrupt
    the quota math, so this must hold even as the action lists are updated in the future."""
    assert CLASS_A_ACTIONS.isdisjoint(CLASS_B_ACTIONS)


@patch("src.r2_usage._api_get")
def test_list_bucket_names(mock_api_get):
    mock_api_get.return_value = {"buckets": [{"name": "a"}, {"name": "b"}]}
    assert _list_bucket_names() == ["a", "b"]


@patch("src.r2_usage._api_get", return_value=None)
def test_list_bucket_names_returns_none_on_api_failure(mock_api_get):
    assert _list_bucket_names() is None


@patch("src.r2_usage._api_get")
def test_fetch_bucket_storage_bytes_sums_standard_and_infrequent_access(mock_api_get):
    mock_api_get.return_value = {
        "payloadSize": "100",
        "metadataSize": "10",
        "infrequentAccessPayloadSize": "5",
        "infrequentAccessMetadataSize": "1",
    }
    assert _fetch_bucket_storage_bytes("a") == 116


@patch("src.r2_usage._fetch_bucket_storage_bytes")
@patch("src.r2_usage._list_bucket_names", return_value=["a", "b"])
def test_fetch_total_storage_bytes_sums_all_buckets(mock_list_buckets, mock_fetch_bytes):
    mock_fetch_bytes.side_effect = [100, 200]
    assert _fetch_total_storage_bytes() == 300


@patch("src.r2_usage._fetch_bucket_storage_bytes")
@patch("src.r2_usage._list_bucket_names", return_value=["a", "b"])
def test_fetch_total_storage_bytes_none_if_any_bucket_unreachable(mock_list_buckets, mock_fetch_bytes):
    """A partial sum would understate real usage against the free tier, so one unreachable bucket
    fails the whole total rather than silently omitting it."""
    mock_fetch_bytes.side_effect = [100, None]
    assert _fetch_total_storage_bytes() is None


@patch("src.r2_usage._list_bucket_names", return_value=None)
def test_fetch_total_storage_bytes_none_if_bucket_list_unreachable(mock_list_buckets):
    assert _fetch_total_storage_bytes() is None


@patch("src.r2_usage._list_bucket_names", return_value=[])
def test_fetch_total_storage_bytes_zero_when_no_buckets(mock_list_buckets):
    assert _fetch_total_storage_bytes() == 0


@patch("src.r2_usage._fetch_operation_counts_this_month")
@patch("src.r2_usage._fetch_total_storage_bytes")
@patch("src.r2_usage.CLOUDFLARE_API_TOKEN", "fake-token")
def test_fetch_r2_usage_summary_computes_percentages(mock_storage, mock_operations):
    mock_storage.return_value = 1_000_000_000  # 1 GB of the 10 GB free tier
    mock_operations.return_value = {"PutObject": 10_000, "GetObject": 100_000, "DeleteObject": 999_999}

    summary = fetch_r2_usage_summary()

    assert summary.storage_bytes == 1_000_000_000
    assert summary.storage_pct == 10.0
    assert summary.class_a_requests == 10_000
    assert summary.class_a_pct == 1.0
    assert summary.class_b_requests == 100_000
    assert summary.class_b_pct == 1.0


@patch("src.r2_usage.CLOUDFLARE_API_TOKEN", None)
def test_fetch_r2_usage_summary_none_without_token():
    assert fetch_r2_usage_summary() is None


@patch("src.r2_usage._fetch_operation_counts_this_month", return_value=None)
@patch("src.r2_usage._fetch_total_storage_bytes", return_value=100)
@patch("src.r2_usage.CLOUDFLARE_API_TOKEN", "fake-token")
def test_fetch_r2_usage_summary_none_when_operations_unavailable(mock_storage, mock_operations):
    assert fetch_r2_usage_summary() is None


@patch("src.r2_usage._fetch_operation_counts_this_month", return_value={})
@patch("src.r2_usage._fetch_total_storage_bytes", return_value=100)
@patch("src.r2_usage.CLOUDFLARE_API_TOKEN", "fake-token")
def test_fetch_r2_usage_summary_caches_within_ttl(mock_storage, mock_operations):
    fetch_r2_usage_summary()
    fetch_r2_usage_summary()
    assert mock_storage.call_count == 1
