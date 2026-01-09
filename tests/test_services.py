"""Tests for services.py module."""

from unittest.mock import MagicMock, patch

import pytest

from src.services import (
    get_project_color,
    get_project_group,
    get_service_info,
    get_service_status,
    get_services,
    parse_cpu,
    parse_last_error,
    parse_memory,
    parse_uptime,
)


@patch("src.services.subprocess.check_output")
def test_get_services(mock_check_output):
    """Get services parses systemctl output correctly."""
    mock_check_output.return_value = (
        "projects_test1.service loaded active running\n" " projects_test2.service loaded active running\n"
    )
    assert get_services() == ["projects_test1.service", "projects_test2.service"]


@pytest.mark.parametrize(
    "parse_fn,text,expected",
    [
        (parse_uptime, "Active: active (running) since Mon; 4 days ago", "4 days"),
        (parse_uptime, "Active: inactive", None),
        (parse_memory, "Memory: 123.4M\n", "123.4M"),
        (parse_memory, "No memory", None),
        (parse_cpu, "CPU: 123ms\n", "123ms"),
        (parse_cpu, "No cpu", None),
        (parse_last_error, "Error: Service failed\n", "Service failed"),
        (parse_last_error, "No errors", None),
    ],
)
def test_parse_functions(parse_fn, text, expected):
    """Parse functions extract values or return None."""
    assert parse_fn(text) == expected


@patch("src.services.subprocess.run")
def test_get_service_info(mock_run):
    """Get service info returns stdout, or stdout+stderr on error."""
    mock_run.return_value = MagicMock(returncode=0, stdout="output", stderr="")
    assert get_service_info("test.service") == "output"

    mock_run.return_value = MagicMock(returncode=1, stdout="out", stderr="err")
    assert get_service_info("test.service") == "out\nerr"


@patch("src.services.get_service_info")
def test_get_service_status_active(mock_get_info):
    """Active services have correct status fields."""
    mock_get_info.return_value = (
        "Active: active (running) since Mon; 4 days ago\n" "Memory: 123.4M\n" "CPU: 123ms\n"
    )
    result = get_service_status("projects_test.service")

    assert result.is_active
    assert not result.is_failed
    assert result.uptime == "4 days"


@patch("src.services.get_service_info")
def test_get_service_status_failed(mock_get_info):
    """Failed services are detected correctly."""
    mock_get_info.return_value = "Active: failed (result: exit-code)\nError: Failed\n"
    result = get_service_status("projects_test.service")

    assert not result.is_active
    assert result.is_failed
    assert result.last_error == "Failed"


@pytest.mark.parametrize(
    "service_name,expected_group",
    [
        ("projects_atc_tour_extension.service", "atc_tour_extension"),
        ("projects_energy_monitor.service", "energy_monitor"),
        ("projects_flight_calendar_updater.service", "flight_calendar_updater"),
        ("projects_incognita-dashboard.service", "incognita"),
        ("projects_incognita-data-api.service", "incognita"),
        ("projects_incognita-data-backup-scheduler.service", "incognita"),
        ("projects_ios-health-dump.service", "ios-health-dump"),
        ("projects_ios-health-dump-data-backup-scheduler.service", "ios-health-dump"),
        ("projects_pingpong.service", "pingpong"),
        ("projects_servicemonitor.service", "servicemonitor"),
        ("projects_task-manager.service", "task-manager"),
        ("projects_task-manager-data-backup-scheduler.service", "task-manager"),
        ("projects_train_tracker.service", "train_tracker"),
        ("projects_train_tracker_site.service", "train_tracker"),
        ("projects_trainspotter.service", "trainspotter"),
        ("projects_usc-vis.service", "usc-vis"),
        ("projects_usc-vis-data-backup-scheduler.service", "usc-vis"),
        ("projects_wordle_alarm.service", "wordle_alarm"),
    ],
)
def test_get_project_group(service_name, expected_group):
    assert get_project_group(service_name) == expected_group


def test_get_project_color_deterministic():
    """Same project always gets same color."""
    assert get_project_color("test") == get_project_color("test")


def test_get_project_color_valid_hex():
    """Colors are valid hex codes."""
    color = get_project_color("test")
    assert color.startswith("#")
    assert len(color) == 7
    int(color[1:], 16)  # Raises if not valid hex
