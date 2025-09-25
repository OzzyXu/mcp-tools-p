# GPU Monitor - User Guide

Quick setup guide for team members.

## 🚀 What You Get

Ask your GPUs questions in plain English:
- **"Which GPU server is free?"**
- **"Show my current GPU usage"** 
- **"Kill all my processes on gpu01"**

## 💬 VSCode Setup (Recommended)

### Step 1: Forward Port 8700

**Option A - Ports Panel:**
1. Connect via Remote-SSH to your server
2. Open Command Palette: `Ctrl+Shift+P`
3. Type: **"Ports: Focus on Ports View"**
4. Click **"Add Port"** → Enter `8700`

**Option B - One-Click Task:**
1. Open Command Palette: `Ctrl+Shift+P` 
2. Type: **"Tasks: Run Task"**
3. Select: **"Forward GPU Monitor Port"**
4. Follow the instructions shown

### Step 2: Configure MCP

Add this to your VSCode MCP settings file:

```json
{
  "servers": {
    "gpu-mcp": { 
      "type": "http", 
      "url": "http://127.0.0.1:8700" 
    }
  }
}
```

**Where to add this:**
- **VSCode 1.103+**: Settings → Extensions → MCP → Edit Configuration
- **Or**: Manually edit your MCP settings file

### Step 3: Ask Questions

Now you can ask Copilot:
```
"Which GPU server has the most free memory?"
"Show my current GPU usage"
"Kill all my processes on gpu01"
```

## 🛠️ Command Line (Backup Method)

If VSCode isn't working, use these commands:

### Option 1: Python Script (Recommended)
**Requirements:** Python 3.8+ (standard on most systems)

```bash
# Check GPU status on all servers
/shared/tools/gpumonitor status

# Check your GPU usage
/shared/tools/gpumonitor usage

# Check someone else's usage
/shared/tools/gpumonitor usage john

# Kill your processes (will ask for confirmation)
/shared/tools/gpumonitor kill

# Kill specific user's processes
/shared/tools/gpumonitor kill john --confirm

# See what would be killed (dry run)
/shared/tools/gpumonitor kill john --dry-run

# Show help
/shared/tools/gpumonitor --help
```

### Option 2: Bash Scripts (Older Systems)
**Requirements:** Bash 4.0+ (works on any Unix/Linux, even very old systems)

```bash
# Check GPU status on all servers
/shared/tools/gpu_status.sh

# Check your GPU usage
/shared/tools/gpu_usage.sh

# Check someone else's usage
/shared/tools/gpu_usage.sh john

# Kill your processes (will ask for confirmation)
/shared/tools/gpu_kill.sh

# Kill specific user's processes
/shared/tools/gpu_kill.sh john --confirm

# See what would be killed (dry run)
/shared/tools/gpu_kill.sh john --dry-run
```

## ❓ Troubleshooting

**"I don't see the Ports panel"**
- Try Option B (VS Code Task) or ask admin for help

**"Port forwarding failed"**  
- Make sure you're connected via Remote-SSH
- Ask admin if the server is running

**"MCP server not responding"**
- Check that `http://127.0.0.1:8700` opens in your browser
- If not, port forwarding isn't working

**"Command not found: /shared/tools/gpumonitor"**
- Ask admin to deploy the script to shared location
- Or copy it yourself: `cp src/gpu_monitor/gpumonitor /shared/tools/gpumonitor`
- For older systems: `cp src/gpu_monitor/scripts/*.sh /shared/tools/`

## 🔧 Admin Contact

If something isn't working:
1. Try the command line backup method
2. Check with your admin that the server is running
3. Verify your Remote-SSH connection is working

---

*That's it! You should now be able to monitor GPUs through Copilot or command line.*
