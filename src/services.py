import colorsys
import logging
import re
import subprocess
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ServiceStatus:
    name: str
    is_active: bool
    is_failed: bool
    uptime: str | None
    memory: str | None
    cpu: str | None
    last_error: str | None
    full_status: str
    project_group: str
    project_color: str


def get_project_group(service_name: str) -> str:
    name = service_name.replace("projects_", "").replace(".service", "")
    name = name.replace("_site", "")
    name = name.replace("-dashboard", "")
    name = name.replace("-data-backup-scheduler", "")
    name = name.replace("-data-api", "")
    name = name.replace("-scheduler", "")
    return name


def get_project_color(project_group: str) -> str:
    hue = ((hash(project_group) % 1000) * 0.618033988749895) % 1.0
    r, g, b = colorsys.hsv_to_rgb(hue, 0.75, 0.95)
    return f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"


def get_services():
    out = subprocess.check_output(
        ["systemctl", "list-units", "--type=service", "--no-legend", "projects_*"],
        text=True,
    )
    return [line.strip().split()[0] for line in out.strip().splitlines()]


def parse_uptime(status_text):
    match = re.search(r"Active: active \(running\) since .*?; (.*?) ago", status_text)
    return match.group(1) if match else None


def parse_memory(status_text):
    match = re.search(r"Memory: (.*?)(?:\n|$)", status_text)
    return match.group(1).strip() if match else None


def parse_cpu(status_text):
    match = re.search(r"CPU: (.*?)(?:\n|$)", status_text)
    return match.group(1).strip() if match else None


def parse_last_error(status_text):
    match = re.search(r"Error: (.*?)(?:\n|$)", status_text)
    return match.group(1).strip() if match else None


def get_service_info(service: str) -> str:
    result = subprocess.run(
        ["systemctl", "status", service, "--no-pager", "--lines=200"],
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        logger.warning("systemctl status failed for %s: %s", service, result.stderr.strip())
        return result.stdout + "\n" + result.stderr
    return result.stdout


def get_service_status(service):
    status_text = get_service_info(service)
    project_group = get_project_group(service)
    is_active = "active (running)" in status_text.lower()

    return ServiceStatus(
        name=service,
        is_active=is_active,
        is_failed="failed (result: exit-code)" in status_text.lower(),
        uptime=parse_uptime(status_text) if is_active else None,
        memory=parse_memory(status_text),
        cpu=parse_cpu(status_text),
        last_error=parse_last_error(status_text),
        full_status=status_text,
        project_group=project_group,
        project_color=get_project_color(project_group),
    )
