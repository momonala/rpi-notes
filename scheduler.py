import logging
import threading
import time
from datetime import datetime

import schedule

from services import get_service_status
from services import get_services
from telegram import report_error_to_telegram

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Track which services have been alerted today: {service_name: last_alert_date}
_alerted_services: dict[str, datetime] = {}
_alert_lock = threading.Lock()
reset_time = 6  # AM


def _get_current_day() -> datetime:
    """Get the current 'day' for alerting purposes (resets at 6am)."""
    now = datetime.now()
    # If before reset_time, consider it still the previous day
    if now.hour < reset_time:
        return now.replace(hour=0, minute=0, second=0, microsecond=0).replace(day=now.day - 1)
    return now.replace(hour=reset_time, minute=0, second=0, microsecond=0)


def _should_alert(service_name: str) -> bool:
    """Check if we should send an alert for this service (once per day)."""
    with _alert_lock:
        current_day = _get_current_day()
        last_alert = _alerted_services.get(service_name)
        return last_alert is None or last_alert < current_day


def _mark_alerted(service_name: str) -> None:
    """Mark a service as alerted for the current day."""
    with _alert_lock:
        _alerted_services[service_name] = datetime.now()


def service_health_check():
    """Check the health of services and log their status."""
    services = get_services()
    service_statuses = [get_service_status(svc) for svc in services]
    for service_status in service_statuses:
        if service_status.is_failed:
            logger.warning(f"Service {service_status.name} has failed.")
            if _should_alert(service_status.name):
                report_error_to_telegram(service_status)
                _mark_alerted(service_status.name)
                logger.info(f"Alert sent for {service_status.name}")
            else:
                logger.info(f"Alert already sent today for {service_status.name}, skipping.")


def schedule_loop():
    """Schedule the periodic tasks."""
    schedule.every().hour.at(":00").do(service_health_check)
    logger.info("Scheduled hourly service health check")
    while True:
        schedule.run_pending()
        time.sleep(1)


def start_threads():
    """Start the schedule thread."""
    schedule_thread = threading.Thread(target=schedule_loop)
    schedule_thread.start()
    # dont join the threads (blocks main thread which flask runs on)
    logger.info("Initilizaed threads for schedule")


if __name__ == "__main__":
    service_health_check()
