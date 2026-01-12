import logging
import platform
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


def get_project_group(service_name: str) -> str:
    service_name = service_name.replace(".service", "")
    service_name = service_name.replace("projects_", "")
    project = service_name.split("_")[0]
    return project


def is_linux():
    return platform.system() == "Linux"


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


def get_info_for_service(service: str) -> str:
    result = subprocess.run(
        ["systemctl", "status", service, "--no-pager", "--lines=1000"],
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        logger.warning("systemctl status failed for %s: %s", service, result.stderr.strip())
        return result.stdout + "\n" + result.stderr
    return result.stdout


def get_service_status(service):
    status_text = get_info_for_service(service)
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
    )
