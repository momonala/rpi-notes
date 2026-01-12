"""Tests for services.py module."""

from unittest.mock import patch

import pytest

from src.canned_info import canned_service_statuses
from src.services import (
    get_info_for_service,
    get_project_group,
    get_service_status,
    get_services,
    parse_cpu,
    parse_last_error,
    parse_memory,
    parse_uptime,
)


@pytest.mark.parametrize(
    "status_text,expected",
    [
        ("Active: active (running) since Mon; 4 days ago", "4 days"),
        ("Active: active (running) since Mon; 2h 15min ago", "2h 15min"),
        ("Active: inactive (dead) since Mon; 4 days ago", None),
        ("", None),
    ],
)
def test_parse_uptime(status_text, expected):
    """Parse uptime extracts duration from active services only."""
    assert parse_uptime(status_text) == expected


@pytest.mark.parametrize(
    "status_text,expected",
    [
        ("Memory: 123.4M\n", "123.4M"),
        ("Memory: 1.2G\nCPU: 100ms", "1.2G"),
        ("No memory info", None),
    ],
)
def test_parse_memory(status_text, expected):
    """Parse memory extracts memory usage or None."""
    assert parse_memory(status_text) == expected


@pytest.mark.parametrize(
    "status_text,expected",
    [
        ("CPU: 1h 23min 45.678s\nMemory: 100M", "1h 23min 45.678s"),
        ("No cpu info", None),
    ],
)
def test_parse_cpu(status_text, expected):
    """Parse CPU extracts CPU time or None."""
    assert parse_cpu(status_text) == expected


@pytest.mark.parametrize(
    "status_text,expected",
    [
        ("Error: Service failed\n", "Service failed"),
        ("Error: Command returned exit code 1\nOther info", "Command returned exit code 1"),
        ("No errors here", None),
    ],
)
def test_parse_last_error(status_text, expected):
    """Parse last error extracts error messages or None."""
    assert parse_last_error(status_text) == expected


@pytest.mark.parametrize(
    "service",
    canned_service_statuses,
)
def test_get_project_group(service):
    """Project group strips service prefixes and suffixes."""
    assert get_project_group(service.name) == service.project_group


@patch("src.services.subprocess.check_output")
def test_get_services(mock_check_output):
    """Parse systemctl list-units output and handle empty output."""
    mock_check_output.return_value = (
        "projects_test1.service       loaded active running   Test Service 1\n"
        "projects_test2.service       loaded active running   Test Service 2\n"
    )
    assert get_services() == ["projects_test1.service", "projects_test2.service"]

    mock_check_output.return_value = ""
    assert get_services() == []


@patch("src.services.subprocess.run")
def test_get_info_for_service(mock_run):
    """Return stdout on success, stdout+stderr on failure."""
    mock_run.return_value.returncode = 0
    mock_run.return_value.stdout = "Service is running"
    mock_run.return_value.stderr = ""
    assert get_info_for_service("test.service") == "Service is running"

    mock_run.return_value.returncode = 3
    mock_run.return_value.stdout = "Unit not found"
    mock_run.return_value.stderr = "Failed"
    assert get_info_for_service("test.service") == "Unit not found\nFailed"


@patch("src.services.get_info_for_service")
def test_get_service_status(mock_get_info):
    """Parse service status for active, failed, and inactive services."""
    mock_get_info.return_value = (
        "Active: active (running) since Mon; 4 days ago\n" "Memory: 123.4M\n" "CPU: 2min 15.678s\n"
    )
    status = get_service_status("projects_test.service")
    assert status.is_active and not status.is_failed
    assert status.uptime == "4 days" and status.memory == "123.4M"
    assert status.project_group == "test"

    mock_get_info.return_value = "Active: failed (Result: exit-code)\nError: Connection refused\n"
    status = get_service_status("projects_test.service")
    assert not status.is_active and status.is_failed
    assert status.last_error == "Connection refused"

    mock_get_info.return_value = "Active: inactive (dead)\n"
    status = get_service_status("projects_test.service")
    assert not status.is_active and not status.is_failed
