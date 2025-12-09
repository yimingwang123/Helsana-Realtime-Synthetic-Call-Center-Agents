# Quick Start Guide - Linux/macOS

Complete guide to test the entire Helsana Realtime Call Center Agents application locally on Linux.

## 📋 Prerequisites

### 1. System Requirements
- Python 3.9+
- Node.js 18+ and npm
- Azure CLI (`az` command)
- lsof (for port management)

### 2. Azure Authentication
Login to Azure (required for accessing Azure resources):
```bash
az login
```

Verify you're authenticated:
```bash
az account show
```

### 3. Set up Azure Environment
Load your Azure environment (choose one method):

**Option A: Use azd (recommended)**
```bash
azd env list  # See available environments
azd env set <your-environment-name>
azd env get-values  # Verify it loads
```

**Option B: Copy .env file manually**
```bash
# If you have an .env file from Azure deployment
cp .azure/<your-env>/.env src/backend/.env
cp .azure/<your-env>/.env src/mcp-servers/ai-foundry-agent/.env
```

**Option C: Set environment variables manually**
```bash
export AZURE_OPENAI_ENDPOINT="https://<your-resource>.openai.azure.com"
export AZURE_OPENAI_DEPLOYMENT="gpt-4o-realtime-preview"
export AZURE_AI_PROJECT_CONNECTION_STRING="<your-connection-string>"
export AZURE_COSMOS_ENDPOINT="https://<your-cosmos>.documents.azure.com:443/"
export AZURE_SEARCH_ENDPOINT="https://<your-search>.search.windows.net"
export AZURE_SEARCH_INDEX="<your-index-name>"
# ... etc
```

## 🚀 Installation

### Step 1: Create Python Virtual Environments

**Backend:**
```bash
cd src/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
deactivate
cd ../..
```

**MCP Server:**
```bash
cd src/mcp-servers/ai-foundry-agent
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
deactivate
cd ../../..
```

### Step 2: Install Frontend Dependencies
```bash
cd src/frontend
npm install
cd ../..
```

## 🎯 Running the Application

### Quick Start (All Services)
```bash
./start-local-dev.sh
```

This will open 3 terminal windows:
1. **MCP Server** - Port 8888
2. **Backend API** - Port 8000
3. **Frontend** - Port 5173

### Custom Ports
```bash
MCP_PORT=9000 BACKEND_PORT=8001 FRONTEND_PORT=3000 ./start-local-dev.sh
```

### Manual Start (Alternative)

If the script doesn't work or you prefer manual control:

**Terminal 1 - MCP Server:**
```bash
cd src/mcp-servers/ai-foundry-agent
source .venv/bin/activate
export PORT=8888
python3 -m mcp_agent_router
```

**Terminal 2 - Backend API:**
```bash
cd src/backend
source .venv/bin/activate
export AZURE_AI_FOUNDRY_MCP_URL=http://localhost:8888
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 3 - Frontend:**
```bash
cd src/frontend
npm run dev -- --port 5173
```

## 🧪 Testing the Application

### 1. Access the Application
Open your browser: **http://localhost:5173**

### 2. Test Basic Functionality
1. Click **"Start Session"** to begin voice chat
2. Grant microphone permissions when prompted
3. You should see "Connected" status

### 3. Test Identity Verification (NEW!)
The AI will perform identity verification BEFORE answering any questions:

**Test Scenario:**
1. AI asks: "Could you please provide your insurance number?"
2. You say: "CH-7671355403813" (example)
3. AI asks: "What is your name?"
4. You say: "Anna Meier"
5. AI asks: "What is your date of birth?"
6. You say: "June 1st, 1962"
7. AI asks: "What is your address?"
8. You say: "Hauptstrasse 10, 3000 Bern"
9. AI may ask security question: "What is your mother's maiden name?"
10. You answer the security question
11. ✅ After verification, AI switches to answering your questions

**Test Customer Data:**
Run the identity integration test to create test customers:
```bash
cd src/backend
source .venv/bin/activate
python3 test_identity_integration.py
```

### 4. Test Multi-Agent Features

**Web Search (Bing grounding):**
- "What's the weather in Zurich?"
- "Who won the world cup?"

**Internal Knowledge Base:**
- "What health insurance plans do you offer?"
- "Tell me about dental coverage"

**Database Operations:**
- "Show me my customer profile"
- "What are my recent transactions?"
- "Update my email address"

**Email Automation:**
- "Send me a summary of my policy"
- "Email me the claim form"

### 5. Check Service Health

**Backend API Docs:**
http://localhost:8000/docs

**MCP Server Health:**
```bash
curl http://localhost:8888/health
```

**Backend WebSocket:**
```bash
curl http://localhost:8000/health
```

## 🔍 Monitoring & Debugging

### Check Logs

**Backend logs:**
- Watch the Backend terminal for API requests, WebSocket connections, and agent interactions

**MCP Server logs:**
- Watch the MCP Server terminal for tool executions and AI Foundry calls

**Frontend console:**
- Open browser DevTools (F12) → Console tab
- Watch for WebSocket messages and errors

### Common Issues

**1. "Port already in use"**
```bash
# Find and kill process
lsof -ti:8000 | xargs kill -9  # Backend
lsof -ti:8888 | xargs kill -9  # MCP
lsof -ti:5173 | xargs kill -9  # Frontend

