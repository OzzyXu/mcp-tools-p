"""Test configuration and fixtures."""

import pytest
from pathlib import Path
import tempfile
import json

from gpu_monitor.models import ClusterConfig, ServerConfig


@pytest.fixture
def sample_config():
    """Sample configuration for testing."""
    return ClusterConfig(
        servers=[
            ServerConfig(
                id="test-gpu01",
                hostname="test1.example.com",
                description="Test GPU server 1"
            ),
            ServerConfig(
                id="test-gpu02", 
                hostname="test2.example.com",
                description="Test GPU server 2"
            )
        ],
        settings={
            "cache_ttl": 5,
            "ssh_timeout": 2,
            "max_concurrent": 2
        }
    )


@pytest.fixture
def config_file(sample_config):
    """Temporary config file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write(sample_config.model_dump_json(indent=2))
        return f.name


@pytest.fixture
def mock_nvidia_smi_output():
    """Mock nvidia-smi output for testing."""
    return """
GPU 0: Tesla V100, 85% utilization, 15000/16000 MB
GPU 1: Tesla V100, 45% utilization, 8000/16000 MB
---PROCESSES---
PID 12345 testuser GPU:0 2048MB python train.py
PID 67890 testuser GPU:1 4096MB python inference.py
PID 11111 otheruser GPU:0 1024MB jupyter
"""


@pytest.fixture
def mock_failed_ssh_output():
    """Mock failed SSH output for testing."""
    return "ssh: connect to host test1.example.com port 22: Connection refused"
