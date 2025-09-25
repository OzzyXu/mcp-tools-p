#!/bin/bash
# GPU Status Checker - Bash Version
# Compatible with any system that has bash and ssh
# Usage: ./gpu_status.sh [server_id]

# Configuration - Edit these for your cluster
SERVERS=(
    "python2-gpu1:python2-gpu1.ard-gpu1.hpos.rnd.sas.com"
    "python2-gpu2:python2-gpu2.ard-gpu1.hpos.rnd.sas.com"
    "python2-gpu3:python2-gpu3.ard-gpu1.hpos.rnd.sas.com"
    "python2-gpu4:python2-gpu4.ard-gpu1.hpos.rnd.sas.com"
    "python2-gpu5:python2-gpu5.ard-gpu1.hpos.rnd.sas.com"
    "python2-gpu6:python2-gpu6.ard-gpu1.hpos.rnd.sas.com"
    "python2-gpu7:python2-gpu7.ard-gpu1.hpos.rnd.sas.com"
)

SSH_TIMEOUT=5

# Colors for output (optional, works on most terminals)
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_usage() {
    echo "Usage: $0 [server_id]"
    echo "Examples:"
    echo "  $0           # Check all servers"
    echo "  $0 python2-gpu1     # Check specific server"
    echo ""
    echo "Available servers:"
    for server in "${SERVERS[@]}"; do
        server_id="${server%:*}"
        echo "  - $server_id"
    done
}

get_gpu_status() {
    local server_id="$1"
    local hostname="$2"
    
    echo "Checking $server_id ($hostname)..."
    
    # Test SSH connectivity first
    if ! timeout $SSH_TIMEOUT ssh -o ConnectTimeout=$SSH_TIMEOUT -o BatchMode=yes "$hostname" "echo 'SSH OK'" >/dev/null 2>&1; then
        echo -e "${RED}✗ $server_id - SSH connection failed${NC}"
        return 1
    fi
    
    # Get GPU status
    local gpu_output
    gpu_output=$(timeout $SSH_TIMEOUT ssh -o ConnectTimeout=$SSH_TIMEOUT -o BatchMode=yes "$hostname" \
        "nvidia-smi --query-gpu=index,name,utilization.gpu,memory.used,memory.total,temperature.gpu --format=csv,noheader,nounits 2>/dev/null" 2>/dev/null)
    
    if [ $? -ne 0 ] || [ -z "$gpu_output" ]; then
        echo -e "${RED}✗ $server_id - nvidia-smi failed or no GPUs found${NC}"
        return 1
    fi
    
    echo -e "${GREEN}✓ $server_id - Online${NC}"
    
    # Parse and display GPU info
    local gpu_count=0
    while IFS=, read -r index name util mem_used mem_total temp; do
        # Clean up whitespace
        index=$(echo "$index" | tr -d ' ')
        name=$(echo "$name" | tr -d ' ')
        util=$(echo "$util" | tr -d ' ')
        mem_used=$(echo "$mem_used" | tr -d ' ')
        mem_total=$(echo "$mem_total" | tr -d ' ')
        temp=$(echo "$temp" | tr -d ' ')
        
        # Calculate free memory
        local mem_free=$((mem_total - mem_used))
        local mem_used_gb=$((mem_used / 1024))
        local mem_total_gb=$((mem_total / 1024))
        local mem_free_gb=$((mem_free / 1024))
        
        # Choose color based on utilization
        local color="$GREEN"
        if [ "$util" -gt 70 ]; then
            color="$RED"
        elif [ "$util" -gt 30 ]; then
            color="$YELLOW"
        fi
        
        echo -e "  ${color}GPU$index${NC}: $util% util, ${mem_free_gb}GB/${mem_total_gb}GB free"
        gpu_count=$((gpu_count + 1))
    done <<< "$gpu_output"
    
    echo "  Total GPUs: $gpu_count"
    echo
}

main() {
    local target_server="$1"
    
    if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
        print_usage
        exit 0
    fi
    
    echo "=== GPU Status Check ==="
    echo "Timeout: ${SSH_TIMEOUT}s"
    echo
    
    local found=0
    
    for server in "${SERVERS[@]}"; do
        server_id="${server%:*}"
        hostname="${server#*:}"
        
        # If specific server requested, only check that one
        if [ -n "$target_server" ] && [ "$server_id" != "$target_server" ]; then
            continue
        fi
        
        get_gpu_status "$server_id" "$hostname"
        found=1
    done
    
    if [ -n "$target_server" ] && [ $found -eq 0 ]; then
        echo "Error: Server '$target_server' not found"
        echo
        print_usage
        exit 1
    fi
}

main "$@"
