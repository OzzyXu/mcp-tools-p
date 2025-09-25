"""Test GPU Monitor CLI functionality."""

import pytest
import json
from unittest.mock import patch, AsyncMock, MagicMock
from click.testing import CliRunner
from datetime import datetime

from gpu_monitor.cli import cli
from gpu_monitor.models import ClusterStatus, ServerStatus, UserUsageSummary


class TestCLI:
    """Test CLI interface."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
    
    def test_cli_config_command(self, config_file):
        """Test config command."""
        with patch('gpu_monitor.cli.GPUMonitor') as mock_monitor_class:
            mock_monitor = MagicMock()
            mock_monitor.config.servers = [
                MagicMock(id="gpu01", hostname="test.com", description="Test server")
            ]
            mock_monitor.config.settings = {"cache_ttl": 30}
            mock_monitor_class.return_value = mock_monitor
            
            result = self.runner.invoke(cli, ['--config', config_file, 'config'])
            
            assert result.exit_code == 0
            assert "Current Configuration" in result.output
            assert "gpu01" in result.output
    
    def test_cli_config_error(self):
        """Test config command with error."""
        with patch('gpu_monitor.cli.GPUMonitor') as mock_monitor_class:
            mock_monitor_class.side_effect = Exception("Config error")
            
            result = self.runner.invoke(cli, ['config'])
            
            assert result.exit_code == 0
            assert "Error loading configuration" in result.output
    
    @patch('gpu_monitor.cli.asyncio.run')
    def test_cli_status_command(self, mock_asyncio_run):
        """Test status command."""
        # Mock the async function result
        mock_cluster_status = ClusterStatus(
            servers=[
                ServerStatus(
                    server_id="gpu01",
                    hostname="test.com",
                    online=True,
                    gpus=[],
                    processes=[],
                    last_updated=datetime.now(),
                    response_time_ms=100.0
                )
            ],
            total_gpus=0,
            online_servers=1,
            total_servers=1,
            last_updated=datetime.now()
        )
        
        async def mock_status_func():
            return mock_cluster_status
            
        mock_asyncio_run.side_effect = lambda func: mock_status_func()
        
        result = self.runner.invoke(cli, ['status'])
        
        assert result.exit_code == 0
        mock_asyncio_run.assert_called_once()
    
    @patch('gpu_monitor.cli.asyncio.run')
    def test_cli_status_json_output(self, mock_asyncio_run):
        """Test status command with JSON output."""
        mock_cluster_status = ClusterStatus(
            servers=[],
            total_gpus=0,
            online_servers=0,
            total_servers=0,
            last_updated=datetime.now()
        )
        
        async def mock_status_func():
            return mock_cluster_status
            
        mock_asyncio_run.side_effect = lambda func: mock_status_func()
        
        result = self.runner.invoke(cli, ['status', '--json'])
        
        assert result.exit_code == 0
        # Should be valid JSON
        try:
            json.loads(result.output.strip())
        except json.JSONDecodeError:
            pytest.fail("Output is not valid JSON")
    
    @patch('gpu_monitor.cli.asyncio.run')
    def test_cli_status_specific_server(self, mock_asyncio_run):
        """Test status command for specific server."""
        mock_cluster_status = ClusterStatus(
            servers=[],
            total_gpus=0,
            online_servers=0,
            total_servers=0,
            last_updated=datetime.now()
        )
        
        async def mock_status_func():
            return mock_cluster_status
            
        mock_asyncio_run.side_effect = lambda func: mock_status_func()
        
        result = self.runner.invoke(cli, ['status', '--server', 'gpu01'])
        
        assert result.exit_code == 0
        mock_asyncio_run.assert_called_once()
    
    @patch('gpu_monitor.cli.asyncio.run')
    @patch('gpu_monitor.cli.get_current_user')
    def test_cli_usage_command(self, mock_get_user, mock_asyncio_run):
        """Test usage command."""
        mock_get_user.return_value = "testuser"
        
        mock_usage = UserUsageSummary(
            username="testuser",
            total_processes=1,
            total_memory_used_mb=2048,
            servers_used=["gpu01"],
            processes_by_server={},
            last_updated=datetime.now()
        )
        
        async def mock_usage_func():
            return mock_usage
            
        mock_asyncio_run.side_effect = lambda func: mock_usage_func()
        
        result = self.runner.invoke(cli, ['usage'])
        
        assert result.exit_code == 0
        assert "testuser" in result.output
        mock_asyncio_run.assert_called_once()
    
    @patch('gpu_monitor.cli.asyncio.run')
    def test_cli_usage_specific_user(self, mock_asyncio_run):
        """Test usage command for specific user."""
        mock_usage = UserUsageSummary(
            username="otheruser",
            total_processes=0,
            total_memory_used_mb=0,
            servers_used=[],
            processes_by_server={},
            last_updated=datetime.now()
        )
        
        async def mock_usage_func():
            return mock_usage
            
        mock_asyncio_run.side_effect = lambda func: mock_usage_func()
        
        result = self.runner.invoke(cli, ['usage', '--user', 'otheruser'])
        
        assert result.exit_code == 0
        mock_asyncio_run.assert_called_once()
    
    @patch('gpu_monitor.cli.asyncio.run')
    @patch('gpu_monitor.cli.get_current_user')
    def test_cli_kill_dry_run(self, mock_get_user, mock_asyncio_run):
        """Test kill command with dry run."""
        mock_get_user.return_value = "testuser"
        
        mock_usage = UserUsageSummary(
            username="testuser",
            total_processes=1,
            total_memory_used_mb=2048,
            servers_used=["gpu01"],
            processes_by_server={
                "gpu01": [
                    MagicMock(pid=12345, gpu_index=0, process_name="python train.py")
                ]
            },
            last_updated=datetime.now()
        )
        
        # Mock sequence: get usage, then dry run
        call_count = 0
        async def mock_kill_func():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return mock_usage
            return {"gpu01": "Would kill 1 processes"}
            
        mock_asyncio_run.side_effect = lambda func: mock_kill_func()
        
        result = self.runner.invoke(cli, ['kill', '--dry-run'])
        
        assert result.exit_code == 0
        assert "Dry run" in result.output
        assert "no processes were actually killed" in result.output
    
    @patch('gpu_monitor.cli.asyncio.run')
    @patch('gpu_monitor.cli.get_current_user')
    def test_cli_kill_no_processes(self, mock_get_user, mock_asyncio_run):
        """Test kill command when no processes exist."""
        mock_get_user.return_value = "testuser"
        
        mock_usage = UserUsageSummary(
            username="testuser",
            total_processes=0,
            total_memory_used_mb=0,
            servers_used=[],
            processes_by_server={},
            last_updated=datetime.now()
        )
        
        async def mock_kill_func():
            return mock_usage
            
        mock_asyncio_run.side_effect = lambda func: mock_kill_func()
        
        result = self.runner.invoke(cli, ['kill'])
        
        assert result.exit_code == 0
        assert "No active GPU processes found" in result.output
    
    @patch('gpu_monitor.cli.asyncio.run')
    @patch('gpu_monitor.cli.get_current_user')
    def test_cli_kill_with_confirm(self, mock_get_user, mock_asyncio_run):
        """Test kill command with confirmation."""
        mock_get_user.return_value = "testuser"
        
        mock_usage = UserUsageSummary(
            username="testuser",
            total_processes=1,
            total_memory_used_mb=2048,
            servers_used=["gpu01"],
            processes_by_server={
                "gpu01": [
                    MagicMock(pid=12345, gpu_index=0, process_name="python train.py")
                ]
            },
            last_updated=datetime.now()
        )
        
        # Mock sequence: get usage, then kill result
        call_count = 0
        async def mock_kill_func():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return mock_usage
            return {"gpu01": "Killed 1 processes"}
            
        mock_asyncio_run.side_effect = lambda func: mock_kill_func()
        
        result = self.runner.invoke(cli, ['kill', '--confirm'])
        
        assert result.exit_code == 0
        assert "Killing processes" in result.output
    
    def test_cli_install_command(self):
        """Test install command."""
        result = self.runner.invoke(cli, ['install'])
        
        assert result.exit_code == 0
        assert "install this script for failure-safe access" in result.output
        assert "/shared/tools" in result.output


class TestCLIHelpers:
    """Test CLI helper functions."""
    
    def test_get_current_user(self):
        """Test getting current user."""
        with patch('os.environ.get') as mock_env:
            mock_env.return_value = "testuser"
            
            from gpu_monitor.cli import get_current_user
            user = get_current_user()
            
            assert user == "testuser"
            mock_env.assert_called_once_with('USER', 'unknown')
    
    def test_format_gpu_status(self):
        """Test formatting GPU status for display."""
        from gpu_monitor.cli import format_gpu_status
        from gpu_monitor.models import GPUInfo
        
        gpu = GPUInfo(
            index=0, name="Tesla V100", utilization_percent=85,
            memory_used_mb=15000, memory_total_mb=16000, memory_free_mb=1000
        )
        
        server_status = ServerStatus(
            server_id="gpu01", hostname="test.com", online=True,
            gpus=[gpu], processes=[], last_updated=datetime.now(),
            response_time_ms=100.0
        )
        
        cluster_status = ClusterStatus(
            servers=[server_status], total_gpus=1, online_servers=1,
            total_servers=1, last_updated=datetime.now()
        )
        
        formatted = format_gpu_status(cluster_status)
        
        assert "GPU Cluster Status" in formatted
        assert "gpu01" in formatted
        assert "85%" in formatted
        assert "🔴" in formatted  # High utilization emoji
    
    def test_format_user_usage(self):
        """Test formatting user usage for display."""
        from gpu_monitor.cli import format_user_usage
        from gpu_monitor.models import ProcessInfo
        
        process = ProcessInfo(
            pid=12345, username="testuser", gpu_index=0,
            memory_used_mb=2048, process_name="python train.py"
        )
        
        usage = UserUsageSummary(
            username="testuser", total_processes=1, total_memory_used_mb=2048,
            servers_used=["gpu01"], processes_by_server={"gpu01": [process]},
            last_updated=datetime.now()
        )
        
        formatted = format_user_usage(usage)
        
        assert "testuser" in formatted
        assert "12345" in formatted
        assert "python train.py" in formatted
        assert "gpu01" in formatted
