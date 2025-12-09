#!/bin/bash
# Check status of running services

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}   Service Status Check${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo ""

# Check Frontend
echo -e "${YELLOW}Frontend (Vite):${NC}"
FRONTEND_PORT=$(lsof -ti:5173,5001,5002,5003 2>/dev/null | head -1)
if [ -n "$FRONTEND_PORT" ]; then
    ACTUAL_PORT=$(lsof -Pan -p $FRONTEND_PORT -i 2>/dev/null | grep LISTEN | awk '{print $9}' | cut -d: -f2 | head -1)
    if [ -n "$ACTUAL_PORT" ]; then
        echo -e "  ${GREEN}✓ Running on port $ACTUAL_PORT${NC}"
        echo -e "  ${BLUE}  → http://localhost:$ACTUAL_PORT${NC}"
    else
        # Check logs if port detection failed
        LOG_PORT=$(tail -20 logs/frontend.log 2>/dev/null | grep -oP 'Local:\s+http://localhost:\K[0-9]+' | tail -1)
        if [ -n "$LOG_PORT" ]; then
            echo -e "  ${GREEN}✓ Running on port $LOG_PORT${NC}"
            echo -e "  ${BLUE}  → http://localhost:$LOG_PORT${NC}"
        else
            echo -e "  ${YELLOW}⚠ Process found but port unclear - check logs/frontend.log${NC}"
        fi
    fi
else
    echo -e "  ${RED}✗ Not running${NC}"
fi

# Check Backend
echo ""
echo -e "${YELLOW}Backend (FastAPI):${NC}"
if lsof -ti:8000 >/dev/null 2>&1; then
    echo -e "  ${GREEN}✓ Running on port 8000${NC}"
    echo -e "  ${BLUE}  → http://localhost:8000/docs${NC}"
else
    echo -e "  ${RED}✗ Not running${NC}"
fi

# Check MCP Server
echo ""
echo -e "${YELLOW}MCP Server:${NC}"
if lsof -ti:8888 >/dev/null 2>&1; then
    echo -e "  ${GREEN}✓ Running on port 8888${NC}"
    echo -e "  ${BLUE}  → http://localhost:8888/health${NC}"
else
    echo -e "  ${RED}✗ Not running${NC}"
    if [ -f "logs/mcp-server.log" ]; then
        ERROR=$(tail -5 logs/mcp-server.log | grep -i "error\|missing" | tail -1)
        if [ -n "$ERROR" ]; then
            echo -e "  ${YELLOW}  Last error: ${ERROR:0:80}...${NC}"
        fi
    fi
fi

# Quick links
echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}Logs:${NC}"
echo -e "  tail -f logs/frontend.log"
echo -e "  tail -f logs/backend.log"
echo -e "  tail -f logs/mcp-server.log"
echo ""
