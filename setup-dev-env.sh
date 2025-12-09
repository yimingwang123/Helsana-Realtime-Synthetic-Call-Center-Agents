#!/bin/bash
# Setup script for local development environment

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}   Setting Up Development Environment${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo ""

# 1. Backend virtual environment
echo -e "${YELLOW}1. Setting up Backend virtual environment...${NC}"
cd src/backend
if [ -d ".venv" ]; then
    echo -e "${YELLOW}   Removing existing .venv...${NC}"
    rm -rf .venv
fi
python3 -m venv .venv
source .venv/bin/activate
echo -e "${BLUE}   Installing backend dependencies...${NC}"
pip install --upgrade pip
pip install -r requirements.txt
deactivate
echo -e "${GREEN}   ✓ Backend environment ready${NC}"
cd ../..

# 2. MCP Server virtual environment
echo ""
echo -e "${YELLOW}2. Setting up MCP Server virtual environment...${NC}"
cd src/mcp-servers/ai-foundry-agent
if [ -d ".venv" ]; then
    echo -e "${YELLOW}   Removing existing .venv...${NC}"
    rm -rf .venv
fi
python3 -m venv .venv
source .venv/bin/activate
echo -e "${BLUE}   Installing MCP server dependencies...${NC}"
pip install --upgrade pip
pip install -r requirements.txt
deactivate
echo -e "${GREEN}   ✓ MCP Server environment ready${NC}"
cd ../../..

# 3. Frontend dependencies
echo ""
echo -e "${YELLOW}3. Setting up Frontend dependencies...${NC}"
cd src/frontend
if [ ! -d "node_modules" ]; then
    echo -e "${BLUE}   Installing npm packages...${NC}"
    npm install
else
    echo -e "${BLUE}   Updating npm packages...${NC}"
    npm install
fi
echo -e "${GREEN}   ✓ Frontend environment ready${NC}"
cd ../..

# 4. Check Azure CLI
echo ""
echo -e "${YELLOW}4. Checking Azure CLI authentication...${NC}"
if command -v az &> /dev/null; then
    if az account show &> /dev/null; then
        echo -e "${GREEN}   ✓ Azure CLI authenticated${NC}"
        az account show --query "{Subscription:name, TenantId:tenantId}" -o table
    else
        echo -e "${YELLOW}   ⚠ Azure CLI not authenticated${NC}"
        echo -e "${YELLOW}   Run: az login${NC}"
    fi
else
    echo -e "${YELLOW}   ⚠ Azure CLI not installed${NC}"
fi

# Summary
echo ""
echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}   ✓ Development Environment Setup Complete${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo -e "  1. Ensure Azure authentication: ${BLUE}az login${NC}"
echo -e "  2. Set azd environment: ${BLUE}azd env set <your-env>${NC}"
echo -e "  3. Start services: ${BLUE}./start-local-dev.sh${NC}"
echo ""
echo -e "${GREEN}Ready to develop! 🚀${NC}"
