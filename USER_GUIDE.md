# GPU Monitor - User Guide

Quick setup guide for team members.

## 🚀 What You Get

Ask your GPUs questions in plain English:
- **"Which GPU server is free?"**
- **"Show my current GPU usage"** 
- **"Kill all my processes on gpu01"**

## 💬 VSCode Setup (Recommended)

### Step 1: Connect to GPU Server

**Option A - Ports Panel:**
1. Connect via Remote-SSH to your server
2. Open Command Palette: `Ctrl+Shift+P`
3. Type: **"Ports: Focus on Ports View"**
4. Click **"Add Port"** → Enter `11694`

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
      "url": "http://10.126.6.227:11694" 
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

## 🤖 Advanced: Using MCP Resources and Prompts

Once you have the MCP server configured, you can use advanced features for more detailed analysis.

### 📊 MCP Resources (Direct Data Access)

MCP resources provide direct access to GPU data that you can reference in your questions:

#### Available Resources:
- `gpu://status` - All server status data
- `gpu://status/gpu01` - Specific server status
- `gpu://usage/john` - User's usage across all servers  
- `gpu://usage/john/gpu01` - User's usage on specific server

#### How to Use Resources:
```
# Reference specific server data
"@gpu://status/gpu01 Is this server suitable for a large training job?"

# Compare multiple servers
"@gpu://status Compare gpu01 and gpu02 memory availability"

# Analyze user patterns
"@gpu://usage/john How efficiently is john using GPU resources?"
```

### 🎯 MCP Prompts (Smart Analysis)

MCP prompts provide intelligent analysis of your GPU data with specialized formatting:

#### 1. **GPU Availability Summary**
```
# Ask Copilot to use the summarize_gpu_availability prompt
"Summarize current GPU availability for job placement"

# This automatically calls the prompt with current cluster data
# Returns: "🟢 gpu02: 90% free (78GB), 🟡 gpu01: 60% free (45GB)..."
```

#### 2. **User Usage Analysis**  
```
# Get detailed usage analysis
"Analyze my GPU usage patterns and suggest optimizations"

# For specific users
"Analyze john's GPU usage - is he using resources efficiently?"

# This calls analyze_user_usage prompt with user data
```

#### 3. **Process Kill Confirmation**
```
# When killing processes, get formatted confirmation
"I want to kill all my processes on gpu01"

# Copilot uses format_kill_confirmation prompt to show:
# "⚠️ CONFIRM: Kill 3 processes for user on gpu01"
```

### 💡 Practical Examples

#### **Planning a Training Job:**
```
You: "I need to run a large model training that will use 40GB GPU memory. Which server should I use?"

Copilot: 
1. Fetches gpu://status 
2. Uses summarize_gpu_availability prompt
3. Responds: "🟢 gpu02 is best - has 78GB free with only 10% utilization. gpu01 is busy at 85% utilization."
```

#### **Monitoring Resource Usage:**
```
You: "How is my team using GPU resources this week?"

Copilot:
1. Fetches gpu://usage data for team members
2. Uses analyze_user_usage prompt for each
3. Summarizes patterns and efficiency recommendations
```

#### **Troubleshooting Issues:**
```
You: "Why is gpu01 running slowly?"

Copilot:
1. Fetches gpu://status/gpu01
2. Analyzes utilization and memory usage
3. Identifies: "gpu01 is at 95% utilization with 15GB/16GB memory used. High memory pressure may cause slowdowns."
```

### 🔧 Tips for Better Results

#### **Be Specific with Server Names:**
```
✅ Good: "Check gpu01 availability"
❌ Vague: "Check server availability"
```

#### **Reference Users by Name:**
```
✅ Good: "Show john's GPU usage"  
✅ Good: "Compare alice and bob's resource efficiency"
```

#### **Ask for Recommendations:**
```
✅ Good: "Which server is best for a 20GB model?"
✅ Good: "Should I kill my processes on gpu02?"
```

#### **Use Time Context:**
```
✅ Good: "Show current GPU status"
✅ Good: "Which server is free right now?"
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
- Check that `http://10.126.6.227:11694` opens in your browser
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
