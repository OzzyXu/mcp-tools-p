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

## 🔧 MCP Tool Functions (Direct Function Calls)

MCP tool functions provide direct access to GPU monitoring capabilities. These are called automatically when you ask Copilot certain questions, but you can also invoke them explicitly.

### 📋 Available Tool Functions

#### 1. **`check_gpu_status`** - Get Server Status
```
# Check all servers
"Use check_gpu_status tool"

# Check specific server  
"Use check_gpu_status tool with server_id=gpu01"

# What this returns:
{
  "servers": {
    "gpu01": {
      "online": true,
      "gpus": [...], 
      "total_memory_gb": 80,
      "free_memory_gb": 45
    }
  }
}
```

#### 2. **`check_user_usage`** - Get User's GPU Usage
```
# Check your own usage (auto-detects $USER)
"Use check_user_usage tool"

# Check specific user on all servers
"Use check_user_usage tool with username=john"

# Check specific user on specific server
"Use check_user_usage tool with username=john and server_id=gpu01"

# What this returns:
{
  "username": "john",
  "total_processes": 3,
  "total_memory_used_gb": 24,
  "servers": {
    "gpu01": {
      "processes": [...],
      "memory_used_gb": 24
    }
  }
}
```

#### 3. **`kill_user_tasks`** - Terminate GPU Processes
```
# Kill your own processes (auto-detects $USER)
"Use kill_user_tasks tool with confirm=true"

# Kill specific user's processes on all servers
"Use kill_user_tasks tool with username=john and confirm=true"

# Kill processes on specific server only
"Use kill_user_tasks tool with username=john, server_id=gpu01, and confirm=true"

# ⚠️ IMPORTANT: Must set confirm=true to actually kill processes
# Without confirm=true, it only shows what would be killed (dry run)
```

### 💡 How Tool Functions Work

#### **Automatic Invocation:**
When you ask natural language questions, Copilot automatically chooses the right tool:

```
You: "Show me GPU status on gpu01"
→ Copilot calls: check_gpu_status(server_id="gpu01")
→ Returns formatted status information

You: "What's john's GPU usage?"  
→ Copilot calls: check_user_usage(username="john")
→ Returns john's usage across all servers

You: "Kill all my processes on gpu02"
→ Copilot calls: kill_user_tasks(server_id="gpu02", confirm=true)
→ Terminates your processes on gpu02
```

#### **Explicit Invocation:**
You can also call tools directly for precise control:

```
"Use the check_gpu_status tool to get status for gpu01"
"Call check_user_usage with username alice"
"Invoke kill_user_tasks for user bob on gpu03 with confirm true"
```

### 🎯 Tool Function Examples

#### **Example 1: Resource Planning**
```
You: "Use check_gpu_status tool to see which servers have the most free memory"

Copilot:
1. Calls check_gpu_status() 
2. Gets data for all servers
3. Analyzes memory availability
4. Responds: "gpu02 has 78GB free (most available), gpu01 has 45GB free, gpu03 is busy with only 12GB free"
```

#### **Example 2: User Monitoring**
```
You: "Use check_user_usage tool with username=alice to see her current workload"

Copilot:
1. Calls check_user_usage(username="alice")
2. Gets alice's processes across all servers  
3. Responds: "Alice is using 32GB GPU memory across 2 servers: 24GB on gpu01 (training job) and 8GB on gpu03 (inference)"
```

#### **Example 3: Process Management**
```
You: "Use kill_user_tasks tool with username=bob, server_id=gpu01, confirm=true"

Copilot:
1. Calls kill_user_tasks(username="bob", server_id="gpu01", confirm=true)
2. Terminates bob's processes on gpu01
3. Responds: "✅ Killed 2 processes for user bob on gpu01. Freed 16GB GPU memory."
```

### 🔒 Safety Features

#### **Automatic User Detection:**
- **Username defaults to $USER**: Tools auto-detect your username
- **No accidental kills**: Must specify `confirm=true` for kill operations
- **Dry run by default**: `kill_user_tasks` shows what would be killed unless confirmed

#### **Scope Control:**
- **Server-specific**: Can limit operations to specific servers
- **User-specific**: Can check/kill only specific user's processes
- **Confirmation required**: Destructive operations need explicit confirmation

### 🚀 Advanced Usage Patterns

#### **Combining Tools with Prompts:**
```
You: "Use check_gpu_status, then analyze_user_usage prompt to recommend the best server for my training job"

Copilot:
1. Calls check_gpu_status() to get current cluster state
2. Uses summarize_gpu_availability prompt with the data
3. Provides intelligent recommendation based on current usage
```

#### **Monitoring Workflows:**
```
You: "Use check_user_usage for alice, bob, and charlie, then tell me who's using resources most efficiently"

Copilot:
1. Calls check_user_usage() for each user
2. Compares their resource utilization patterns
3. Provides efficiency analysis and recommendations
```

#### **Troubleshooting:**
```
You: "gpu01 seems slow. Use check_gpu_status for gpu01 and check who's using it heavily"

Copilot:
1. Calls check_gpu_status(server_id="gpu01")
2. Analyzes utilization and identifies heavy users
3. Suggests actions to resolve performance issues
```

### 📊 Tool Output Format

All tools return structured JSON data that Copilot can interpret and present in natural language. You can also ask for raw data:

```
"Use check_gpu_status tool and show me the raw JSON response"
"Call check_user_usage and format the output as a table"
"Use kill_user_tasks with dry run and list exactly what processes would be killed"
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
