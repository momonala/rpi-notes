import logging
import re
import subprocess
from dataclasses import dataclass

from flask import Flask
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)


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


def get_services():
    """Get list of project services from systemd."""
    cmd = ["systemctl", "list-units", "--type=service", "--no-legend", "projects_*"]
    out = subprocess.check_output(cmd, text=True)
    services = []
    for line in out.strip().splitlines():
        if not line.startswith("projects_"):
            line = line[1:]
        service = line.split()[0]
        logging.info(f"Found {service=}")
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
        logging.warning(f"Command '{' '.join(cmd)}' got {result.returncode=}: {result.stderr.strip()}")
        return result.stdout + "\n" + result.stderr


def get_service_status(service):
    """Get status information for a service."""
    status_text = get_service_info(service)
    return ServiceStatus(
        name=service,
        is_active="active (running)" in status_text.lower(),
        is_failed="failed" in status_text.lower(),
        uptime=parse_uptime(status_text) if "active (running)" in status_text.lower() else None,
        memory=parse_memory(status_text),
        cpu=parse_cpu(status_text),
        last_error=parse_last_error(status_text),
    )


@app.route("/restart", methods=["POST"])
def restart_service():
    """Restart a given service and redirect back to the index view."""
    service = request.form.get("service", "")
    try:
        services = get_services()
    except Exception as exc:
        logging.exception("Failed to list services: %s", exc)
        return "Failed to list services", 500

    if service not in services:
        logging.warning("Attempt to restart unknown or disallowed service: %s", service)
        return "Invalid service", 400

    try:
        # Requires appropriate sudoers configuration for the running user
        subprocess.run(["sudo", "systemctl", "restart", service], check=True, text=True, capture_output=True)
        logging.info("Successfully restarted service %s", service)
    except subprocess.CalledProcessError as exc:
        logging.error("Failed to restart %s: %s", service, exc.stderr)
        return (exc.stderr or f"Failed to restart {service}"), 500

    return redirect(url_for("index", service=service))


@app.route("/train-tracker/check", methods=["POST"])
def train_tracker_check():
    """Run the train tracker inspections check command."""
    service = request.form.get("service", "")
    if service != "projects_train_tracker.service":
        logging.warning("Attempt to run train-tracker check for wrong service: %s", service)
        return "Invalid service", 400

    cmd = [
        "/home/mnalavadi/miniconda3/envs/train_tracker/bin/python",
        "-m",
        "scripts.check_inspections",
    ]

    try:
        result = subprocess.run(
            cmd, check=True, text=True, capture_output=True, cwd="/home/mnalavadi/train_tracker"
        )
        logging.info("Train-tracker check completed. stdout: %s", (result.stdout or "").strip())
        if result.stderr:
            logging.info("Train-tracker check stderr: %s", result.stderr.strip())
    except subprocess.CalledProcessError as exc:
        logging.error("Train-tracker check failed: %s", exc.stderr)
        return (exc.stderr or "Train-tracker check failed"), 500

    return redirect(url_for("index", service=service))


@app.route("/")
def index():
    service = request.args.get("service")
    services = get_services()

    # Get status for all services
    service_statuses = [get_service_status(svc) for svc in services]

    # Website links with icons (icon mapping centralized here, not in template)
    websites = [
        {
            "name": "energyMonitor",
            "url": "https://energy-monitor.mnalavadi.org",
            "description": "Energy Monitor",
            "icon": "⚡️",
        },
        {
            "name": "pingpong",
            "url": "https://pingpong.mnalavadi.org",
            "description": "Shared Expense Tracker",
            "icon": "🏓",
        },
        {
            "name": "USC-vis",
            "url": "https://usc-vis.mnalavadi.org/mobile",
            "description": "USC checkin visualizer",
            "icon": "💪🏾",
        },
        {
            "name": "trainspotter",
            "url": "https://trainspotter.mnalavadi.org",
            "description": "Spot when the next train comes!",
            "icon": "🚃",
        },
        {
            "name": "inspectordetector",
            "url": "https://inspectordetector.mnalavadi.org",
            "description": "Gute Schwarzfahrt!",
            "icon": "🚨",
        },
        {"name": "Trace", "url": "https://trace.mnalavadi.org", "description": "GPS Tracker", "icon": "📍"},
    ]
    websites.sort(key=lambda x: x["name"].lower())

    # Get detailed info for selected service if one is selected
    service_info = get_service_info(service) if service else ""

    return render_template(
        "index.html", services=service_statuses, current=service, service_info=service_info, websites=websites
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
