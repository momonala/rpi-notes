"""Tests for app.py Flask application."""

import subprocess
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from app import app


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def mock_services():
    """Mock list of services."""
    return ["projects_test1.service", "projects_test2.service", "projects_train_tracker.service"]


def test_index_get_no_service(client, mock_services):
    """Test index route without service parameter."""
    with (
        patch("app.get_services", return_value=mock_services),
        patch("app.get_service_status") as mock_status,
        patch("app.get_service_info", return_value=""),
    ):
        mock_status.side_effect = lambda svc: MagicMock(
            name=svc,
            is_active=True,
            is_failed=False,
            uptime="1 day",
            memory="100M",
            cpu="50ms",
            last_error=None,
        )

        response = client.get("/")
        assert response.status_code == 200
        # Verify get_service_status was called for each service
        assert mock_status.call_count == len(mock_services)


def test_index_get_with_service(client, mock_services):
    """Test index route with service parameter."""
    with (
        patch("app.get_services", return_value=mock_services),
        patch("app.get_service_status") as mock_status,
        patch("app.get_service_info", return_value="Service info output") as mock_info,
    ):
        mock_status.side_effect = lambda svc: MagicMock(
            name=svc,
            is_active=True,
            is_failed=False,
            uptime="1 day",
            memory="100M",
            cpu="50ms",
            last_error=None,
        )

        response = client.get("/?service=projects_test1.service")
        assert response.status_code == 200
        # Verify get_service_info was called with the selected service
        mock_info.assert_called_once_with("projects_test1.service")


def test_index_websites_present(client, mock_services):
    """Test that websites are included in the response."""
    with (
        patch("app.get_services", return_value=mock_services),
        patch("app.get_service_status") as mock_status,
        patch("app.get_service_info", return_value=""),
    ):
        mock_status.side_effect = lambda svc: MagicMock(
            name=svc,
            is_active=True,
            is_failed=False,
            uptime="1 day",
            memory="100M",
            cpu="50ms",
            last_error=None,
        )

        response = client.get("/")
        assert response.status_code == 200
        # Verify the response contains HTML (template was rendered)
        assert b"<!DOCTYPE html>" in response.data or b"<html" in response.data


def test_restart_service_success(client, mock_services):
    """Test restarting a service successfully."""
    with patch("app.get_services", return_value=mock_services), patch("app.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)

        response = client.post("/restart", data={"service": "projects_test1.service"}, follow_redirects=False)

        assert response.status_code == 302  # Redirect
        mock_run.assert_called_once_with(
            ["sudo", "systemctl", "restart", "projects_test1.service"],
            check=True,
            text=True,
            capture_output=True,
        )


def test_restart_service_invalid_service(client, mock_services):
    """Test restarting an invalid service."""
    with patch("app.get_services", return_value=mock_services):
        response = client.post("/restart", data={"service": "invalid_service.service"})

        assert response.status_code == 400
        assert b"Invalid service" in response.data


def test_restart_service_missing_service_param(client, mock_services):
    """Test restarting without service parameter."""
    with patch("app.get_services", return_value=mock_services):
        response = client.post("/restart", data={})

        assert response.status_code == 400
        assert b"Invalid service" in response.data


def test_restart_service_subprocess_failure(client, mock_services):
    """Test restarting when subprocess fails."""
    with patch("app.get_services", return_value=mock_services), patch("app.subprocess.run") as mock_run:
        mock_error = subprocess.CalledProcessError(1, "sudo", stderr="Permission denied")
        mock_run.side_effect = mock_error

        response = client.post("/restart", data={"service": "projects_test1.service"})

        assert response.status_code == 500
        assert b"Permission denied" in response.data or b"Failed to restart" in response.data


def test_restart_service_get_services_exception(client):
    """Test restart when get_services raises an exception."""
    with patch("app.get_services", side_effect=Exception("System error")):
        response = client.post("/restart", data={"service": "projects_test1.service"})

        assert response.status_code == 500
        assert b"Failed to list services" in response.data


def test_train_tracker_check_success(client):
    """Test train tracker check successfully."""
    with patch("app.subprocess.run") as mock_run:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Check completed"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        response = client.post(
            "/train-tracker/check", data={"service": "projects_train_tracker.service"}, follow_redirects=False
        )

        assert response.status_code == 302  # Redirect
        mock_run.assert_called_once_with(
            [
                "/home/mnalavadi/.local/bin/uv",
                "run",
                "-m",
                "scripts.check_inspections",
            ],
            check=True,
            text=True,
            capture_output=True,
            cwd="/home/mnalavadi/train_tracker",
        )


def test_train_tracker_check_wrong_service(client):
    """Test train tracker check with wrong service."""
    response = client.post("/train-tracker/check", data={"service": "projects_test1.service"})

    assert response.status_code == 400
    assert b"Invalid service" in response.data


def test_train_tracker_check_missing_service(client):
    """Test train tracker check without service parameter."""
    response = client.post("/train-tracker/check", data={})

    assert response.status_code == 400
    assert b"Invalid service" in response.data


def test_train_tracker_check_subprocess_failure(client):
    """Test train tracker check when subprocess fails."""
    with patch("app.subprocess.run") as mock_run:
        mock_error = subprocess.CalledProcessError(1, "python", stderr="Script failed")
        mock_run.side_effect = mock_error

        response = client.post("/train-tracker/check", data={"service": "projects_train_tracker.service"})

        assert response.status_code == 500
        assert b"Script failed" in response.data or b"Train-tracker check failed" in response.data


def test_train_tracker_check_with_stderr(client):
    """Test train tracker check with stderr output."""
    with patch("app.subprocess.run") as mock_run:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Check completed"
        mock_result.stderr = "Warning message"
        mock_run.return_value = mock_result

        response = client.post(
            "/train-tracker/check", data={"service": "projects_train_tracker.service"}, follow_redirects=False
        )

        assert response.status_code == 302  # Should still succeed with warnings
