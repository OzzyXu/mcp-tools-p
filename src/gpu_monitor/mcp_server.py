"""MCP server implementation for GPU cluster monitoring via HTTP."""

import asyncio
import json
import os
from typing import Optional

from fastmcp import FastMCP
from .core import GPUMonitor
from .models import ClusterStatus, UserUsageSummary

# Initialize FastMCP app for HTTP transport
app = FastMCP("GPU Monitor")

# Global monitor instance
monitor: Optional[GPUMonitor] = None


def get_monitor() -> GPUMonitor:
    """Get or create the global monitor instance."""
    global monitor
    if monitor is None:
        monitor = GPUMonitor()
    return monitor


def get_current_user() -> str:
    """Get current user from environment."""
    return os.environ.get('USER', 'unknown')


@app.resource("gpu://status")
async def gpu_status_resource():
    """Resource: Get status of all GPU servers."""
    monitor = get_monitor()
    status = await monitor.get_cluster_status()
    return {
        "uri": "gpu://status",
        "name": "GPU Cluster Status",
        "description": "Current status of all GPU servers in the cluster",
        "mimeType": "application/json",
        "text": status.model_dump_json(indent=2)
    }


@app.resource("gpu://status/{server_id}")
async def gpu_server_status_resource(server_id: str):
    """Resource: Get status of a specific GPU server."""
    monitor = get_monitor()
    status = await monitor.get_cluster_status([server_id])
    server_status = status.servers[0] if status.servers else None
    
    if not server_status:
        return {
            "uri": f"gpu://status/{server_id}",
            "name": f"GPU Server {server_id} Status",
            "description": f"Server {server_id} not found",
            "mimeType": "application/json",
            "text": json.dumps({"error": f"Server {server_id} not found"}, indent=2)
        }
    
    return {
        "uri": f"gpu://status/{server_id}",
        "name": f"GPU Server {server_id} Status", 
        "description": f"Current status of GPU server {server_id}",
        "mimeType": "application/json",
        "text": server_status.model_dump_json(indent=2)
    }


@app.resource("gpu://usage/{username}")
async def gpu_user_usage_resource(username: str):
    """Resource: Get GPU usage for a specific user across all servers."""
    monitor = get_monitor()
    usage = await monitor.get_user_usage(username)
    return {
        "uri": f"gpu://usage/{username}",
        "name": f"GPU Usage for {username}",
        "description": f"GPU usage summary for user {username} across all servers",
        "mimeType": "application/json", 
        "text": usage.model_dump_json(indent=2)
    }


@app.resource("gpu://usage/{username}/{server_id}")
async def gpu_user_server_usage_resource(username: str, server_id: str):
    """Resource: Get GPU usage for a specific user on a specific server."""
    monitor = get_monitor()
    usage = await monitor.get_user_usage(username, [server_id])
    return {
        "uri": f"gpu://usage/{username}/{server_id}",
        "name": f"GPU Usage for {username} on {server_id}",
        "description": f"GPU usage for user {username} on server {server_id}",
        "mimeType": "application/json",
        "text": usage.model_dump_json(indent=2)
    }


@app.tool("check_gpu_status")
async def check_gpu_status_tool(server_id: Optional[str] = None):
    """
    Check GPU status for all servers or a specific server.
    
    Args:
        server_id (str, optional): Server ID to check. If not provided, checks all servers.
    
    Returns:
        JSON with GPU status information including utilization, memory usage, and running processes.
    """
    monitor = get_monitor()
    server_ids = [server_id] if server_id else None
    status = await monitor.get_cluster_status(server_ids)
    return status.model_dump()


@app.tool("check_my_usage")
async def check_my_usage_tool(server_id: Optional[str] = None):
    """
    Check current user's GPU usage across servers.
    Automatically detects the current user from the $USER environment variable.
    
    Args:
        server_id (str, optional): Server ID to check. If not provided, checks all servers.
        
    Returns:
        JSON with user's GPU usage summary including processes and memory consumption.
    """
    username = get_current_user()
    monitor = get_monitor()
    server_ids = [server_id] if server_id else None
    usage = await monitor.get_user_usage(username, server_ids)
    return usage.model_dump()


