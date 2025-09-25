# 🚀 GPU Monitor - Quick Setup Card

## VSCode Copilot (5 minutes)

### 1. Forward Port
- `Ctrl+Shift+P` → **"Ports: Focus on Ports View"**
- **Add Port** → `8700`

### 2. Add MCP Config
```json
{
  "servers": {
    "gpu-mcp": { "type": "http", "url": "http://127.0.0.1:8700" }
  }
}
```

### 3. Ask Copilot
```
"Which GPU server is free?"
"Show my GPU usage"
"Kill my processes on gpu01"
```

**💡 Advanced:** Use `@gpu://status` for direct data access or ask for "GPU availability summary" to trigger smart analysis prompts. See [detailed examples](USER_GUIDE.md#advanced-using-mcp-resources-and-prompts).

---

## Command Line (Instant)

### Python (Recommended)
**Requirements:** Python 3.8+

```bash
/shared/tools/gpumonitor status    # Check all GPUs
/shared/tools/gpumonitor usage     # Your usage  
/shared/tools/gpumonitor kill      # Kill your processes
```

### Bash (Older Systems)
**Requirements:** Bash 4.0+

```bash
/shared/tools/gpu_status.sh       # Check all GPUs
/shared/tools/gpu_usage.sh        # Your usage
/shared/tools/gpu_kill.sh         # Kill your processes
```

---

**Need help?** See [USER_GUIDE.md](USER_GUIDE.md) or ask your admin.
