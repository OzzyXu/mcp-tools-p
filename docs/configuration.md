# GPU Monitor Configuration

This document explains how to configure the GPU Monitor tool.

## Server Configuration

The GPU Monitor uses a JSON configuration file to define the cluster servers and settings. The default configuration is located at `src/gpu_monitor/server_config.json`.

### Basic Configuration Structure

```json
{
  "servers": [
    {
      "id": "gpu01",
      "hostname": "gpu01.cluster.local",
      "description": "Primary training server"
    },
    {
      "id": "gpu02", 
      "hostname": "gpu02.cluster.local",
      "description": "Secondary training server"
    }
  ],
  "settings": {
    "cache_ttl": 30,
    "ssh_timeout": 5,
    "max_concurrent": 4
  }
}
```

### Server Configuration Fields

Each server in the `servers` array requires:

- **`id`** (string, required): Unique identifier for the server
- **`hostname`** (string, required): SSH hostname or IP address  
- **`description`** (string, optional): Human-readable description

### Settings Configuration

The `settings` object controls runtime behavior:

| Setting | Default | Description |
|---------|---------|-------------|
| `cache_ttl` | 30 | Cache time-to-live in seconds |
| `ssh_timeout` | 5 | SSH connection timeout in seconds |
| `max_concurrent` | 4 | Maximum concurrent SSH connections |

### Configuration Details

#### Cache TTL (`cache_ttl`)
- Controls how long GPU status is cached before refreshing
- Lower values = more up-to-date data, higher server load
- Higher values = reduced server load, slightly stale data
- Recommended: 15-60 seconds depending on usage patterns

#### SSH Timeout (`ssh_timeout`)
- Maximum time to wait for SSH connection establishment
- Should account for network latency and server responsiveness
- Too low: false negatives for slow servers
- Too high: long waits for truly offline servers
- Recommended: 3-10 seconds

#### Max Concurrent (`max_concurrent`)
- Limits simultaneous SSH connections to prevent overwhelming servers
- Higher values = faster cluster-wide status checks
- Lower values = gentler on network/servers but slower updates
- Should not exceed server SSH connection limits
- Recommended: 4-8 for typical clusters

### Advanced Configuration

#### Custom Configuration File Location

```bash
# CLI usage
gpu-monitor --config /custom/path/server_config.json status

# MCP server usage  
gpu-mcp-server --config /custom/path/server_config.json

# Standalone script usage
./src/gpu_monitor/gpumonitor --config /custom/path/server_config.json status
```

#### Environment-Specific Configurations

You can maintain different configurations for different environments:

```bash
# Development
servers_dev.json

# Production
servers_prod.json

# Testing
servers_test.json
```

#### Large Cluster Considerations

For clusters with many servers (20+), consider:

```json
{
  "settings": {
    "cache_ttl": 60,
    "ssh_timeout": 3,
    "max_concurrent": 8
  }
}
```

### Configuration Validation

The tool validates configuration on startup:

- **Server IDs must be unique**
- **Hostnames must be valid**
- **Settings must be positive integers**
- **Missing required fields will cause startup failure**

### Default Configuration

If no configuration file is found, the tool creates a default configuration with:

```json
{
  "servers": [
    {
      "id": "gpu01",
      "hostname": "gpu01.cluster.local",
      "description": "Primary training server"
    }
  ],
  "settings": {
    "cache_ttl": 30,
    "ssh_timeout": 5,
    "max_concurrent": 4
  }
}
```

### Troubleshooting Configuration

#### Common Issues

1. **"Server not found" errors**
   - Check server ID spelling in commands
   - Verify server is listed in configuration

2. **SSH connection failures**
   - Verify hostnames are reachable
   - Check SSH key authentication is set up
   - Increase `ssh_timeout` if network is slow

3. **Slow performance**
   - Increase `max_concurrent` for faster parallel checks
   - Increase `cache_ttl` to reduce refresh frequency
   - Check network latency to servers

#### Configuration Testing

Test your configuration:

```bash
# Check configuration is valid
gpu-monitor config

# Test connectivity to all servers
gpu-monitor status

# Test specific server
gpu-monitor status --server gpu01
```

### Security Considerations

- **SSH Keys**: The tool relies on your existing SSH key authentication
- **File Permissions**: Ensure configuration files have appropriate permissions
- **Network Security**: SSH connections use your existing network security setup
- **No Credentials**: No passwords or keys are stored in configuration files
