import logging
import re
import subprocess
from dataclasses import dataclass

from flask import Flask, render_template, request, jsonify

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


@app.route("/")
def index():
    service = request.args.get("service")
    services = get_services()

    # Get status for all services
    service_statuses = [get_service_status(svc) for svc in services]

    # Define website links
    websites = [
        {"name": "🏓 pingpong", "url": "https://pingpong.mnalavadi.org", "description": "Shared Expense Trakcer"},
        {"name": "🧗🏽‍♂️ USC-vis", "url": "https://usc-vis.mnalavadi.org/mobile", "description": "USC checkin visualizer"},
        {"name": "🚂 trainspotter", "url": "https://trainspotter.mnalavadi.org", "description": "spot when the next train comes!"},
        {"name": "🚨 inspectordetector", "url": "https://inspectordetector.mnalavadi.org", "description": "Gute Schwartzfahrt!"},
        {"name": "🌏 Trace", "url": "https://trace.mnalavadi.org", "description": "GPS Tracker"},
        {"name": "🤠 img", "url": "https://img.mnalavadi.org", "description": ""},
    ]

    # Get detailed info for selected service if one is selected
    service_info = get_service_info(service) if service else ""

    return render_template(
        "index.html", 
        services=service_statuses, 
        current=service, 
        service_info=service_info,
        websites=websites
    )


@app.route("/restart/<service>", methods=["POST"])
def restart_service(service):
    """Restart a systemd service."""
    try:
        # Validate that the service name starts with "projects_" for security
        if not service.startswith("projects_"):
            return jsonify({"success": False, "error": "Invalid service name"}), 400
        
        # Execute the restart command
        cmd = ["sudo", "systemctl", "restart", service]
        result = subprocess.run(cmd, text=True, capture_output=True, timeout=30)
        
        if result.returncode == 0:
            logging.info(f"Successfully restarted service: {service}")
            return jsonify({"success": True, "message": f"Service {service} restarted successfully"})
        else:
            logging.error(f"Failed to restart service {service}: {result.stderr}")
            return jsonify({"success": False, "error": result.stderr.strip() or "Unknown error"}), 500
            
    except Exception as e:
        logging.error(f"Exception while restarting service {service}: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
