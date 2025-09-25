# GPU Monitor

Monitor your GPU cluster usage directly from VSCode or command line.

## 🚀 What This Does

Ask questions like:
- **"Which GPU server is free?"** 
- **"Show my current GPU usage"**
- **"Kill all my processes on gpu01"**

Get answers instantly in VSCode Copilot or run commands directly.

## 📋 Two Ways to Use This

### 1. 💬 **VSCode Copilot (Recommended)**
Talk to your GPUs in natural language through Copilot.

### 2. 🛠️ **Command Line (Always Works)**  
Direct commands that work even when servers are down.

---

## 💬 VSCode Copilot Setup

### Step 1: Connect to Server
The admin has set up a GPU monitor server. Connect using **one of these methods**:

#### Option A: Use Ports Panel (Remote-SSH)
1. Connect to the server via **Remote-SSH**
2. Open **Ports view**: `Ctrl+Shift+P` → "Ports: Focus on Ports View"
3. Click **"Add Port"** → Enter `8700`
4. Now `http://127.0.0.1:8700` works on your local machine

#### Option B: Use VS Code Task (One-Click)
1. Open Command Palette: `Ctrl+Shift+P`
2. Run: **"Tasks: Run Task"** → **"Forward GPU Monitor Port"**
3. Port is automatically forwarded

### Step 2: Add MCP Configuration
Add this to your VSCode MCP settings:

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

### Step 3: Ask Copilot Questions
```
"Which GPU server has the most free memory?"
"Show my current GPU usage" 
"Kill all my processes on gpu01"
```

---

## 🛠️ Command Line Usage (Always Available)

Use this when VSCode isn't working or you prefer command line:

### Python Script (Recommended)
**Requirements:** Python 3.8+ (standard on most systems)

```bash
# Check all GPU servers
/shared/tools/gpumonitor status

# Check specific user's usage  
/shared/tools/gpumonitor usage john

# Kill user's processes (with confirmation)
/shared/tools/gpumonitor kill john --confirm

# Show help
/shared/tools/gpumonitor --help
```

### Bash Scripts (Older Systems)
**Requirements:** Bash 4.0+ (2009, works on any Unix/Linux)

```bash
# Check all GPU servers
/shared/tools/gpu_status.sh

# Check specific user's usage  
/shared/tools/gpu_usage.sh john

# Kill user's processes (with confirmation)
/shared/tools/gpu_kill.sh john --confirm
```

## ❓ Common Questions

**Q: "I don't see the Ports panel"**  
A: Use Option B (VS Code Task) or ask your admin to share the task file.

**Q: "The server is down"**  
A: Use the command line: `/shared/tools/gpumonitor status`

**Q: "How do I kill only my processes?"**  
A: Ask Copilot: "Kill all my processes" or use: `/shared/tools/gpumonitor kill`

**Q: "Can I check someone else's usage?"**  
A: Yes: `/shared/tools/gpumonitor usage username` or ask Copilot: "Show john's GPU usage"

**Q: "My server doesn't have Python 3.8+"**  
A: Use the bash scripts: `/shared/tools/gpu_status.sh` - works on any Unix/Linux system

---

## 👨‍💻 For Admins

- **[Setup Guide](docs/deployment.md)** - How to deploy this for your team
- **[Configuration](docs/configuration.md)** - Server settings and options
- **[Bash Scripts](src/gpu_monitor/bash_scripts/README.md)** - For older systems without Python 3.8+
- **Config file**: `src/gpu_monitor/servers.json` - Edit with your cluster details
