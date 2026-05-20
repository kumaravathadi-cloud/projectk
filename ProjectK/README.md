# ProjectK - AI Call Screening Backend

Minimal, chat-focused backend implementation extracted and simplified from the Azure ART Voice Agent Accelerator.

**Purpose:** Test agent-based chat interaction locally before integrating voice features.

---

## 📁 Project Structure

```
ProjectK/
├── apps/
│   ├── backend/                    # Python FastAPI backend
│   │   ├── registries/
│   │   │   ├── agentstore/         # Agent configurations (YAML + prompts)
│   │   │   │   └── call_screener/
│   │   │   │       └── agent.yaml
│   │   │   └── toolstore/          # Tool registry (for future tools)
│   │   ├── api/
│   │   │   └── v1/
│   │   │       └── endpoints/
│   │   │           ├── health.py   # Health checks
│   │   │           └── chat.py     # WebSocket chat
│   │   └── main.py                 # FastAPI app entry point
│   └── frontend/                   # Frontend (TBD)
├── utils/                          # Shared utilities
├── .env.example                    # Environment variables template
├── pyproject.toml                  # Python dependencies
└── README.md                       # This file
```

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+**
- **pip** or **uv** package manager
- **Azure OpenAI API** access (key + endpoint)
- Optional: **Redis** (for session storage)

### 1. Clone & Setup

```bash
cd /Users/vksvarma/Desktop/ProjectK
```

### 2. Install Dependencies

```bash
# Using pip
pip install -e ".[dev]"

# OR using uv (faster)
uv pip install -e ".[dev]"
```

### 3. Configure Environment

Copy the template and add your Azure credentials:

```bash
cp .env.example .env
```

Edit `.env` and fill in:
```
AZURE_OPENAI_API_KEY=<your-key>
AZURE_OPENAI_ENDPOINT=<your-endpoint>
AZURE_OPENAI_API_VERSION=2024-08-01-preview
```

