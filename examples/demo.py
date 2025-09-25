#!/usr/bin/env python3
"""Demo script for GPU Cluster Monitor."""

import asyncio
import json
import os
from gpu_monitor.core import GPUMonitor
from gpu_monitor.models import ClusterConfig, ServerConfig


async def demo():
    """Run a demo of the GPU cluster monitor."""
    print("🚀 GPU Cluster Monitor Demo")
    print("=" * 50)
    
    # Create a demo configuration
    demo_config = ClusterConfig(
        servers=[
            ServerConfig(
                id="demo-gpu01",
                hostname="localhost",  # Use localhost for demo
                description="Demo GPU server 1"
            ),
            ServerConfig(
                id="demo-gpu02", 
                hostname="127.0.0.1",  # Use localhost for demo
                description="Demo GPU server 2"
            )
        ],
        settings={
            "cache_ttl": 5,  # Short cache for demo
            "ssh_timeout": 2,
            "max_concurrent": 2
        }
    )
    
    # Initialize monitor with demo config
    monitor = GPUMonitor()
    monitor.config = demo_config
    
    print(f"📋 Configuration loaded:")
    print(f"   Servers: {len(monitor.config.servers)}")
    for server in monitor.config.servers:
        print(f"   • {server.id}: {server.hostname}")
    print()
    
    # Demo 1: Check cluster status
    print("🔍 Demo 1: Checking cluster status...")
    try:
        status = await monitor.get_cluster_status()
        print(f"   Total servers: {status.total_servers}")
        print(f"   Online servers: {status.online_servers}")
        
        for server in status.servers:
            if server.online:
                print(f"   ✅ {server.server_id}: Online ({server.response_time_ms:.1f}ms)")
            else:
                print(f"   ❌ {server.server_id}: Offline - {server.error_message}")
    except Exception as e:
        print(f"   ⚠️  Demo servers not accessible (expected): {e}")
    print()
    
    # Demo 2: Check user usage
    print("🔍 Demo 2: Checking user usage...")
    current_user = os.environ.get('USER', 'demo-user')
    try:
        usage = await monitor.get_user_usage(current_user)
        print(f"   User: {usage.username}")
        print(f"   Total processes: {usage.total_processes}")
        print(f"   Servers used: {usage.servers_used}")
    except Exception as e:
        print(f"   ⚠️  Demo servers not accessible (expected): {e}")
    print()
    
    # Demo 3: Show configuration
    print("📋 Demo 3: Configuration details...")
    print(f"   Cache TTL: {monitor.config.settings['cache_ttl']}s")
    print(f"   SSH timeout: {monitor.config.settings['ssh_timeout']}s")
    print(f"   Max concurrent: {monitor.config.settings['max_concurrent']}")
    print()
    
    print("✅ Demo completed!")
    print("\n📖 Next steps:")
    print("1. Edit src/gpu_monitor/servers.json with your actual GPU server hostnames")
    print("2. Test CLI: uv run gpu-monitor status")
    print("3. Start MCP server: uv run gpu-mcp-server")
    print("4. Install for team: uv sync && uv pip install -e .")


if __name__ == "__main__":
    asyncio.run(demo())