# Or use stop script
./stop-local-dev.sh
```

**2. "MCP connection error"**
- Ensure MCP server is running: `curl http://localhost:8888/health`
- Check backend environment: `AZURE_AI_FOUNDRY_MCP_URL=http://localhost:8888`

**3. "Azure authentication failed"**
```bash
# Re-login
az login

# Check active subscription
az account show

# Reload environment
azd env get-values
```

**4. "Virtual environment not found"**
- Follow installation steps above to create venvs

**5. "ModuleNotFoundError"**
```bash
# Reinstall dependencies
cd src/backend
source .venv/bin/activate
pip install -r requirements.txt
```

## 🛑 Stopping Services

### Quick Stop (All Services)
```bash
./stop-local-dev.sh
```

### Manual Stop
```bash
# Kill by port
lsof -ti:5173 | xargs kill -9  # Frontend
lsof -ti:8000 | xargs kill -9  # Backend
lsof -ti:8888 | xargs kill -9  # MCP

# Or use Ctrl+C in each terminal
```

## 📊 Service Architecture

```
┌─────────────────┐
│   Browser       │
│  localhost:5173 │
└────────┬────────┘
         │ HTTP/WS
         ▼
┌─────────────────┐
│   Frontend      │  Vite dev server
│   (React/TS)    │  Proxies /api → Backend
└────────┬────────┘
         │ REST/WebSocket
         ▼
┌─────────────────┐
│   Backend       │  FastAPI
│  localhost:8000 │  • Realtime voice (WebSocket)
└────────┬────────┘  • Agent orchestration
         │           • Identity verification
         │ HTTP (JSON-RPC)
         ▼
┌─────────────────┐
│  MCP Server     │  AI Foundry Agent Router
│  localhost:8888 │  • Web search (Bing)
└─────────────────┘  • Document search (AI Search)
         │           • Database ops (Cosmos)
         │           • Email (Logic Apps)
         ▼
┌─────────────────┐
│ Azure Services  │  AI Foundry, Cosmos DB,
│                 │  AI Search, OpenAI, etc.
└─────────────────┘
```

## 🎯 Next Steps

After successful local testing:

1. **Make code changes** - All services auto-reload on file changes
2. **Test identity verification** - Run `python3 test_identity_integration.py`
3. **Debug agents** - Check logs in each terminal window
4. **Deploy to Azure** - Run `azd deploy` when ready

## 📚 Additional Resources

- **Identity Verification**: `docs/IDENTITY_VERIFICATION_INTEGRATION.md`
- **Local Testing Guide**: `docs/LOCAL_TESTING_GUIDE.md`
- **API Documentation**: `src/backend/README_API.md`
- **Windows Setup**: `LOCAL_DEVELOPMENT.md`

---

**Need help?** Check the logs in each terminal window for detailed error messages.

**Happy testing!** 🎉
