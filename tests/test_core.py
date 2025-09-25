"""Test GPU Monitor core functionality."""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from gpu_monitor.core import GPUMonitor
from gpu_monitor.models import ServerStatus, GPUInfo, ProcessInfo


class TestGPUMonitor:
    """Test GPUMonitor class."""
    
    def test_init_with_config_file(self, config_file):
        """Test initializing monitor with config file."""
        monitor = GPUMonitor(config_file)
        assert len(monitor.config.servers) == 2
        assert monitor.config.servers[0].id == "test-gpu01"
    
    def test_init_default_config(self):
        """Test initializing monitor with default config."""
        with patch('gpu_monitor.core.Path.open', side_effect=FileNotFoundError):
            monitor = GPUMonitor()
            assert len(monitor.config.servers) >= 1  # Default config
    
    def test_cache_validation(self, sample_config):
        """Test cache validation logic."""
        monitor = GPUMonitor()
        monitor.config = sample_config
        
        # Test cache miss
        assert not monitor._is_cache_valid("test_key", 30)
        
        # Set cache and test hit
        monitor._set_cache("test_key", "test_data")
        assert monitor._is_cache_valid("test_key", 30)
        
        # Test cache expiry
        assert not monitor._is_cache_valid("test_key", 0)
    
    def test_parse_nvidia_smi_output(self, sample_config, mock_nvidia_smi_output):
        """Test parsing nvidia-smi output."""
        monitor = GPUMonitor()
        monitor.config = sample_config
        
        gpus, processes = monitor._parse_nvidia_smi_output(mock_nvidia_smi_output)
        
        # Check GPU parsing
        assert len(gpus) == 2
        assert gpus[0].index == 0
        assert gpus[0].utilization_percent == 85
        assert gpus[1].utilization_percent == 45
        
        # Check process parsing
        assert len(processes) == 3
        assert processes[0].username == "testuser"
        assert processes[0].pid == 12345
        assert processes[2].username == "otheruser"
    
    @pytest.mark.asyncio
    async def test_run_ssh_command_success(self, sample_config):
        """Test successful SSH command execution."""
        monitor = GPUMonitor()
        monitor.config = sample_config
        
        with patch('asyncio.create_subprocess_exec') as mock_subprocess:
            # Mock successful subprocess
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate.return_value = (b"success output", b"")
            mock_subprocess.return_value = mock_process
            
            success, output, response_time = await monitor._run_ssh_command(
                "test.com", "echo hello"
            )
            
            assert success is True
            assert output == "success output"
            assert response_time > 0
    
    @pytest.mark.asyncio
    async def test_run_ssh_command_failure(self, sample_config):
        """Test failed SSH command execution."""
        monitor = GPUMonitor()
        monitor.config = sample_config
        
        with patch('asyncio.create_subprocess_exec') as mock_subprocess:
            # Mock failed subprocess
            mock_process = AsyncMock()
            mock_process.returncode = 1
            mock_process.communicate.return_value = (b"", b"connection refused")
            mock_subprocess.return_value = mock_process
            
            success, output, response_time = await monitor._run_ssh_command(
                "test.com", "echo hello"
            )
            
            assert success is False
            assert "connection refused" in output
            assert response_time > 0
    
    @pytest.mark.asyncio
    async def test_run_ssh_command_timeout(self, sample_config):
        """Test SSH command timeout."""
        monitor = GPUMonitor()
        monitor.config = sample_config
        
        with patch('asyncio.create_subprocess_exec') as mock_subprocess:
            # Mock timeout
            mock_process = AsyncMock()
            mock_process.communicate.side_effect = asyncio.TimeoutError()
            mock_subprocess.return_value = mock_process
            
            success, output, response_time = await monitor._run_ssh_command(
                "test.com", "echo hello"
            )
            
            assert success is False
            assert "timeout" in output.lower()
            assert response_time > 0
    
    @pytest.mark.asyncio
    async def test_get_server_status_online(self, sample_config, mock_nvidia_smi_output):
        """Test getting status for online server."""
        monitor = GPUMonitor()
        monitor.config = sample_config
        
        with patch.object(monitor, '_run_ssh_command') as mock_ssh:
            mock_ssh.return_value = (True, mock_nvidia_smi_output, 100.0)
            
            status = await monitor._get_server_status(sample_config.servers[0])
            
            assert status.online is True
            assert status.server_id == "test-gpu01"
            assert len(status.gpus) == 2
            assert len(status.processes) == 3
            assert status.response_time_ms == 100.0
    
    @pytest.mark.asyncio
    async def test_get_server_status_offline(self, sample_config):
        """Test getting status for offline server."""
        monitor = GPUMonitor()
        monitor.config = sample_config
        
        with patch.object(monitor, '_run_ssh_command') as mock_ssh:
            mock_ssh.return_value = (False, "Connection refused", 50.0)
            
            status = await monitor._get_server_status(sample_config.servers[0])
            
            assert status.online is False
            assert status.error_message == "Connection refused"
            assert len(status.gpus) == 0
            assert status.response_time_ms == 50.0
    
    @pytest.mark.asyncio
    async def test_get_cluster_status_all_servers(self, sample_config, mock_nvidia_smi_output):
        """Test getting cluster status for all servers."""
        monitor = GPUMonitor()
        monitor.config = sample_config
        
        with patch.object(monitor, '_run_ssh_command') as mock_ssh:
            mock_ssh.return_value = (True, mock_nvidia_smi_output, 100.0)
            
            cluster_status = await monitor.get_cluster_status()
            
            assert len(cluster_status.servers) == 2
            assert cluster_status.total_servers == 2
            assert cluster_status.online_servers == 2
            assert cluster_status.total_gpus == 4  # 2 GPUs per server
    
    @pytest.mark.asyncio
    async def test_get_cluster_status_specific_server(self, sample_config, mock_nvidia_smi_output):
        """Test getting cluster status for specific server."""
        monitor = GPUMonitor()
        monitor.config = sample_config
        
        with patch.object(monitor, '_run_ssh_command') as mock_ssh:
            mock_ssh.return_value = (True, mock_nvidia_smi_output, 100.0)
            
            cluster_status = await monitor.get_cluster_status(["test-gpu01"])
            
            assert len(cluster_status.servers) == 1
            assert cluster_status.servers[0].server_id == "test-gpu01"
    
    @pytest.mark.asyncio
    async def test_get_user_usage(self, sample_config, mock_nvidia_smi_output):
        """Test getting user usage summary."""
        monitor = GPUMonitor()
        monitor.config = sample_config
        
        with patch.object(monitor, '_run_ssh_command') as mock_ssh:
            mock_ssh.return_value = (True, mock_nvidia_smi_output, 100.0)
            
            usage = await monitor.get_user_usage("testuser")
            
            assert usage.username == "testuser"
            assert usage.total_processes == 2  # testuser has 2 processes
            assert usage.total_memory_used_mb == 6144  # 2048 + 4096
            assert len(usage.servers_used) == 2
    
    @pytest.mark.asyncio
    async def test_kill_user_tasks_no_confirm(self, sample_config):
        """Test killing user tasks without confirmation."""
        monitor = GPUMonitor()
        monitor.config = sample_config
        
        result = await monitor.kill_user_tasks("testuser", confirm=False)
        
        assert "error" in result
        assert "confirm=True" in result["error"]
    
    @pytest.mark.asyncio
    async def test_kill_user_tasks_success(self, sample_config, mock_nvidia_smi_output):
        """Test successfully killing user tasks."""
        monitor = GPUMonitor()
        monitor.config = sample_config
        
        with patch.object(monitor, '_run_ssh_command') as mock_ssh:
            # First call: get processes, second call: kill command
            mock_ssh.side_effect = [
                (True, mock_nvidia_smi_output, 100.0),
                (True, mock_nvidia_smi_output, 100.0),
                (True, "", 50.0),  # kill command success
                (True, "", 50.0)   # kill command success
            ]
            
            result = await monitor.kill_user_tasks("testuser", confirm=True)
            
            assert "test-gpu01" in result
            assert "test-gpu02" in result
            # Should contain success messages
            for server_result in result.values():
                assert "Killed" in str(server_result)
    
    @pytest.mark.asyncio
    async def test_kill_user_tasks_no_processes(self, sample_config):
        """Test killing user tasks when no processes exist."""
        monitor = GPUMonitor()
        monitor.config = sample_config
        
        with patch.object(monitor, '_run_ssh_command') as mock_ssh:
            # Return empty nvidia-smi output (no processes)
            mock_ssh.return_value = (True, "GPU 0: Tesla V100, 0% utilization, 0/16000 MB", 100.0)
            
            result = await monitor.kill_user_tasks("testuser", confirm=True)
            
            assert "message" in result
            assert "No processes found" in result["message"]
