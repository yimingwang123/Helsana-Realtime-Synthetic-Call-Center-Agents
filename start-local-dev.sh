#!/bin/bash
# Local Development Startup Script for Linux/macOS
# Starts MCP Server, Backend API, and Frontend in separate terminals

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default ports
MCP_PORT=${MCP_PORT:-8888}
BACKEND_PORT=${BACKEND_PORT:-8000}
FRONTEND_PORT=${FRONTEND_PORT:-5173}

echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}   Helsana Realtime Call Center Agents - Local Development${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo ""

# Function to check if virtual environment exists
check_venv() {
    local path=$1
    local name=$2
    if [ ! -d "$path/.venv" ]; then
        echo -e "${RED}✗ Virtual environment not found: $path/.venv${NC}"
        echo -e "${YELLOW}  Create it with:${NC}"
        echo -e "    cd $path"
        echo -e "    python3 -m venv .venv"
        echo -e "    source .venv/bin/activate"
        echo -e "    pip install -r requirements.txt"
        return 1
    fi
    return 0
}

# Function to check if node_modules exists
check_node_modules() {
    if [ ! -d "src/frontend/node_modules" ]; then
        echo -e "${RED}✗ node_modules not found: src/frontend/node_modules${NC}"
        echo -e "${YELLOW}  Install with:${NC}"
        echo -e "    cd src/frontend"
        echo -e "    npm install"
        return 1
    fi
    return 0
}

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"
errors=0

if ! check_venv "src/backend" "Backend"; then
    errors=$((errors + 1))
fi

if ! check_venv "src/mcp-servers/ai-foundry-agent" "MCP Server"; then
    errors=$((errors + 1))
fi

if ! check_node_modules; then
    errors=$((errors + 1))
fi

if [ $errors -gt 0 ]; then
    echo -e "${RED}✗ Prerequisites check failed. Fix the errors above and try again.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Prerequisites check passed${NC}"
echo ""

# Function to start service in new terminal
start_service() {
    local name=$1
    local command=$2
    local port=$3
    
    echo -e "${BLUE}Starting $name on port $port...${NC}"
    
    # Try different terminal emulators
    if command -v gnome-terminal &> /dev/null; then
        gnome-terminal -- bash -c "$command; exec bash" &
    elif command -v xterm &> /dev/null; then
        xterm -hold -e "$command" &
    elif command -v konsole &> /dev/null; then
        konsole -e "$command" &
    else
        echo -e "${YELLOW}⚠ No terminal emulator found. Running in background...${NC}"
        eval "$command" > "logs/${name,,}.log" 2>&1 &
        echo $! > "logs/${name,,}.pid"
    fi
    
    sleep 2
}

# Create logs directory
mkdir -p logs

# Start services
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}   Starting Services${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo ""

# 1. Start MCP Server
start_service "MCP-Server" \
    "cd src/mcp-servers/ai-foundry-agent && source .venv/bin/activate && export PORT=$MCP_PORT && echo 'Starting MCP Server on port $MCP_PORT...' && python3 main.py" \
    "$MCP_PORT"

# 2. Start Backend
start_service "Backend" \
    "cd src/backend && source .venv/bin/activate && export AZURE_AI_FOUNDRY_MCP_URL=http://localhost:$MCP_PORT && echo 'Starting Backend API on port $BACKEND_PORT...' && uvicorn main:app --reload --host 0.0.0.0 --port $BACKEND_PORT" \
    "$BACKEND_PORT"

# 3. Start Frontend
start_service "Frontend" \
    "cd src/frontend && echo 'Starting Frontend on port $FRONTEND_PORT...' && npm run dev -- --port $FRONTEND_PORT" \
    "$FRONTEND_PORT"

# Summary
echo ""
echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}   ✓ All Services Started${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}Service URLs:${NC}"
echo -e "  🌐 Frontend:    ${BLUE}Check logs/frontend.log for actual port${NC}"
echo -e "                  (Vite may use 5001, 5002, etc. if ports are busy)"
echo -e "  🔧 Backend API: ${BLUE}http://localhost:$BACKEND_PORT/docs${NC}"
echo -e "  🤖 MCP Server:  ${BLUE}http://localhost:$MCP_PORT/health${NC}"
echo -e "                  (Needs Azure AI Foundry env vars to start)"
echo ""
echo -e "${YELLOW}Find Frontend Port:${NC}"
echo -e "  ${BLUE}tail logs/frontend.log | grep 'Local:'${NC}"
echo ""
echo -e "${YELLOW}Testing:${NC}"
echo -e "  1. Check frontend port: ${BLUE}tail logs/frontend.log | grep Local${NC}"
echo -e "  2. Open browser to that URL"
echo -e "  3. Click 'Start Session' to begin voice chat"
echo -e "  4. Test identity verification (customer must verify first)"
echo ""
echo -e "${YELLOW}View Logs:${NC}"
echo -e "  Frontend: ${BLUE}tail -f logs/frontend.log${NC}"
echo -e "  Backend:  ${BLUE}tail -f logs/backend.log${NC}"
echo -e "  MCP:      ${BLUE}tail -f logs/mcp-server.log${NC}"
echo ""
echo -e "${YELLOW}Stop Services:${NC}"
echo -e "  Run: ${BLUE}./stop-local-dev.sh${NC}"
echo ""
echo -e "${GREEN}Happy coding! 🎉${NC}"
