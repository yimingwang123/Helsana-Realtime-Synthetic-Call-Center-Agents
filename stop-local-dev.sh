#!/bin/bash
# Stop all local development services

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Stopping local development services...${NC}"

# Default ports
MCP_PORT=${MCP_PORT:-8888}
BACKEND_PORT=${BACKEND_PORT:-8000}
FRONTEND_PORTS="5173 5001 5002 5003"  # Check multiple possible frontend ports

# Function to kill process on port
kill_port() {
    local port=$1
    local name=$2
    
    echo -n "  Stopping $name (port $port)... "
    
    # Find and kill process
    local pids=$(lsof -ti:$port 2>/dev/null)
    
    if [ -z "$pids" ]; then
        echo -e "${YELLOW}not running${NC}"
        return
    fi
    
    for pid in $pids; do
        kill -9 $pid 2>/dev/null
    done
    
    echo -e "${GREEN}✓ stopped${NC}"
}

# Kill services
for port in $FRONTEND_PORTS; do
    kill_port $port "Frontend"
done
kill_port $BACKEND_PORT "Backend"
kill_port $MCP_PORT "MCP Server"

# Clean up PID files if they exist
if [ -d "logs" ]; then
    rm -f logs/*.pid 2>/dev/null
fi

echo ""
echo -e "${GREEN}✓ All services stopped${NC}"