**Where to find these:**
1. Go to [Azure Portal](https://portal.azure.com)
2. Find your OpenAI resource
3. Go to **Keys and Endpoint** section
4. Copy **Key 1** and **Endpoint URL**

### 4. Run Backend Server

```bash
cd /Users/vksvarma/Desktop/ProjectK/apps/backend
python main.py
```

You should see:
```
======================================================================
🚀 PROJECTK BACKEND STARTUP
======================================================================
📦 Loading agents...
✅ Agents loaded: ['call_screener']
🔧 Initializing tools...
✅ Tools initialized
🤖 Initializing Azure OpenAI...
✅ Azure OpenAI client ready
======================================================================
✨ PROJECTK BACKEND READY
======================================================================
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### 5. Test Endpoints

#### Health Check
```bash
curl http://localhost:8000/api/v1/health
```

#### List Agents
```bash
curl http://localhost:8000/api/v1/agents
```

#### API Documentation
Open in browser: http://localhost:8000/docs

---

## 💬 Testing Chat Interaction

### Via WebSocket (Python)

```python
import asyncio
import websockets
import json

async def test_chat():
    uri = "ws://localhost:8000/api/v1/realtime/conversation"
    async with websockets.connect(uri) as ws:
        # Send message
        message = {
            "text": "Hello, how can I help you?",
            "agent": "call_screener",
            "context": {
                "caller_phone": "+1-555-1234",
                "customer_name": "John Doe",
                "risk_level": "low",
                "interaction_id": "call_001",
                "company_name": "ProjectK Inc"
            }
        }
        
        await ws.send(json.dumps(message))
        
        # Receive response
        response = await ws.recv()
        print("Response:", json.loads(response))

# Run
asyncio.run(test_chat())
```

### Via WebSocket (JavaScript/Node.js)

```javascript
const WebSocket = require('ws');

async function testChat() {
    const ws = new WebSocket('ws://localhost:8000/api/v1/realtime/conversation');
    
    ws.onopen = () => {
        const message = {
            text: "Hello, I have a question about my account",
            agent: "call_screener",
            context: {
                caller_phone: "+1-555-1234",
                customer_name: "Jane Smith",
                risk_level: "medium",
                interaction_id: "call_002",
                company_name: "ProjectK Inc"
            }
        };
        ws.send(JSON.stringify(message));
    };
    
    ws.onmessage = (event) => {
        console.log("Response:", JSON.parse(event.data));
        ws.close();
    };
}

testChat();
```

### Via cURL (testing setup)

```bash
# 1. Check server is running
curl http://localhost:8000/health

# 2. List available agents
curl http://localhost:8000/api/v1/agents

# 3. Check API docs
open http://localhost:8000/docs
```

---

## 📋 How It Works

### Chat Flow

```
User Message (WebSocket)
    ↓
[main.py] Receive JSON
    ↓
[chat.py] Load agent config (call_screener/agent.yaml)
    ↓
[base.py] Render Jinja2 prompt with context variables
    ↓
[OpenAI API] Call gpt-4o with system prompt + user message
    ↓
Get response from OpenAI
    ↓
Send back via WebSocket
```

### Agent Configuration

Agent config in `apps/backend/registries/agentstore/call_screener/agent.yaml`:

```yaml
name: call_screener
description: "AI-powered call screening"
greeting: "Hello! How can I help?"

model:
  deployment_id: gpt-4o           # Azure OpenAI deployment
  temperature: 0.7
  max_tokens: 500

prompt_template: |
  You are a professional AI assistant for {{ company_name }}.
  
  Call Context:
  - Caller: {{ caller_phone }}
  - Customer: {{ customer_name }}
  - Risk Level: {{ risk_level }}
  
  Be helpful and professional.
```

Template variables (from `context` in WebSocket message):
- `company_name` - Your company
- `caller_phone` - Caller's phone number
- `customer_name` - Customer name
- `risk_level` - low/medium/high
- `interaction_id` - Unique call ID

---

## 🔧 Configuration

### Environment Variables (`.env`)

| Variable | Required | Example | Notes |
|----------|----------|---------|-------|
| `AZURE_OPENAI_API_KEY` | ✅ Yes | `sk-...` | From Azure Portal |
| `AZURE_OPENAI_ENDPOINT` | ✅ Yes | `https://xxx.openai.azure.com/` | From Azure Portal |
| `AZURE_OPENAI_API_VERSION` | ✅ Yes | `2024-08-01-preview` | Usually this version |
| `HOST` | No | `0.0.0.0` | Server host |
| `PORT` | No | `8000` | Server port |
| `ENV` | No | `dev` | Environment (dev/staging/prod) |
| `REDIS_URL` | No | `redis://localhost:6379` | Optional session storage |

### Agent Configuration (YAML)

Edit `apps/backend/registries/agentstore/call_screener/agent.yaml`:

```yaml
name: call_screener                    # Must be unique
description: "Brief description"
greeting: "Greeting message"

model:
  deployment_id: gpt-4o               # Your Azure OpenAI deployment
  temperature: 0.7                    # 0-1 (lower = more focused)
  max_tokens: 500                     # Max response length

voice:
  current_voice: "en-US-AvaMultilingualNeural"  # For future voice support

tools: []                             # Tool names (add later)

handoff:
  trigger: escalate_to_human
  is_entry_point: true

prompt_template: |                    # Jinja2 template
  You are {{ agent_role }}.
  ...
```

---

## 🚨 Troubleshooting

### ❌ `ModuleNotFoundError: No module named 'apps'`

**Solution:** Run from project root and install in editable mode:
```bash
cd /Users/vksvarma/Desktop/ProjectK
pip install -e .
```

### ❌ `AZURE_OPENAI_API_KEY or AZURE_OPENAI_ENDPOINT not set`

**Solution:** 
1. Check `.env` file exists and is in the project root
2. Add your credentials to `.env`:
   ```
   AZURE_OPENAI_API_KEY=your-key-here
   AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
   ```
3. Restart the server

### ❌ `Connection refused` on WebSocket

**Solution:**
1. Make sure server is running (check terminal output)
2. Check port 8000 is not in use: `lsof -i :8000`
3. If in use, change PORT in `.env` and restart

### ❌ `401 Unauthorized` from OpenAI API

**Solution:**
1. Verify API key is correct in `.env`
2. Check endpoint URL format: `https://xxx.openai.azure.com/`
3. Make sure deployment name (`gpt-4o`) exists in Azure OpenAI resource

### ❌ WebSocket timeout or no response

**Solution:**
1. Check server logs for errors
2. Verify Azure OpenAI is responding: Test in Azure Portal
3. Check network connectivity to Azure
4. Increase timeout if network is slow

---

## 📝 Next Steps

### Phase 1: Chat Testing (Current)
- ✅ Backend API working
- ✅ Azure OpenAI integration
- ✅ Agents configured
- [ ] Frontend chat UI

### Phase 2: Frontend (Next)
- Build simple React/Expo chat interface
- Connect to WebSocket endpoint
- Add message history
- Add context variables input

### Phase 3: Voice Integration (Later)
- Add Azure Speech Services (STT/TTS)
- Integrate Exotel for phone calls
- Add real-time voice streaming

### Phase 4: Tools & Features (Later)
- Implement tool registry
- Add fraud detection tools
- Add customer lookup
- Add escalation to human

---

## 📚 Resources

- **Azure OpenAI Docs**: https://learn.microsoft.com/azure/ai-services/openai/
- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **ART Accelerator**: https://github.com/Azure-Samples/art-voice-agent-accelerator
- **Exotel Docs** (for phone): https://exotel.com/api-docs/

---

## ✅ Verification Checklist

Before testing chat, verify:

- [ ] Python 3.11+ installed
- [ ] Dependencies installed (`pip install -e .`)
- [ ] `.env` file created with Azure credentials
- [ ] Server starts without errors
- [ ] `/api/v1/health` returns `{"status": "healthy"}`
- [ ] `/api/v1/agents` lists `call_screener`
- [ ] WebSocket connection accepted
- [ ] Chat message gets response from OpenAI

---

## 📞 Support

For issues:
1. Check **Troubleshooting** section above
2. Review server logs (terminal output)
3. Verify Azure credentials in `.env`
4. Check network connectivity
5. Open an issue with error details

---

**Version:** 1.0.0  
**Status:** Chat-only MVP  
**Last Updated:** May 2026
