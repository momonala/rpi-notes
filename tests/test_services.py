"""Tests for services.py module."""

from unittest.mock import MagicMock
from unittest.mock import patch


from services import ServiceStatus
from services import get_service_info
from services import get_service_status
from services import get_services
from services import parse_cpu
from services import parse_last_error
from services import parse_memory
from services import parse_uptime


class TestGetServices:
    """Tests for get_services function."""

    @patch("services.subprocess.check_output")
    def test_get_services_success(self, mock_check_output):
        """Test getting services successfully."""
        mock_check_output.return_value = (
            "projects_test1.service loaded active running\n" "projects_test2.service loaded active running\n"
        )
        result = get_services()
        assert result == ["projects_test1.service", "projects_test2.service"]
        mock_check_output.assert_called_once_with(
            ["systemctl", "list-units", "--type=service", "--no-legend", "projects_*"], text=True
        )

    @patch("services.subprocess.check_output")
    def test_get_services_empty(self, mock_check_output):
        """Test getting services when none exist."""
        mock_check_output.return_value = ""
        result = get_services()
        assert result == []

    @patch("services.subprocess.check_output")
    def test_get_services_with_leading_space(self, mock_check_output):
        """Test handling services with leading space."""
        mock_check_output.return_value = " projects_test.service loaded active running\n"
        result = get_services()
        assert result == ["projects_test.service"]


class TestParseUptime:
    """Tests for parse_uptime function."""

    def test_parse_uptime_success(self):
        """Test parsing uptime successfully."""
        status_text = "Active: active (running) since Mon 2024-03-18 10:00:00 UTC; 4 days ago"
        result = parse_uptime(status_text)
        assert result == "4 days"

    def test_parse_uptime_not_found(self):
        """Test parsing uptime when not found."""
        status_text = "Active: inactive (dead)"
        result = parse_uptime(status_text)
        assert result is None

    def test_parse_uptime_empty(self):
        """Test parsing uptime from empty text."""
        result = parse_uptime("")
        assert result is None


class TestParseMemory:
    """Tests for parse_memory function."""

    def test_parse_memory_success(self):
        """Test parsing memory successfully."""
        status_text = "Memory: 123.4M\n"
        result = parse_memory(status_text)
        assert result == "123.4M"

    def test_parse_memory_with_spaces(self):
        """Test parsing memory with spaces."""
        status_text = "Memory: 123.4 MB\n"
        result = parse_memory(status_text)
        assert result == "123.4 MB"

    def test_parse_memory_not_found(self):
        """Test parsing memory when not found."""
        status_text = "No memory info"
        result = parse_memory(status_text)
        assert result is None

    def test_parse_memory_empty(self):
        """Test parsing memory from empty text."""
        result = parse_memory("")
        assert result is None


class TestParseCpu:
    """Tests for parse_cpu function."""

    def test_parse_cpu_success(self):
        """Test parsing CPU successfully."""
        status_text = "CPU: 123ms\n"
        result = parse_cpu(status_text)
        assert result == "123ms"

    def test_parse_cpu_with_spaces(self):
        """Test parsing CPU with spaces."""
        status_text = "CPU: 1.23s\n"
        result = parse_cpu(status_text)
        assert result == "1.23s"

    def test_parse_cpu_not_found(self):
        """Test parsing CPU when not found."""
        status_text = "No CPU info"
        result = parse_cpu(status_text)
        assert result is None

    def test_parse_cpu_empty(self):
        """Test parsing CPU from empty text."""
        result = parse_cpu("")
        assert result is None


class TestParseLastError:
    """Tests for parse_last_error function."""

    def test_parse_last_error_success(self):
        """Test parsing last error successfully."""
        status_text = "Error: Service failed to start\n"
        result = parse_last_error(status_text)
        assert result == "Service failed to start"

    def test_parse_last_error_not_found(self):
        """Test parsing last error when not found."""
        status_text = "No errors"
        result = parse_last_error(status_text)
        assert result is None

    def test_parse_last_error_empty(self):
        """Test parsing last error from empty text."""
        result = parse_last_error("")
        assert result is None


class TestGetServiceInfo:
    """Tests for get_service_info function."""

    @patch("services.subprocess.run")
    def test_get_service_info_success(self, mock_run):
        """Test getting service info successfully."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Service status output"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = get_service_info("projects_test.service")
        assert result == "Service status output"
        mock_run.assert_called_once_with(
            ["systemctl", "status", "projects_test.service", "--no-pager", "--lines=200"],
            text=True,
            capture_output=True,
        )

    @patch("services.subprocess.run")
    def test_get_service_info_with_error(self, mock_run):
        """Test getting service info when command fails."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = "Some output"
        mock_result.stderr = "Error message"
        mock_run.return_value = mock_result

        result = get_service_info("projects_test.service")
        assert result == "Some output\nError message"


class TestGetServiceStatus:
    """Tests for get_service_status function."""

    @patch("services.get_service_info")
    def test_get_service_status_active(self, mock_get_info):
        """Test getting status for active service."""
        mock_get_info.return_value = (
            "Active: active (running) since Mon 2024-03-18 10:00:00 UTC; 4 days ago\n"
            "Memory: 123.4M\n"
            "CPU: 123ms\n"
        )
        result = get_service_status("projects_test.service")

        assert isinstance(result, ServiceStatus)
        assert result.name == "projects_test.service"
        assert result.is_active is True
        assert result.is_failed is False
        assert result.uptime == "4 days"
        assert result.memory == "123.4M"
        assert result.cpu == "123ms"
        assert result.last_error is None

    @patch("services.get_service_info")
    def test_get_service_status_failed(self, mock_get_info):
        """Test getting status for failed service."""
        mock_get_info.return_value = (
            "Active: failed (result: exit-code) since Mon 2024-03-18 10:00:00 UTC\n"
            "Error: Service failed to start\n"
        )
        result = get_service_status("projects_test.service")

        assert isinstance(result, ServiceStatus)
        assert result.name == "projects_test.service"
        assert result.is_active is False
        assert result.is_failed is True
        assert result.uptime is None
        assert result.last_error == "Service failed to start"

    @patch("services.get_service_info")
    def test_get_service_status_inactive(self, mock_get_info):
        """Test getting status for inactive service."""
        mock_get_info.return_value = "Active: inactive (dead)\n"
        result = get_service_status("projects_test.service")

        assert isinstance(result, ServiceStatus)
        assert result.name == "projects_test.service"
        assert result.is_active is False
        assert result.is_failed is False
        assert result.uptime is None

    @patch("services.get_service_info")
    def test_get_service_status_active_no_memory_cpu(self, mock_get_info):
        """Test getting status for active service without memory/cpu info."""
        mock_get_info.return_value = (
            "Active: active (running) since Mon 2024-03-18 10:00:00 UTC; 2 hours ago\n"
        )
        result = get_service_status("projects_test.service")

        assert isinstance(result, ServiceStatus)
        assert result.name == "projects_test.service"
        assert result.is_active is True
        assert result.is_failed is False
        assert result.uptime == "2 hours"
        assert result.memory is None
        assert result.cpu is None
        assert result.last_error is None

    @patch("services.get_service_info")
    def test_get_service_status_full_status_preserved(self, mock_get_info):
        """Test that full_status is preserved in ServiceStatus."""
        status_text = "Active: active (running) since Mon 2024-03-18 10:00:00 UTC; 1 day ago\nMemory: 50M\n"
        mock_get_info.return_value = status_text
        result = get_service_status("projects_test.service")

        assert isinstance(result, ServiceStatus)
        assert result.full_status == status_text
