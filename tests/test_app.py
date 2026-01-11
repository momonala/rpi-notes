"""Tests for app.py Flask application."""

import subprocess
from unittest.mock import patch

import pytest

from src.app import app
from src.services import ServiceStatus


@pytest.fixture
def client():
    """Flask test client."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@patch("src.app.is_linux", return_value=True)
@patch("src.app.get_services")
@patch("src.app.get_service_status")
@patch("src.app.get_info_for_service")
def test_index(mock_get_info, mock_get_status, mock_get_services, mock_is_linux, client):
    """Index route renders with services and selected service info."""
    mock_get_services.return_value = ["projects_test1.service", "projects_test2.service"]
    mock_get_status.return_value = ServiceStatus(
        name="projects_test1.service",
        is_active=True,
        is_failed=False,
        uptime="1 day",
        memory="100M",
        cpu="50ms",
        last_error=None,
        full_status="",
        project_group="test1",
    )
    mock_get_info.return_value = ""

    response = client.get("/")
    assert response.status_code == 200
    assert mock_get_status.call_count == 2

    mock_get_info.return_value = "Detailed service info"
    response = client.get("/?service=projects_test1.service")
    assert response.status_code == 200
    mock_get_info.assert_called_with("projects_test1.service")


@patch("src.app.is_linux", return_value=False)
def test_index_non_linux(mock_is_linux, client):
    """Index route uses canned data on non-Linux systems."""
    response = client.get("/")
    assert response.status_code == 200


@patch("src.app.subprocess.run")
def test_restart_service(mock_run, client):
    """Restart service calls systemctl and redirects on success or returns error."""
    mock_run.return_value.returncode = 0
    response = client.post("/restart", data={"service": "projects_test.service"}, follow_redirects=False)
    assert response.status_code == 302
    mock_run.assert_called_once_with(
        ["sudo", "systemctl", "restart", "projects_test.service"],
        check=True,
        text=True,
        capture_output=True,
    )

    mock_run.side_effect = subprocess.CalledProcessError(1, "sudo", stderr="Permission denied")
    response = client.post("/restart", data={"service": "projects_test.service"})
    assert response.status_code == 500
    assert b"Permission denied" in response.data


@patch("src.app.subprocess.run")
def test_train_tracker_check(mock_run, client):
    """Train tracker check runs command and redirects on success or returns error."""
    mock_run.return_value.returncode = 0
    mock_run.return_value.stdout = "Check completed"
    mock_run.return_value.stderr = ""

    response = client.post(
        "/train-tracker/check", data={"service": "projects_train.service"}, follow_redirects=False
    )
    assert response.status_code == 302
    mock_run.assert_called_once_with(
        ["/home/mnalavadi/.local/bin/uv", "run", "-m", "scripts.check_inspections"],
        check=True,
        text=True,
        capture_output=True,
        cwd="/home/mnalavadi/train_tracker",
    )

    mock_run.side_effect = subprocess.CalledProcessError(1, "uv", stderr="Script failed")
    response = client.post("/train-tracker/check", data={"service": "projects_train.service"})
    assert response.status_code == 500
    assert b"Script failed" in response.data
