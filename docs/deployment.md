# GPU Monitor Deployment Guide

This guide covers deploying GPU Monitor for team use in production environments.

## Overview

GPU Monitor has two deployment components:

1. **HTTP MCP Server**: Centralized service running on the cluster controller (port 8700)
2. **Standalone Script**: Failure-safe script with no dependencies, accessible to all users

## Prerequisites

- Python 3.11+
- UV package manager
- SSH access to GPU cluster nodes
- Cluster controller node for MCP server deployment

## Production Deployment

### 1. Install GPU Monitor

On the cluster controller node:

```bash
# Clone the repository
git clone <your-repo> /opt/gpu-monitor
cd /opt/gpu-monitor

# Install with UV
uv sync
uv pip install -e .
```

### 2. Configure the Cluster

Edit the server configuration:

```bash
# Copy template
cp src/gpu_monitor/servers.json /etc/gpu-monitor/servers.json

# Edit with your cluster details
sudo vim /etc/gpu-monitor/servers.json
```

Example production configuration:

```json
{
  "servers": [
    {
      "id": "gpu01",
      "hostname": "gpu01.cluster.internal",
      "description": "Primary training server - 8x A100"
    },
    {
      "id": "gpu02",
      "hostname": "gpu02.cluster.internal", 
      "description": "Secondary training server - 8x A100"
    },
    {
      "id": "gpu03",
      "hostname": "gpu03.cluster.internal",
      "description": "Inference server - 4x A100"
    }
  ],
  "settings": {
    "cache_ttl": 30,
    "ssh_timeout": 5,
    "max_concurrent": 6
  }
}
```

### 3. Set Up Systemd Service

Create the systemd service file:

```bash
sudo tee /etc/systemd/system/gpu-monitor.service << 'EOF'
[Unit]
Description=GPU Monitor MCP Server
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=gpu-monitor
Group=gpu-monitor
WorkingDirectory=/opt/gpu-monitor
Environment=PATH=/opt/gpu-monitor/.venv/bin:/usr/local/bin:/usr/bin:/bin
ExecStart=/opt/gpu-monitor/.venv/bin/gpu-mcp-server --config /etc/gpu-monitor/servers.json --host 0.0.0.0 --port 8700
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

# Security settings
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/log/gpu-monitor
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF
```

### 4. Create Service User

```bash
# Create dedicated user for the service
sudo useradd --system --no-create-home --shell /bin/false gpu-monitor

# Create log directory
sudo mkdir -p /var/log/gpu-monitor
sudo chown gpu-monitor:gpu-monitor /var/log/gpu-monitor

# Set ownership
sudo chown -R gpu-monitor:gpu-monitor /opt/gpu-monitor
sudo chown gpu-monitor:gpu-monitor /etc/gpu-monitor/servers.json
```

### 5. Configure SSH for Service User

The GPU Monitor service needs SSH access to cluster nodes:

```bash
# Switch to service user
sudo -u gpu-monitor bash

# Generate SSH key (no passphrase for service)
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519 -N ""

# Copy public key to all GPU nodes
for server in gpu01 gpu02 gpu03; do
    ssh-copy-id -i ~/.ssh/id_ed25519.pub monitor@$server.cluster.internal
done

# Test connectivity
ssh gpu01.cluster.internal "nvidia-smi --version"
```

### 6. Start and Enable Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable and start the service
sudo systemctl enable gpu-monitor
sudo systemctl start gpu-monitor

# Check status
sudo systemctl status gpu-monitor

# View logs
sudo journalctl -u gpu-monitor -f
```

### 7. Configure Firewall

If using a firewall, allow access to the HTTP MCP server:

```bash
# UFW example
sudo ufw allow 8700/tcp

# firewalld example  
sudo firewall-cmd --permanent --add-port=8700/tcp
sudo firewall-cmd --reload
```

## Failure-Safe Script Deployment

### 1. Deploy Python Script (Recommended)

```bash
# Create shared tools directory
sudo mkdir -p /shared/tools

# Copy Python standalone script (requires Python 3.8+)
sudo cp /opt/gpu-monitor/src/gpu_monitor/gpumonitor /shared/tools/gpumonitor
sudo chmod +x /shared/tools/gpumonitor

