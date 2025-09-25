#!/bin/bash
# GPU Process Killer - Bash Version
# Kill GPU processes for a specific user
# Usage: ./gpu_kill.sh [username] [server_id] [--confirm]

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

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_usage() {
    echo "Usage: $0 [username] [server_id] [--confirm|--dry-run]"
    echo "Examples:"
    echo "  $0                         # Check what would be killed for \$USER"
    echo "  $0 john                    # Check what would be killed for john"
    echo "  $0 john --confirm          # Kill john's processes on all servers"
    echo "  $0 john python2-gpu1 --confirm    # Kill john's processes on python2-gpu1"
    echo "  $0 john --dry-run          # Show what would be killed (same as no --confirm)"
    echo ""
    echo "Available servers:"
    for server in "${SERVERS[@]}"; do
        server_id="${server%:*}"
        echo "  - $server_id"
    done
}

get_user_pids() {
    local username="$1"
    local server_id="$2"
    local hostname="$3"
    
    # Get GPU processes and extract PIDs
    local pids
    pids=$(timeout $SSH_TIMEOUT ssh -o ConnectTimeout=$SSH_TIMEOUT -o BatchMode=yes "$hostname" \
        "nvidia-smi pmon -c 1 2>/dev/null | grep -E '^[[:space:]]*[0-9]+[[:space:]]+$username' | awk '{print \$2}' 2>/dev/null" 2>/dev/null)
    
    echo "$pids"
}

show_processes_to_kill() {
    local username="$1"
    local target_server="$2"
    
    echo "=== Processes to kill for $username ==="
    echo
    
    local total_processes=0
    local servers_with_processes=()
    local all_pids=()
    
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
        
        # Get process details for display
        local process_output
        process_output=$(timeout $SSH_TIMEOUT ssh -o ConnectTimeout=$SSH_TIMEOUT -o BatchMode=yes "$hostname" \
            "nvidia-smi pmon -c 1 2>/dev/null | grep -E '^[[:space:]]*[0-9]+[[:space:]]+$username' 2>/dev/null" 2>/dev/null)
        
        if [ -n "$process_output" ]; then
            echo -e "${YELLOW}$server_id${NC}:"
            local process_count=0
            local server_pids=()
            
            while read -r line; do
                if [ -z "$line" ]; then continue; fi
                
                # Parse nvidia-smi pmon output
                local gpu_id pid type sm mem enc dec command
                read -r gpu_id pid type sm mem enc dec command <<< "$line"
                
                # Skip invalid lines
                if [[ ! "$gpu_id" =~ ^[0-9]+$ ]] || [[ ! "$pid" =~ ^[0-9]+$ ]]; then
                    continue
                fi
                
                echo "  GPU$gpu_id: PID $pid - $command"
                process_count=$((process_count + 1))
                server_pids+=("$pid")
                all_pids+=("$server_id:$pid")
            done <<< "$process_output"
            
            if [ $process_count -gt 0 ]; then
                echo "  Processes to kill: $process_count"
                servers_with_processes+=("$server_id")
                total_processes=$((total_processes + process_count))
            fi
            echo
        fi
    done
    
    echo "Summary:"
    echo "  User: $username"
    echo "  Total processes to kill: $total_processes"
    echo "  Servers affected: ${#servers_with_processes[@]}"
    
    # Return the total count for the caller
    return $total_processes
}

kill_user_processes() {
    local username="$1"
    local target_server="$2"
    
    echo "=== Killing processes for $username ==="
    echo
    
    local total_killed=0
    local success_count=0
    local fail_count=0
    
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
            fail_count=$((fail_count + 1))
            continue
        fi
        
        # Get PIDs to kill
        local pids
        pids=$(get_user_pids "$username" "$server_id" "$hostname")
        
        if [ -z "$pids" ]; then
            continue  # No processes to kill on this server
        fi
        
        # Convert PIDs to array and kill them
        local pid_array=($pids)
        local kill_count=0
        
        echo "Killing ${#pid_array[@]} processes on $server_id..."
        
        # Kill all PIDs at once
        local kill_cmd="kill -9 ${pid_array[*]}"
        if timeout $SSH_TIMEOUT ssh -o ConnectTimeout=$SSH_TIMEOUT -o BatchMode=yes "$hostname" "$kill_cmd" >/dev/null 2>&1; then
            kill_count=${#pid_array[@]}
            echo -e "${GREEN}✓ $server_id - Killed $kill_count processes${NC}"
            success_count=$((success_count + 1))
        else
            echo -e "${RED}✗ $server_id - Failed to kill processes${NC}"
            fail_count=$((fail_count + 1))
        fi
        
        total_killed=$((total_killed + kill_count))
    done
    
    echo
    echo "Results:"
    echo "  Total processes killed: $total_killed"
    echo "  Successful servers: $success_count"
    echo "  Failed servers: $fail_count"
}

main() {
    local username=""
    local target_server=""
    local confirm=0
    local dry_run=0
    
    # Parse arguments
    while [ $# -gt 0 ]; do
        case "$1" in
            -h|--help)
                print_usage
                exit 0
                ;;
            --confirm)
                confirm=1
                ;;
            --dry-run)
                dry_run=1
                ;;
            *)
                if [ -z "$username" ]; then
                    username="$1"
                elif [ -z "$target_server" ]; then
                    target_server="$1"
                else
                    echo "Error: Too many arguments"
                    print_usage
                    exit 1
                fi
                ;;
        esac
        shift
    done
    
    # Use current user if none specified
    if [ -z "$username" ]; then
        username="$USER"
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
    
    # First, show what would be killed
    show_processes_to_kill "$username" "$target_server"
    local process_count=$?
    
    if [ $process_count -eq 0 ]; then
        echo -e "${YELLOW}No GPU processes found for $username.${NC}"
        exit 0
    fi
    
    echo
    
    # If dry run or no confirmation, just show what would be killed
    if [ $dry_run -eq 1 ]; then
        echo -e "${YELLOW}Dry run - no processes were actually killed.${NC}"
        exit 0
    fi
    
    if [ $confirm -eq 0 ]; then
        echo -e "${YELLOW}⚠️  Use --confirm to actually kill these processes${NC}"
        echo "Example: $0 $username${target_server:+ $target_server} --confirm"
        exit 0
    fi
    
    # Confirm with user
    echo -e "${RED}⚠️  WARNING: About to kill $process_count processes for $username${NC}"
    read -p "Type 'YES' to confirm: " response
    
    if [ "$response" != "YES" ]; then
        echo "Operation cancelled."
        exit 0
    fi
    
    # Actually kill the processes
    kill_user_processes "$username" "$target_server"
}

main "$@"
