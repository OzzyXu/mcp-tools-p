#!/bin/bash
# GPU Usage Checker - Bash Version
# Check GPU usage for a specific user
# Usage: ./gpu_usage.sh [username] [server_id]

# Configuration - Edit these for your cluster
SERVERS=(
    "gpu01:gpu01.cluster.local"
    "gpu02:gpu02.cluster.local"
    "gpu03:gpu03.cluster.local"
)

SSH_TIMEOUT=5

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_usage() {
    echo "Usage: $0 [username] [server_id]"
    echo "Examples:"
    echo "  $0                    # Check your usage (\$USER)"
    echo "  $0 john               # Check john's usage on all servers"
    echo "  $0 john gpu01         # Check john's usage on gpu01"
    echo ""
    echo "Available servers:"
    for server in "${SERVERS[@]}"; do
        server_id="${server%:*}"
        echo "  - $server_id"
    done
}

get_user_processes() {
    local username="$1"
    local server_id="$2"
    local hostname="$3"
    
    # Get GPU processes
    local process_output
    process_output=$(timeout $SSH_TIMEOUT ssh -o ConnectTimeout=$SSH_TIMEOUT -o BatchMode=yes "$hostname" \
        "nvidia-smi pmon -c 1 2>/dev/null | grep -E '^[[:space:]]*[0-9]+[[:space:]]+$username' 2>/dev/null" 2>/dev/null)
    
    if [ -z "$process_output" ]; then
        return 0  # No processes found (not an error)
    fi
    
    echo -e "${GREEN}$server_id${NC}:"
    local process_count=0
    local total_memory=0
    
    while read -r line; do
        if [ -z "$line" ]; then continue; fi
        
        # Parse nvidia-smi pmon output: gpu_id pid type sm mem enc dec command
        local gpu_id pid type sm mem enc dec command
        read -r gpu_id pid type sm mem enc dec command <<< "$line"
        
        # Skip header lines or invalid lines
        if [[ ! "$gpu_id" =~ ^[0-9]+$ ]] || [[ ! "$pid" =~ ^[0-9]+$ ]]; then
            continue
        fi
        
        # Get memory usage in MB
        if [[ "$mem" =~ ^[0-9]+$ ]]; then
            total_memory=$((total_memory + mem))
        fi
        
        echo "  GPU$gpu_id: PID $pid, ${mem}MB - $command"
        process_count=$((process_count + 1))
    done <<< "$process_output"
    
    if [ $process_count -gt 0 ]; then
        local memory_gb=$((total_memory / 1024))
        echo "  Total: $process_count processes, ${memory_gb}GB memory"
    fi
    echo
    
    return $process_count
}

check_user_usage() {
    local username="$1"
    local target_server="$2"
    
    echo "=== GPU Usage for $username ==="
    echo
    
    local total_processes=0
    local servers_with_usage=0
    
    for server in "${SERVERS[@]}"; do
        server_id="${server%:*}"
        hostname="${server#*:}"
        
        # If specific server requested, only check that one
        if [ -n "$target_server" ] && [ "$server_id" != "$target_server" ]; then
            continue
        fi
        
        # Test SSH connectivity first
        if ! timeout $SSH_TIMEOUT ssh -o ConnectTimeout=$SSH_TIMEOUT -o BatchMode=yes "$hostname" "echo 'SSH OK'" >/dev/null 2>&1; then
            echo -e "${RED}✗ $server_id - SSH connection failed${NC}"
            continue
        fi
        
        get_user_processes "$username" "$server_id" "$hostname"
        local process_count=$?
        
        if [ $process_count -gt 0 ]; then
            total_processes=$((total_processes + process_count))
            servers_with_usage=$((servers_with_usage + 1))
        fi
    done
    
    echo "Summary:"
    echo "  User: $username"
    echo "  Total processes: $total_processes"
    echo "  Servers with usage: $servers_with_usage"
    
    if [ $total_processes -eq 0 ]; then
        echo -e "${YELLOW}  No GPU processes found for $username${NC}"
    fi
}

main() {
    local username="${1:-$USER}"
    local target_server="$2"
    
    if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
        print_usage
        exit 0
    fi
    
    if [ -z "$username" ]; then
        echo "Error: Could not determine username. Please specify one."
        print_usage
        exit 1
    fi
    
    # Validate server if specified
    if [ -n "$target_server" ]; then
        local found=0
        for server in "${SERVERS[@]}"; do
            server_id="${server%:*}"
            if [ "$server_id" = "$target_server" ]; then
                found=1
                break
            fi
        done
        
        if [ $found -eq 0 ]; then
            echo "Error: Server '$target_server' not found"
            echo
            print_usage
            exit 1
        fi
    fi
    
    check_user_usage "$username" "$target_server"
}

main "$@"