# Optionally copy configuration (script has defaults built-in)
sudo cp /etc/gpu-monitor/servers.json /shared/tools/servers.json
sudo chmod 644 /shared/tools/servers.json
```

### 1b. Deploy Bash Scripts (Older Systems)

For servers without Python 3.8+:

```bash
# Copy bash scripts (requires only Bash 4.0+)
sudo cp /opt/gpu-monitor/src/gpu_monitor/scripts/*.sh /shared/tools/
sudo chmod +x /shared/tools/*.sh

# Edit configuration in each script
sudo vim /shared/tools/gpu_status.sh
sudo vim /shared/tools/gpu_usage.sh  
sudo vim /shared/tools/gpu_kill.sh
```

### 2. Update User Profiles

Add to system-wide profile (e.g., `/etc/profile.d/gpu-monitor.sh`):

```bash
sudo tee /etc/profile.d/gpu-monitor.sh << 'EOF'
# GPU Monitor Scripts
export PATH="/shared/tools:$PATH"

# Python version (recommended)
alias gpu-status="/shared/tools/gpumonitor status"
alias gpu-usage="/shared/tools/gpumonitor usage"
alias gpu-kill="/shared/tools/gpumonitor kill"

# Bash version (fallback for older systems)
alias gpu-status-bash="/shared/tools/gpu_status.sh"
alias gpu-usage-bash="/shared/tools/gpu_usage.sh"
alias gpu-kill-bash="/shared/tools/gpu_kill.sh"
EOF
```

### 3. Script Comparison

#### Python Script
- **Dependencies**: Python 3.8+ (standard on most systems)
- **Features**: Full functionality, JSON output, caching
- **Performance**: Fast concurrent operations
- **File count**: 1 file

#### Bash Scripts  
- **Dependencies**: Bash 4.0+ (works on any Unix/Linux)
- **Features**: Basic functionality, simple text output
- **Performance**: Sequential operations (slower for many servers)
- **File count**: 3 files

Both options:
- **No Installation**: Copy and run immediately
- **Self-Contained**: All logic included
- **Configurable**: Edit scripts directly or use external config

## Load Balancer Setup (Optional)

For high availability, deploy multiple MCP servers behind a load balancer:

### HAProxy Configuration

```bash
# /etc/haproxy/haproxy.cfg
global
    daemon

defaults
    mode http
    timeout connect 5s
    timeout client 30s
    timeout server 30s

frontend gpu_monitor_frontend
    bind *:8700
    default_backend gpu_monitor_backend

backend gpu_monitor_backend
    balance roundrobin
    server controller1 controller1.cluster.internal:8700 check
    server controller2 controller2.cluster.internal:8700 check
```

## Monitoring and Logging

### 1. Log Configuration

Configure structured logging in the MCP server:

```bash
# /etc/gpu-monitor/logging.json
{
  "version": 1,
  "formatters": {
    "detailed": {
      "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    }
  },
  "handlers": {
    "file": {
      "class": "logging.handlers.RotatingFileHandler",
      "filename": "/var/log/gpu-monitor/gpu-monitor.log",
      "maxBytes": 10485760,
      "backupCount": 5,
      "formatter": "detailed"
    }
  },
  "root": {
    "level": "INFO",
    "handlers": ["file"]
  }
}
```

### 2. Health Monitoring

Set up health checks:

```bash
# Health check script for HTTP MCP server
sudo tee /usr/local/bin/gpu-monitor-health << 'EOF'
#!/bin/bash
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8700/healthz)
if [ "$response" = "200" ]; then
    echo "OK: GPU Monitor is healthy"
    exit 0
else
    echo "CRITICAL: GPU Monitor is unhealthy (HTTP $response)"
    exit 2
fi
EOF

sudo chmod +x /usr/local/bin/gpu-monitor-health
```

### 3. Alerting Integration

Example integration with monitoring systems:

```bash
# Prometheus metrics endpoint (if implemented)
curl http://localhost:8700/metrics

# Custom alerting script
sudo tee /usr/local/bin/gpu-monitor-alert << 'EOF'
#!/bin/bash
# Check if any GPUs are completely idle for >1 hour
# Alert if cluster utilization drops below threshold
# Send notifications via Slack/email
EOF
```

## Backup and Recovery

### 1. Configuration Backup

```bash
# Backup script
sudo tee /usr/local/bin/backup-gpu-monitor << 'EOF'
#!/bin/bash
BACKUP_DIR="/backup/gpu-monitor/$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"

# Backup configuration
cp /etc/gpu-monitor/servers.json "$BACKUP_DIR/"
cp /etc/systemd/system/gpu-monitor.service "$BACKUP_DIR/"

# Backup logs (last 7 days)
find /var/log/gpu-monitor -name "*.log*" -mtime -7 -exec cp {} "$BACKUP_DIR/" \;

echo "Backup completed: $BACKUP_DIR"
EOF

sudo chmod +x /usr/local/bin/backup-gpu-monitor
```

### 2. Disaster Recovery

```bash
# Recovery script
sudo tee /usr/local/bin/restore-gpu-monitor << 'EOF'
#!/bin/bash
BACKUP_DIR="$1"

if [ -z "$BACKUP_DIR" ]; then
    echo "Usage: $0 <backup_directory>"
    exit 1
fi

# Stop service
systemctl stop gpu-monitor

# Restore configuration
cp "$BACKUP_DIR/servers.json" /etc/gpu-monitor/
cp "$BACKUP_DIR/gpu-monitor.service" /etc/systemd/system/

# Reload and restart
systemctl daemon-reload
systemctl start gpu-monitor
systemctl status gpu-monitor
EOF

sudo chmod +x /usr/local/bin/restore-gpu-monitor
```

## Security Hardening

### 1. Network Security

```bash
# Restrict access to specific networks for HTTP MCP server
sudo ufw allow from 10.0.0.0/8 to any port 8700
sudo ufw allow from 192.168.0.0/16 to any port 8700
sudo ufw deny 8700
```

### 2. Service Security

The systemd service includes security settings:
- `NoNewPrivileges=true` - Prevents privilege escalation
- `ProtectSystem=strict` - Read-only filesystem access
- `ProtectHome=true` - No access to user home directories
- `PrivateTmp=true` - Isolated temporary directory

### 3. SSH Key Management

```bash
# Rotate SSH keys periodically
sudo -u gpu-monitor ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519_new -N ""

# Update authorized_keys on all nodes
for server in gpu01 gpu02 gpu03; do
    ssh-copy-id -i ~/.ssh/id_ed25519_new.pub monitor@$server.cluster.internal
done

# Test new key
ssh -i ~/.ssh/id_ed25519_new gpu01.cluster.internal "echo 'New key works'"

# Replace old key
sudo -u gpu-monitor mv ~/.ssh/id_ed25519_new ~/.ssh/id_ed25519
sudo -u gpu-monitor mv ~/.ssh/id_ed25519_new.pub ~/.ssh/id_ed25519.pub
```

## Troubleshooting

### Common Issues

1. **Service won't start**
   ```bash
   # Check logs
   sudo journalctl -u gpu-monitor -f
   
   # Verify configuration
   sudo -u gpu-monitor gpu-mcp-server --config /etc/gpu-monitor/servers.json --help
   ```

2. **SSH connection failures**
   ```bash
   # Test SSH manually
   sudo -u gpu-monitor ssh gpu01.cluster.internal "nvidia-smi"
   
   # Check SSH agent
   sudo -u gpu-monitor ssh-add -l
   ```

3. **Performance issues**
   ```bash
   # Monitor resource usage
   sudo systemctl status gpu-monitor
   htop -p $(pgrep -f gpu-mcp-server)
   
   # Check network latency
   ping gpu01.cluster.internal
   ```

### Maintenance

```bash
# Regular maintenance tasks
sudo tee /etc/cron.daily/gpu-monitor-maintenance << 'EOF'
#!/bin/bash
# Rotate logs
/usr/sbin/logrotate /etc/logrotate.d/gpu-monitor

# Clean old cache files
find /tmp -name "gpu-monitor-*" -mtime +1 -delete

# Backup configuration
/usr/local/bin/backup-gpu-monitor
EOF

sudo chmod +x /etc/cron.daily/gpu-monitor-maintenance
```

This deployment guide ensures a robust, secure, and maintainable GPU Monitor installation for team use.
