"""CLI interface for GPU cluster monitoring (failure-safe standalone script)."""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Optional

import click

from .core import GPUMonitor
from .models import ClusterStatus, UserUsageSummary


def get_current_user() -> str:
    """Get current user from environment."""
    return os.environ.get('USER', 'unknown')


def format_gpu_status(status: ClusterStatus) -> str:
    """Format GPU status for CLI output."""
    output = []
    output.append(f"🖥️  GPU Cluster Status ({status.online_servers}/{status.total_servers} servers online)")
    output.append(f"📊 Total GPUs: {status.total_gpus}")
    output.append("")
    
    for server in status.servers:
        if server.online:
            output.append(f"🟢 {server.server_id} ({server.hostname}) - {server.response_time_ms:.1f}ms")
            
            if not server.gpus:
                output.append("   No GPU information available")
                continue
                
            for gpu in server.gpus:
                utilization_emoji = "🟢" if gpu.utilization_percent < 30 else "🟡" if gpu.utilization_percent < 70 else "🔴"
                memory_gb = gpu.memory_total_mb / 1024
                free_gb = gpu.memory_free_mb / 1024
                output.append(f"   {utilization_emoji} GPU{gpu.index}: {gpu.utilization_percent}% util, {free_gb:.1f}/{memory_gb:.1f}GB free")
            
            if server.processes:
                output.append(f"   👥 {len(server.processes)} active processes")
        else:
            output.append(f"🔴 {server.server_id} ({server.hostname}) - OFFLINE")
            if server.error_message:
                output.append(f"   Error: {server.error_message}")
        
        output.append("")
    
    return "\n".join(output)


def format_user_usage(usage: UserUsageSummary) -> str:
    """Format user usage for CLI output."""
    output = []
    output.append(f"👤 GPU Usage for {usage.username}")
    output.append(f"📊 {usage.total_processes} processes using {usage.total_memory_used_mb/1024:.1f}GB total")
    output.append(f"🖥️  Active on: {', '.join(usage.servers_used) if usage.servers_used else 'None'}")
    output.append("")
    
    if not usage.processes_by_server:
        output.append("No active GPU processes found.")
        return "\n".join(output)
    
    for server_id, processes in usage.processes_by_server.items():
        output.append(f"🖥️  {server_id}:")
        for proc in processes:
            memory_gb = proc.memory_used_mb / 1024
            output.append(f"   • PID {proc.pid} on GPU{proc.gpu_index}: {memory_gb:.1f}GB - {proc.process_name}")
        output.append("")
    
    return "\n".join(output)


@click.group()
@click.option('--config', '-c', help='Path to configuration file')
@click.pass_context
def cli(ctx, config):
    """GPU Cluster Monitor - Check status, usage, and manage GPU tasks."""
    ctx.ensure_object(dict)
    ctx.obj['config'] = config


@cli.command()
@click.option('--server', '-s', help='Server ID to check (default: all servers)')
@click.option('--json-output', '--json', is_flag=True, help='Output in JSON format')
@click.pass_context
def status(ctx, server, json_output):
    """Check GPU status for all servers or a specific server."""
    async def _status():
        monitor = GPUMonitor(ctx.obj['config'])
        server_ids = [server] if server else None
        cluster_status = await monitor.get_cluster_status(server_ids)
        
        if json_output:
            click.echo(cluster_status.model_dump_json(indent=2))
        else:
            click.echo(format_gpu_status(cluster_status))
    
    asyncio.run(_status())


@cli.command()
@click.option('--user', '-u', help='Username to check (default: current user from $USER)')
@click.option('--server', '-s', help='Server ID to check (default: all servers)')
@click.option('--json-output', '--json', is_flag=True, help='Output in JSON format')
@click.pass_context
def usage(ctx, user, server, json_output):
    """Check GPU usage for a user across servers."""
    username = user or get_current_user()
    
    async def _usage():
        monitor = GPUMonitor(ctx.obj['config'])
        server_ids = [server] if server else None
        user_usage = await monitor.get_user_usage(username, server_ids)
        
        if json_output:
            click.echo(user_usage.model_dump_json(indent=2))
        else:
            click.echo(format_user_usage(user_usage))
    
    asyncio.run(_usage())


