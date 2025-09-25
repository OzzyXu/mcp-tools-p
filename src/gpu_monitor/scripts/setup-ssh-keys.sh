#!/usr/bin/env bash
# SSH Key Setup Script for GPU Monitor Service
# This script sets up SSH keys for the gpu-monitor service user to access all GPU nodes

set -euo pipefail

# Configuration
KEY="${HOME}/.ssh/id_ed25519.pub"
servers=(gpu01 gpu02 gpu03 gpu04 gpu05 gpu06 gpu07)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as gpu-monitor user
if [[ "${USER}" != "gpu-monitor" ]]; then
    print_error "This script must be run as the gpu-monitor user"
    print_error "Run: sudo -u gpu-monitor $0"
    exit 1
fi

# Check if SSH key exists
if [[ ! -f "${KEY}" ]]; then
    print_error "SSH public key not found: ${KEY}"
    print_error "Generate it first with: ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519 -N \"\""
    exit 1
fi

print_status "Setting up SSH keys for GPU Monitor service"
print_status "Public key: ${KEY}"
print_status "Target servers: ${servers[*]}"

# Copy SSH key to all servers
failed_servers=()
successful_servers=()

for server in "${servers[@]}"; do
    hostname="python2-${server}.ard-gpu1.hpos.rnd.sas.com"
    print_status "Setting up SSH for ${server} (${hostname})"
    
    if ssh-copy-id \
        -i "$KEY" \
        -o StrictHostKeyChecking=accept-new \
        -o ConnectTimeout=10 \
        "monitor@${hostname}" 2>/dev/null; then
        print_status "✅ SSH key copied to ${server}"
        successful_servers+=("${server}")
    else
        print_error "❌ Failed to copy SSH key to ${server}"
        failed_servers+=("${server}")
    fi
done

# Test connectivity
print_status "Testing SSH connectivity..."
for server in "${successful_servers[@]}"; do
    hostname="python2-${server}.ard-gpu1.hpos.rnd.sas.com"
    if ssh -o ConnectTimeout=5 -o BatchMode=yes "${hostname}" "nvidia-smi --version" >/dev/null 2>&1; then
        print_status "✅ ${server}: SSH and nvidia-smi working"
    else
        print_warning "⚠️  ${server}: SSH works but nvidia-smi failed (check NVIDIA drivers)"
    fi
done

# Summary
echo
print_status "=== SSH Setup Summary ==="
print_status "Successful: ${#successful_servers[@]} servers"
print_status "Failed: ${#failed_servers[@]} servers"

if [[ ${#failed_servers[@]} -gt 0 ]]; then
    print_warning "Failed servers: ${failed_servers[*]}"
    print_warning "Manual setup may be required for these servers"
fi

if [[ ${#successful_servers[@]} -eq ${#servers[@]} ]]; then
    print_status "🎉 All servers configured successfully!"
    print_status "GPU Monitor service is ready to monitor all nodes"
else
    print_warning "⚠️  Some servers failed. GPU Monitor will work for successful servers only."
fi
