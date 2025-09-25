"""Main entry point for GPU Monitor."""

from gpu_monitor.server import main as mcp_main
from gpu_monitor.cli import main as cli_main
import sys


def main():
    """Entry point that routes to MCP server or CLI based on arguments."""
    if len(sys.argv) > 1 and sys.argv[1] in ['status', 'usage', 'kill', 'config', 'install']:
        # CLI mode
        cli_main()
    else:
        # MCP server mode
        print("Starting GPU Monitor MCP Server...")
        print("Use 'uv run python main.py status' for CLI mode")
        print("Or use dedicated commands: 'uv run gpu-monitor status' or 'uv run gpu-mcp-server'")
        print("Config file: src/gpu_monitor/servers.json")
        mcp_main()


if __name__ == "__main__":
    main()
