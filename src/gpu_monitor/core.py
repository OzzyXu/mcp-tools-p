"""Core GPU monitoring functionality."""

import asyncio
import json
import re
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union
import logging

from .models import (
    ClusterConfig, ServerConfig, ServerStatus, GPUInfo, 
    ProcessInfo, UserUsageSummary, ClusterStatus
)

logger = logging.getLogger(__name__)


class GPUMonitor:
    """Core GPU monitoring class with caching and concurrent SSH support."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the GPU monitor with configuration."""
        self.config = self._load_config(config_path)
        self._cache: Dict[str, tuple] = {}  # (data, timestamp)
        self._semaphore = asyncio.Semaphore(self.config.settings.get("max_concurrent", 4))
    
    def _load_config(self, config_path: Optional[str] = None) -> ClusterConfig:
        """Load configuration from JSON file."""
        if config_path is None:
            config_path = Path(__file__).parent / "servers.json"
        
        try:
            with open(config_path, 'r') as f:
                data = json.load(f)
            return ClusterConfig(**data)
        except FileNotFoundError:
            # Create default config if none exists
            default_config = ClusterConfig(
                servers=[
                    ServerConfig(
                        id="gpu01",
                        hostname="gpu01.cluster.local",
                        description="Primary training server"
                    )
                ]
            )
            logger.warning(f"Config file not found at {config_path}, using default config")
            return default_config
    
    def _is_cache_valid(self, key: str, ttl: int) -> bool:
        """Check if cached data is still valid."""
        if key not in self._cache:
            return False
        _, timestamp = self._cache[key]
        return time.time() - timestamp < ttl
    
    def _get_cached(self, key: str) -> Optional[any]:
        """Get cached data if valid."""
        if key in self._cache:
            data, _ = self._cache[key]
            return data
        return None
    
    def _set_cache(self, key: str, data: any):
        """Set cached data with timestamp."""
        self._cache[key] = (data, time.time())
    
    async def _run_ssh_command(self, hostname: str, command: str) -> tuple[bool, str, float]:
        """Run SSH command with timeout and measure response time."""
        start_time = time.time()
        timeout = self.config.settings.get("ssh_timeout", 5)
        
        try:
            # Use subprocess for SSH (company handles authentication)
            process = await asyncio.create_subprocess_exec(
                "ssh", hostname, command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), 
                timeout=timeout
            )
            
            response_time = (time.time() - start_time) * 1000
            
            if process.returncode == 0:
                return True, stdout.decode().strip(), response_time
            else:
                return False, stderr.decode().strip(), response_time
                
        except asyncio.TimeoutError:
            return False, f"SSH timeout after {timeout}s", (time.time() - start_time) * 1000
        except Exception as e:
            return False, str(e), (time.time() - start_time) * 1000
    
    def _parse_nvidia_smi_output(self, output: str) -> tuple[List[GPUInfo], List[ProcessInfo]]:
        """Parse nvidia-smi output to extract GPU and process information."""
        gpus = []
        processes = []
        
        try:
            # Parse GPU information from nvidia-smi --query-gpu output
            gpu_lines = []
            process_lines = []
            current_section = None
            
            for line in output.split('\n'):
                line = line.strip()
                if not line:
                    continue
                
                # Simple parsing - in real implementation, use nvidia-smi with specific formats
                if 'GPU' in line and '%' in line:
                    # Example: GPU 0: Tesla V100, 85% utilization, 15000/16000 MB
                    match = re.search(r'GPU (\d+).*?(\d+)%.*?(\d+)/(\d+)\s*MB', line)
                    if match:
                        gpu_idx, util, used_mem, total_mem = match.groups()
                        gpu = GPUInfo(
                            index=int(gpu_idx),
                            name="Tesla V100",  # Simplified
                            utilization_percent=int(util),
                            memory_used_mb=int(used_mem),
                            memory_total_mb=int(total_mem),
                            memory_free_mb=int(total_mem) - int(used_mem)
                        )
                        gpus.append(gpu)
                
                # Parse process information
                if 'PID' in line and 'Memory' in line:
                    # Example: PID 12345 user1 GPU:0 2048MB python
                    match = re.search(r'PID\s+(\d+)\s+(\w+)\s+GPU:(\d+)\s+(\d+)MB\s+(.+)', line)
                    if match:
                        pid, user, gpu_idx, mem, proc_name = match.groups()
                        process = ProcessInfo(
                            pid=int(pid),
                            username=user,
                            gpu_index=int(gpu_idx),
                            memory_used_mb=int(mem),
                            process_name=proc_name.strip()
                        )
                        processes.append(process)
        
        except Exception as e:
            logger.error(f"Error parsing nvidia-smi output: {e}")
        
        return gpus, processes
    
    async def _get_server_status(self, server: ServerConfig) -> ServerStatus:
        """Get status for a single server."""
        async with self._semaphore:
            start_time = time.time()
            
            # Check cache first
            cache_key = f"server_status_{server.id}"
            ttl = self.config.settings.get("cache_ttl", 30)
            
            if self._is_cache_valid(cache_key, ttl):
                cached_data = self._get_cached(cache_key)
                if cached_data:
                    return cached_data
            
            # Run nvidia-smi command
            success, output, response_time = await self._run_ssh_command(
                server.hostname,
                "nvidia-smi --query-gpu=index,name,utilization.gpu,memory.used,memory.total,temperature.gpu,power.draw --format=csv,noheader,nounits && echo '---PROCESSES---' && nvidia-smi pmon -c 1"
            )
            
            if success:
                gpus, processes = self._parse_nvidia_smi_output(output)
                status = ServerStatus(
                    server_id=server.id,
                    hostname=server.hostname,
                    online=True,
                    gpus=gpus,
                    processes=processes,
                    last_updated=datetime.now(),
                    response_time_ms=response_time
                )
            else:
                status = ServerStatus(
                    server_id=server.id,
                    hostname=server.hostname,
                    online=False,
                    error_message=output,
                    last_updated=datetime.now(),
                    response_time_ms=response_time
                )
            
            # Cache the result
            self._set_cache(cache_key, status)
            return status
    
    async def get_cluster_status(self, server_ids: Optional[List[str]] = None) -> ClusterStatus:
        """Get status for all servers or specific servers."""
        servers_to_check = self.config.servers
        if server_ids:
            servers_to_check = [s for s in servers_to_check if s.id in server_ids]
        
        # Get status for all servers concurrently
        tasks = [self._get_server_status(server) for server in servers_to_check]
        server_statuses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and create valid statuses
        valid_statuses = []
        for i, status in enumerate(server_statuses):
            if isinstance(status, Exception):
                logger.error(f"Error getting status for {servers_to_check[i].id}: {status}")
                # Create error status
                error_status = ServerStatus(
                    server_id=servers_to_check[i].id,
                    hostname=servers_to_check[i].hostname,
                    online=False,
                    error_message=str(status),
                    last_updated=datetime.now()
                )
                valid_statuses.append(error_status)
            else:
                valid_statuses.append(status)
        
        # Calculate cluster summary
        total_gpus = sum(len(s.gpus) for s in valid_statuses if s.online)
        online_servers = sum(1 for s in valid_statuses if s.online)
        
        return ClusterStatus(
            servers=valid_statuses,
            total_gpus=total_gpus,
            online_servers=online_servers,
            total_servers=len(valid_statuses),
            last_updated=datetime.now()
        )
    
    async def get_user_usage(self, username: str, server_ids: Optional[List[str]] = None) -> UserUsageSummary:
        """Get GPU usage summary for a specific user."""
        cluster_status = await self.get_cluster_status(server_ids)
        
        user_processes = []
        processes_by_server = {}
        servers_used = []
        
        for server_status in cluster_status.servers:
            if not server_status.online:
                continue
                
            server_processes = [
                p for p in server_status.processes 
                if p.username == username
            ]
            
            if server_processes:
                servers_used.append(server_status.server_id)
                processes_by_server[server_status.server_id] = server_processes
                user_processes.extend(server_processes)
        
        total_memory = sum(p.memory_used_mb for p in user_processes)
        
        return UserUsageSummary(
            username=username,
            total_processes=len(user_processes),
            total_memory_used_mb=total_memory,
            servers_used=servers_used,
            processes_by_server=processes_by_server,
            last_updated=datetime.now()
        )
    
    async def kill_user_tasks(
        self, 
        username: str, 
        server_ids: Optional[List[str]] = None,
        confirm: bool = False
    ) -> Dict[str, Union[bool, str]]:
        """Kill all tasks for a user on specified servers."""
        if not confirm:
            return {"error": "Must set confirm=True to kill user tasks"}
        
        # Get current user processes
        usage = await self.get_user_usage(username, server_ids)
        
        if not usage.processes_by_server:
            return {"message": f"No processes found for user {username}"}
        
        results = {}
        
        for server_id, processes in usage.processes_by_server.items():
            server = next((s for s in self.config.servers if s.id == server_id), None)
            if not server:
                results[server_id] = f"Server config not found"
                continue
            
            pids = [str(p.pid) for p in processes]
            kill_command = f"kill -9 {' '.join(pids)}"
            
            success, output, _ = await self._run_ssh_command(server.hostname, kill_command)
            
            if success:
                results[server_id] = f"Killed {len(pids)} processes"
                # Invalidate cache for this server
                cache_key = f"server_status_{server_id}"
                if cache_key in self._cache:
                    del self._cache[cache_key]
            else:
                results[server_id] = f"Failed to kill processes: {output}"
        
        return results


# Convenience functions for CLI usage
async def check_gpu_status(server_id: str = "all", config_path: Optional[str] = None) -> ClusterStatus:
    """Check GPU status for all or specific server."""
    monitor = GPUMonitor(config_path)
    server_ids = None if server_id == "all" else [server_id]
    return await monitor.get_cluster_status(server_ids)


async def check_user_usage(username: str, server_id: str = "all", config_path: Optional[str] = None) -> UserUsageSummary:
    """Check user's GPU usage."""
    monitor = GPUMonitor(config_path)
    server_ids = None if server_id == "all" else [server_id]
    return await monitor.get_user_usage(username, server_ids)


async def kill_user_tasks(username: str, server_id: str = "all", confirm: bool = False, config_path: Optional[str] = None) -> Dict[str, Union[bool, str]]:
    """Kill user's tasks."""
    monitor = GPUMonitor(config_path)
    server_ids = None if server_id == "all" else [server_id]
    return await monitor.kill_user_tasks(username, server_ids, confirm)
