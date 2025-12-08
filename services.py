import logging
import re
import subprocess
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ServiceStatus:
    """Service status information."""

    name: str
    is_active: bool
    is_failed: bool
    uptime: str | None
    memory: str | None
    cpu: str | None
    last_error: str | None
    full_status: str


def get_services():
    """Get list of project services from systemd."""
    cmd = ["systemctl", "list-units", "--type=service", "--no-legend", "projects_*"]
    out = subprocess.check_output(cmd, text=True)
    services = []
    for line in out.strip().splitlines():
        if not line.startswith("projects_"):
            line = line[1:]
        service = line.split()[0]
        services.append(service)
    return services


def parse_uptime(status_text):
    """Parse uptime from systemctl status output."""
    # Look for patterns like "Active: active (running) since Mon 2024-03-18 10:00:00 UTC; 4 days ago"
    match = re.search(r"Active: active \(running\) since .*?; (.*?) ago", status_text)
    if match:
        return match.group(1)
    return None


def parse_memory(status_text):
    """Parse memory usage from systemctl status output."""
    match = re.search(r"Memory: (.*?)(?:\n|$)", status_text)
    if match:
        return match.group(1).strip()
    return None


def parse_cpu(status_text):
    """Parse CPU usage from systemctl status output."""
    match = re.search(r"CPU: (.*?)(?:\n|$)", status_text)
    if match:
        return match.group(1).strip()
    return None


def parse_last_error(status_text):
    """Parse last error from systemctl status output."""
    # Look for the last error message in the status output
    error_match = re.search(r"Error: (.*?)(?:\n|$)", status_text)
    if error_match:
        return error_match.group(1).strip()
    return None


def get_service_info(service: str) -> str:
    """Return combined status and logs for a service, or error output if the command fails."""
    cmd = ["systemctl", "status", service, "--no-pager", "--lines=200"]
    result = subprocess.run(cmd, text=True, capture_output=True)
    if result.returncode == 0:
        return result.stdout
    else:
        logger.warning(f"Command '{' '.join(cmd)}' got {result.returncode=}: {result.stderr.strip()}")
        return result.stdout + "\n" + result.stderr


def get_service_status(service):
    """Get status information for a service."""
    status_text = get_service_info(service)
    return ServiceStatus(
        name=service,
        is_active="active (running)" in status_text.lower(),
        is_failed="failed (result: exit-code)" in status_text.lower(),
        uptime=parse_uptime(status_text) if "active (running)" in status_text.lower() else None,
        memory=parse_memory(status_text),
        cpu=parse_cpu(status_text),
        last_error=parse_last_error(status_text),
        full_status=status_text,
    )
