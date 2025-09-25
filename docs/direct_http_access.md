# Direct HTTP Access to GPU Monitor

Connect to the GPU Monitor MCP server directly via HTTP without SSH or port forwarding.

## 🌐 Direct HTTP Connection

Instead of using Remote-SSH and port forwarding, you can connect directly to the GPU Monitor server using its network address.

### Prerequisites

1. **GPU Monitor server** is running on the cluster controller
2. **Network access** from your machine to the server
3. **Firewall rules** allow access to port 8700
4. **Python 3.8+** for standalone script (if needed as backup)

### Setup Steps

#### Step 1: Get Server Address

Ask your admin for the server's network address. It could be:
- **Internal IP**: `http://10.0.1.100:8700`
- **Hostname**: `http://gpu-controller.cluster.local:8700`
- **Public domain**: `http://gpu-monitor.company.com:8700`

#### Step 2: Test Connection

Open your browser and visit the server URL:
```
http://your-server-address:8700
```

You should see a response indicating the MCP server is running.

#### Step 3: Configure VSCode MCP

Add this to your VSCode MCP settings:

```json
{
  "servers": {
    "gpu-mcp": { 
      "type": "http", 
      "url": "http://your-server-address:8700" 
    }
  }
}
```

**Examples:**
```json
{
  "servers": {
    "gpu-mcp": { 
      "type": "http", 
      "url": "http://10.0.1.100:8700" 
    }
  }
}
```

```json
{
  "servers": {
    "gpu-mcp": { 
      "type": "http", 
      "url": "http://gpu-controller.cluster.local:8700" 
    }
  }
}
```

#### Step 4: Use Copilot

Now you can ask Copilot questions without any SSH connection:
```
"Which GPU server is free?"
"Show my current GPU usage"
"Kill all my processes on gpu01"
```

## 🔧 Network Configuration (Admin Guide)

### Server Setup

The GPU Monitor HTTP server needs to be accessible from user machines:

#### 1. Bind to All Interfaces

Start the server with `--host 0.0.0.0` instead of `127.0.0.1`:

```bash
uv run gpu-mcp-server --host 0.0.0.0 --port 8700
```

#### 2. Firewall Configuration

Allow incoming connections on port 8700:

```bash
# UFW (Ubuntu)
sudo ufw allow 8700/tcp

# firewalld (CentOS/RHEL)
sudo firewall-cmd --permanent --add-port=8700/tcp
sudo firewall-cmd --reload

# iptables
sudo iptables -A INPUT -p tcp --dport 8700 -j ACCEPT
```

#### 3. Network Security (Optional)

Restrict access to specific networks:

```bash
# Allow only internal network
sudo ufw allow from 10.0.0.0/8 to any port 8700
sudo ufw allow from 192.168.0.0/16 to any port 8700

# Deny all other access
sudo ufw deny 8700/tcp
```

#### 4. Systemd Service Update

Update the systemd service to bind to all interfaces:

```bash
# Edit /etc/systemd/system/gpu-monitor.service
ExecStart=/opt/gpu-monitor/.venv/bin/gpu-mcp-server --config /etc/gpu-monitor/servers.json --host 0.0.0.0 --port 8700

# Reload and restart
sudo systemctl daemon-reload
sudo systemctl restart gpu-monitor
```

## 🆚 Comparison: Direct HTTP vs SSH Port Forwarding

### Direct HTTP Access
✅ **Pros:**
- No SSH connection required
- Works from any network location
- Simpler setup for users
- Better for distributed teams
- Persistent connection

❌ **Cons:**
- Requires network firewall configuration
- Potential security exposure
- Admin needs to manage network access

### SSH Port Forwarding
✅ **Pros:**
- Uses existing SSH infrastructure
- Automatic security via SSH
- No firewall changes needed
- Works with existing Remote-SSH workflows

❌ **Cons:**
- Requires SSH access to server
- More complex user setup
- Connection tied to SSH session
- Doesn't work for local VSCode

## 🔒 Security Considerations

### Network Security
- **Use internal networks** when possible
- **Implement IP whitelisting** for sensitive environments
- **Consider VPN access** for remote users
- **Monitor access logs** for suspicious activity

### Application Security
The GPU Monitor MCP server includes:
- **Rate limiting** to prevent abuse
- **Input validation** on all requests
- **No authentication bypass** - relies on network security
- **Read-only operations** for status checking

### Recommended Setup
```bash
# Bind to internal network interface only
gpu-mcp-server --host 10.0.1.100 --port 8700

# Or use reverse proxy with HTTPS
nginx → https://gpu-monitor.company.com → http://localhost:8700
```

## 🌐 Advanced: Reverse Proxy Setup

For production environments, use a reverse proxy:

### Nginx Configuration
```nginx
server {
    listen 443 ssl;
    server_name gpu-monitor.company.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:8700;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Apache Configuration
```apache
<VirtualHost *:443>
    ServerName gpu-monitor.company.com
    
    SSLEngine on
    SSLCertificateFile /path/to/cert.pem
    SSLCertificateKeyFile /path/to/key.pem
    
    ProxyPreserveHost On
    ProxyPass / http://localhost:8700/
    ProxyPassReverse / http://localhost:8700/
</VirtualHost>
```

## 🧪 Testing Direct Access

### 1. Test Server Connectivity
```bash
# From user machine
curl http://your-server-address:8700

# Should return MCP server response
```

### 2. Test MCP Functionality
```bash
# Test specific endpoints
curl http://your-server-address:8700/resources
curl http://your-server-address:8700/tools
```

### 3. Verify VSCode Connection
1. Add the HTTP configuration to VSCode MCP settings
2. Restart VSCode
3. Ask Copilot a test question
4. Check that it responds with GPU data

## ❓ Troubleshooting

**"Connection refused"**
- Check if server is running: `systemctl status gpu-monitor`
- Verify port binding: `netstat -tlnp | grep 8700`
- Test firewall: `sudo ufw status`

**"Server not accessible from remote machine"**
- Verify server binds to `0.0.0.0` not `127.0.0.1`
- Check network firewall rules
- Test with `telnet server-address 8700`

**"VSCode MCP connection fails"**
- Verify URL format: `http://server:8700` (no trailing slash)
- Check VSCode MCP extension logs
- Test URL directly in browser first

**"Slow responses"**
- Check network latency: `ping server-address`
- Monitor server resources: `htop`
- Consider caching settings in configuration

---

**This approach eliminates the need for SSH port forwarding and provides direct HTTP access to the GPU Monitor for distributed teams.**