@cli.command()
@click.option('--user', '-u', help='Username to kill tasks for (default: current user from $USER)')
@click.option('--server', '-s', help='Server ID to kill tasks on (default: all servers)')
@click.option('--confirm', is_flag=True, help='Confirm the kill operation')
@click.option('--dry-run', is_flag=True, help='Show what would be killed without actually doing it')
@click.pass_context
def kill(ctx, user, server, confirm, dry_run):
    """Kill GPU tasks for a user."""
    username = user or get_current_user()
    
    async def _kill():
        monitor = GPUMonitor(ctx.obj['config'])
        server_ids = [server] if server else None
        
        # First, show what processes would be killed
        usage = await monitor.get_user_usage(username, server_ids)
        
        if not usage.processes_by_server:
            click.echo(f"No active GPU processes found for user {username}.")
            return
        
        click.echo(f"🎯 Processes to kill for user {username}:")
        for server_id, processes in usage.processes_by_server.items():
            click.echo(f"  {server_id}: {len(processes)} processes")
            for proc in processes:
                click.echo(f"    • PID {proc.pid} on GPU{proc.gpu_index}: {proc.process_name}")
        
        if dry_run:
            click.echo("\n🔍 Dry run - no processes were actually killed.")
            return
        
        if not confirm:
            if click.confirm(f"\n⚠️  Kill {usage.total_processes} processes for {username}?"):
                confirm = True
            else:
                click.echo("Operation cancelled.")
                return
        
        if confirm:
            click.echo(f"\n💀 Killing processes for {username}...")
            results = await monitor.kill_user_tasks(username, server_ids, confirm=True)
            
            for server_id, result in results.items():
                if isinstance(result, str):
                    if "Killed" in result:
                        click.echo(f"✅ {server_id}: {result}")
                    else:
                        click.echo(f"❌ {server_id}: {result}")
                else:
                    click.echo(f"❓ {server_id}: {result}")
    
    asyncio.run(_kill())


@cli.command()
@click.pass_context  
def config(ctx):
    """Show current configuration."""
    try:
        monitor = GPUMonitor(ctx.obj['config'])
        click.echo("📋 Current Configuration:")
        click.echo(f"Servers: {len(monitor.config.servers)}")
        for server in monitor.config.servers:
            click.echo(f"  • {server.id}: {server.hostname} - {server.description}")
        
        click.echo(f"\nSettings:")
        for key, value in monitor.config.settings.items():
            click.echo(f"  • {key}: {value}")
            
    except Exception as e:
        click.echo(f"❌ Error loading configuration: {e}")


@cli.command()
def install():
    """Install the script to a shared location for failure-safe access."""
    script_path = Path(__file__).resolve()
    
    # Suggest common shared locations
    shared_locations = [
        "/shared/tools",
        "/opt/tools", 
        "/usr/local/bin",
        f"{Path.home()}/shared/tools"
    ]
    
    click.echo("📦 To install this script for failure-safe access:")
    click.echo("Choose a shared location accessible by all users:")
    
    for i, location in enumerate(shared_locations, 1):
        click.echo(f"  {i}. {location}")
    
    click.echo(f"\nExample installation:")
    click.echo(f"  sudo mkdir -p /shared/tools")
    click.echo(f"  sudo cp {script_path} /shared/tools/gpu_monitor.py")
    click.echo(f"  sudo chmod +x /shared/tools/gpu_monitor.py")
    click.echo(f"\nThen users can run: /shared/tools/gpu_monitor.py status")


def main():
    """Main entry point for the CLI."""
    cli()


# Make the script executable directly
if __name__ == "__main__":
    main()
