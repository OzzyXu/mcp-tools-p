"""Test GPU Monitor data models."""

import pytest
from datetime import datetime
from pydantic import ValidationError

from gpu_monitor.models import (
    ServerConfig, ClusterConfig, GPUInfo, ProcessInfo, 
    ServerStatus, UserUsageSummary, ClusterStatus
)


class TestServerConfig:
    """Test ServerConfig model."""
    
    def test_valid_server_config(self):
        """Test creating a valid server config."""
        config = ServerConfig(
            id="gpu01",
            hostname="gpu01.example.com",
            description="Test server"
        )
        assert config.id == "gpu01"
        assert config.hostname == "gpu01.example.com"
        assert config.description == "Test server"
    
    def test_server_config_minimal(self):
        """Test server config with minimal required fields."""
        config = ServerConfig(id="gpu01", hostname="gpu01.example.com")
        assert config.description == ""


class TestClusterConfig:
    """Test ClusterConfig model."""
    
    def test_valid_cluster_config(self, sample_config):
        """Test creating a valid cluster config."""
        assert len(sample_config.servers) == 2
        assert sample_config.settings["cache_ttl"] == 5
    
    def test_default_settings(self):
        """Test cluster config with default settings."""
        config = ClusterConfig(servers=[
            ServerConfig(id="gpu01", hostname="test.com")
        ])
        assert "cache_ttl" in config.settings
        assert config.settings["cache_ttl"] == 30


class TestGPUInfo:
    """Test GPUInfo model."""
    
    def test_valid_gpu_info(self):
        """Test creating valid GPU info."""
        gpu = GPUInfo(
            index=0,
            name="Tesla V100",
            utilization_percent=85,
            memory_used_mb=15000,
            memory_total_mb=16000,
            memory_free_mb=1000
        )
        assert gpu.index == 0
        assert gpu.utilization_percent == 85
        assert gpu.memory_free_mb == 1000
    
    def test_gpu_info_optional_fields(self):
        """Test GPU info with optional fields."""
        gpu = GPUInfo(
            index=0,
            name="Tesla V100",
            utilization_percent=85,
            memory_used_mb=15000,
            memory_total_mb=16000,
            memory_free_mb=1000,
            temperature_c=75,
            power_draw_w=250
        )
        assert gpu.temperature_c == 75
        assert gpu.power_draw_w == 250


class TestProcessInfo:
    """Test ProcessInfo model."""
    
    def test_valid_process_info(self):
        """Test creating valid process info."""
        process = ProcessInfo(
            pid=12345,
            username="testuser",
            gpu_index=0,
            memory_used_mb=2048,
            process_name="python train.py"
        )
        assert process.pid == 12345
        assert process.username == "testuser"
        assert process.gpu_index == 0


class TestServerStatus:
    """Test ServerStatus model."""
    
    def test_online_server_status(self):
        """Test creating status for online server."""
        gpu = GPUInfo(
            index=0, name="Tesla V100", utilization_percent=50,
            memory_used_mb=8000, memory_total_mb=16000, memory_free_mb=8000
        )
        status = ServerStatus(
            server_id="gpu01",
            hostname="gpu01.example.com",
            online=True,
            gpus=[gpu],
            processes=[],
            last_updated=datetime.now(),
            response_time_ms=150.5
        )
        assert status.online is True
        assert len(status.gpus) == 1
        assert status.response_time_ms == 150.5
    
    def test_offline_server_status(self):
        """Test creating status for offline server."""
        status = ServerStatus(
            server_id="gpu01",
            hostname="gpu01.example.com",
            online=False,
            error_message="Connection refused",
            last_updated=datetime.now()
        )
        assert status.online is False
        assert status.error_message == "Connection refused"
        assert len(status.gpus) == 0


class TestUserUsageSummary:
    """Test UserUsageSummary model."""
    
    def test_user_usage_summary(self):
        """Test creating user usage summary."""
        process = ProcessInfo(
            pid=12345, username="testuser", gpu_index=0,
            memory_used_mb=2048, process_name="python"
        )
        summary = UserUsageSummary(
            username="testuser",
            total_processes=1,
            total_memory_used_mb=2048,
            servers_used=["gpu01"],
            processes_by_server={"gpu01": [process]},
            last_updated=datetime.now()
        )
        assert summary.username == "testuser"
        assert summary.total_processes == 1
        assert len(summary.servers_used) == 1


class TestClusterStatus:
    """Test ClusterStatus model."""
    
    def test_cluster_status(self):
        """Test creating cluster status."""
        server_status = ServerStatus(
            server_id="gpu01", hostname="gpu01.example.com",
            online=True, last_updated=datetime.now()
        )
        cluster = ClusterStatus(
            servers=[server_status],
            total_gpus=0,
            online_servers=1,
            total_servers=1,
            last_updated=datetime.now()
        )
        assert cluster.online_servers == 1
        assert cluster.total_servers == 1
        assert len(cluster.servers) == 1
