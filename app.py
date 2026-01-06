import logging
import subprocess

from flask import Flask
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for

from scheduler import start_threads
from services import get_service_info
from services import get_service_status
from services import get_services

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)


@app.route("/restart", methods=["POST"])
def restart_service():
    """Restart a given service and redirect back to the index view."""
    service = request.form.get("service", "")
    try:
        services = get_services()
    except Exception as exc:
        logger.exception("Failed to list services: %s", exc)
        return "Failed to list services", 500

    if service not in services:
        logger.warning("Attempt to restart unknown or disallowed service: %s", service)
        return "Invalid service", 400

    try:
        # Requires appropriate sudoers configuration for the running user
        subprocess.run(["sudo", "systemctl", "restart", service], check=True, text=True, capture_output=True)
        logger.info("Successfully restarted service %s", service)
    except subprocess.CalledProcessError as exc:
        logger.error("Failed to restart %s: %s", service, exc.stderr)
        return (exc.stderr or f"Failed to restart {service}"), 500

    return redirect(url_for("index", service=service))


@app.route("/train-tracker/check", methods=["POST"])
def train_tracker_check():
    """Run the train tracker inspections check command."""
    service = request.form.get("service", "")
    if service != "projects_train_tracker.service":
        logger.warning("Attempt to run train-tracker check for wrong service: %s", service)
        return "Invalid service", 400

    cmd = [
        "/home/mnalavadi/.local/bin/uv",
        "run",
        "-m",
        "scripts.check_inspections",
    ]

    try:
        result = subprocess.run(
            cmd, check=True, text=True, capture_output=True, cwd="/home/mnalavadi/train_tracker"
        )
        logger.info("Train-tracker check completed. stdout: %s", (result.stdout or "").strip())
        if result.stderr:
            logger.warning("Train-tracker check stderr: %s", result.stderr.strip())
    except subprocess.CalledProcessError as exc:
        logger.error("Train-tracker check failed: %s", exc.stderr)
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
            "url": "https://usc-vis.mnalavadi.org",
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
        {
            "name": "iOS Health Dump",
            "url": "https://ios-health-dump.mnalavadi.org",
            "description": "Data from iOS Health app",
            "icon": "⚕️",
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
    start_threads()
    app.run(host="0.0.0.0", port=5001, debug=True)
