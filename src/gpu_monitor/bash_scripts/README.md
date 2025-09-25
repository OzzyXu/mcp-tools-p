# GPU Monitor - Bash Scripts

Basic GPU monitoring scripts for older servers without Python 3.8+.

## 🚀 What These Scripts Do

Same core functionality as the Python version, but in pure bash:
- **Check GPU status** across servers
- **Monitor user GPU usage** 
- **Kill user processes** safely

## 📋 Requirements

- **Bash 4.0+** (2009, available on all modern systems)
- **SSH access** to GPU servers (same as Python version)
- **nvidia-smi** on GPU servers
- Standard Unix tools: `grep`, `awk`, `timeout`

## 🛠️ Scripts

### 1. gpu_status.sh - Check GPU Status
```bash
# Check all servers
./gpu_status.sh

# Check specific server
./gpu_status.sh gpu01
```

**Example output:**
```
=== GPU Status Check ===
Timeout: 5s

Checking gpu01 (gpu01.cluster.local)...
✓ gpu01 - Online
  GPU0: 25% util, 14GB/16GB free
  GPU1: 85% util, 2GB/16GB free
  Total GPUs: 2

Checking gpu02 (gpu02.cluster.local)...
✗ gpu02 - SSH connection failed
```

### 2. gpu_usage.sh - Check User Usage
```bash
# Check your usage
./gpu_usage.sh

# Check specific user
./gpu_usage.sh john

# Check user on specific server
./gpu_usage.sh john gpu01
```

**Example output:**
```
=== GPU Usage for john ===

gpu01:
  GPU0: PID 12345, 2048MB - python train.py
  GPU1: PID 12346, 4096MB - python inference.py
  Total: 2 processes, 6GB memory

Summary:
  User: john
  Total processes: 2
  Servers with usage: 1
```

### 3. gpu_kill.sh - Kill User Processes
```bash
# Show what would be killed (dry run)
./gpu_kill.sh john

# Kill processes with confirmation
./gpu_kill.sh john --confirm

# Kill on specific server
./gpu_kill.sh john gpu01 --confirm
```

**Example output:**
```
=== Processes to kill for john ===

gpu01:
  GPU0: PID 12345 - python train.py
  GPU1: PID 12346 - python inference.py
  Processes to kill: 2

Summary:
  User: john
  Total processes to kill: 2
  Servers affected: 1

⚠️  Use --confirm to actually kill these processes
```

## ⚙️ Configuration

Edit the server list in each script:

```bash
# Configuration - Edit these for your cluster
SERVERS=(
    "gpu01:gpu01.cluster.local"
    "gpu02:gpu02.cluster.local"
    "gpu03:gpu03.cluster.local"
)
```

Format: `"server_id:hostname"`

## 🚀 Deployment

### Option 1: Copy Individual Scripts
```bash
# Copy to shared location
cp src/gpu_monitor/bash_scripts/*.sh /shared/tools/
chmod +x /shared/tools/*.sh

# Users run:
/shared/tools/gpu_status.sh
/shared/tools/gpu_usage.sh john
/shared/tools/gpu_kill.sh john --confirm
```

### Option 2: Create Wrapper Script
```bash
# Create all-in-one wrapper
cat > /shared/tools/gpu_monitor_bash << 'EOF'
#!/bin/bash
script_dir="$(dirname "$0")"
case "$1" in
    status) shift; "$script_dir/gpu_status.sh" "$@" ;;
    usage)  shift; "$script_dir/gpu_usage.sh" "$@" ;;
    kill)   shift; "$script_dir/gpu_kill.sh" "$@" ;;
    *) echo "Usage: $0 {status|usage|kill} [args...]" ;;
esac
EOF

chmod +x /shared/tools/gpu_monitor_bash

# Users run:
/shared/tools/gpu_monitor_bash status
/shared/tools/gpu_monitor_bash usage john
/shared/tools/gpu_monitor_bash kill john --confirm
```

## 🆚 Comparison with Python Version

| Feature | Python Script | Bash Scripts |
|---------|---------------|--------------|
| **Requirements** | Python 3.8+ | Bash 4.0+ |
| **Compatibility** | Modern systems | Any Unix/Linux |
| **Installation** | Copy one file | Copy 3 files or use wrapper |
| **Features** | Full functionality | Basic functionality |
| **Output** | Formatted/JSON | Simple text |
| **Caching** | Built-in | None |
| **Concurrency** | Yes | Sequential |
| **Error handling** | Advanced | Basic |

## 🔧 Customization

### Adjust Timeouts
```bash
SSH_TIMEOUT=10  # Increase for slow networks
```

### Disable Colors
```bash
# Set these to empty at the top of scripts
RED=''
GREEN=''
YELLOW=''
NC=''
```

### Add More Servers
```bash
SERVERS=(
    "gpu01:gpu01.cluster.local"
    "gpu02:gpu02.cluster.local"
    "gpu03:gpu03.cluster.local"
    "gpu04:gpu04.cluster.local"  # Add more as needed
)
```

## 🐛 Troubleshooting

**"Command not found: timeout"**
- Use `gtimeout` on macOS: `brew install coreutils`
- Or remove `timeout` prefix for basic functionality

**"SSH connection failed"**
- Check SSH key setup: `ssh gpu01.cluster.local`
- Verify hostnames in configuration
- Check network connectivity

**"nvidia-smi not found"**
- Scripts expect nvidia-smi in PATH on GPU servers
- Some systems need: `/usr/bin/nvidia-smi` or `/usr/local/cuda/bin/nvidia-smi`

**No processes shown**
- Scripts look for exact username match
- Check with: `ssh gpu01 "nvidia-smi pmon -c 1"`

## 📈 Performance

These bash scripts are:
- **Fast**: No Python startup overhead
- **Lightweight**: Minimal memory usage  
- **Reliable**: Use standard Unix tools
- **Sequential**: Check servers one by one (not parallel like Python version)

For large clusters (10+ servers), the Python version will be faster due to concurrency.

## 🔒 Security

Same security model as Python version:
- Uses existing SSH keys and configuration
- No password storage
- Requires explicit confirmation for destructive operations
- Limited to nvidia-smi and kill commands
