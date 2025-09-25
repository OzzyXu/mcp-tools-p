"""Data models for GPU cluster monitoring."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime


class ServerConfig(BaseModel):
    """Configuration for a GPU server."""
    id: str
    hostname: str
    description: str = ""


class ClusterConfig(BaseModel):
    """Configuration for the entire cluster."""
    servers: List[ServerConfig]
    settings: Dict[str, Any] = {
        "cache_ttl": 30,
        "ssh_timeout": 5,
        "max_concurrent": 4
    }


class GPUInfo(BaseModel):
    """Information about a single GPU."""
    index: int
    name: str
    utilization_percent: int
    memory_used_mb: int
    memory_total_mb: int
    memory_free_mb: int
    temperature_c: Optional[int] = None
    power_draw_w: Optional[int] = None


class ProcessInfo(BaseModel):
    """Information about a GPU process."""
    pid: int
    username: str
    gpu_index: int
    memory_used_mb: int
    process_name: str


class ServerStatus(BaseModel):
    """Status of a single server."""
    server_id: str
    hostname: str
    online: bool
    error_message: Optional[str] = None
    gpus: List[GPUInfo] = []
    processes: List[ProcessInfo] = []
    last_updated: datetime
    response_time_ms: Optional[float] = None


class UserUsageSummary(BaseModel):
    """Summary of user's GPU usage across servers."""
    username: str
    total_processes: int
    total_memory_used_mb: int
    servers_used: List[str]
    processes_by_server: Dict[str, List[ProcessInfo]]
    last_updated: datetime


class ClusterStatus(BaseModel):
    """Status of the entire cluster."""
    servers: List[ServerStatus]
    total_gpus: int
    online_servers: int
    total_servers: int
    last_updated: datetime