@app.tool("check_user_usage")
async def check_user_usage_tool(username: str, server_id: Optional[str] = None):
    """
    Check GPU usage for a specific user across servers.
    
    Args:
        username (str): Username to check GPU usage for
        server_id (str, optional): Server ID to check. If not provided, checks all servers.
        
    Returns:
        JSON with user's GPU usage summary including processes and memory consumption.
    """
    monitor = get_monitor()
    server_ids = [server_id] if server_id else None
    usage = await monitor.get_user_usage(username, server_ids)
    return usage.model_dump()


@app.tool("kill_my_tasks")
async def kill_my_tasks_tool(server_id: Optional[str] = None, confirm: bool = False):
    """
    Kill all GPU tasks for the current user.
    Automatically detects the current user from the $USER environment variable.
    
    Args:
        server_id (str, optional): Server ID to kill tasks on. If not provided, kills on all servers.
        confirm (bool): Must be set to True to actually kill tasks (safety measure).
        
    Returns:
        JSON with results of kill operations per server.
    """
    username = get_current_user()
    monitor = get_monitor()
    server_ids = [server_id] if server_id else None
    results = await monitor.kill_user_tasks(username, server_ids, confirm)
    return results


@app.tool("kill_user_tasks")
async def kill_user_tasks_tool(username: str, server_id: Optional[str] = None, confirm: bool = False):
    """
    Kill all GPU tasks for a specific user.
    
    Args:
        username (str): Username to kill tasks for
        server_id (str, optional): Server ID to kill tasks on. If not provided, kills on all servers.
        confirm (bool): Must be set to True to actually kill tasks (safety measure).
        
    Returns:
        JSON with results of kill operations per server.
    """
    monitor = get_monitor()
    server_ids = [server_id] if server_id else None
    results = await monitor.kill_user_tasks(username, server_ids, confirm)
    return results


@app.prompt("summarize_gpu_availability")
def summarize_gpu_availability():
    """
    Summarize GPU availability across the cluster in natural language.
    
    Use this prompt with GPU status data to get a human-friendly summary
    of which servers are available for new jobs.
    
    Variables:
    - servers: JSON list of GPU server status objects
    """
    return """You are a helpful assistant analyzing GPU cluster availability.

Here is the current GPU server status:

{{servers}}

Provide a concise summary highlighting:
1. Which server is most available (lowest utilization, most free memory)
2. Overall cluster utilization 
3. Any servers that are offline or have issues
4. Recommendation for job placement

Format your response to be actionable for someone looking to start a new GPU job.
Use emojis like 🟢 for available, 🟡 for moderate usage, 🔴 for busy/unavailable."""


@app.prompt("analyze_user_usage") 
def analyze_user_usage():
    """
    Analyze a user's GPU usage and provide recommendations.
    
    Variables:
    - usage: JSON object with user's GPU usage summary
    - username: The username being analyzed
    """
    return """You are a helpful assistant analyzing GPU usage for user {{username}}.

Here is their current GPU usage:

{{usage}}

Provide an analysis including:
1. Total resource consumption (processes, memory)
2. Which servers they're using
3. Whether their usage seems efficient
4. Any recommendations for optimization

Be constructive and helpful in your analysis."""


@app.prompt("format_kill_confirmation")
def format_kill_confirmation():
    """
    Format a confirmation message for killing user processes.
    
    Variables:
    - username: Username whose processes will be killed
    - server_id: Server ID (or "all" for all servers)
    - process_count: Number of processes to be killed
    """
    return """⚠️  **CONFIRM PROCESS TERMINATION** ⚠️

You are about to kill {{process_count}} GPU processes for user {{username}} on {{server_id}}.

This action is IRREVERSIBLE and will:
- Terminate all running training/inference jobs
- Potentially lose unsaved work
- Free up GPU resources immediately

Type 'YES' to confirm, or 'NO' to cancel."""


def main():
    """Main entry point for the HTTP MCP server."""
    import argparse
    
    parser = argparse.ArgumentParser(description="GPU Monitor HTTP MCP Server")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8700, help="Port to bind to (default: 8700)")
    
    args = parser.parse_args()
    
    # Initialize global monitor with config
    global monitor
    monitor = GPUMonitor(args.config)
    
    print(f"🚀 Starting GPU Monitor HTTP MCP Server on {args.host}:{args.port}")
    print(f"📋 Monitoring {len(monitor.config.servers)} servers")
    print(f"🔗 VSCode config: {{\"servers\": {{\"gpu-mcp\": {{\"type\": \"http\", \"url\": \"http://{args.host}:{args.port}\"}}}}}}")
    
    # Run the HTTP MCP server
    app.run(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
