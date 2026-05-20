# ProjectK Codebase Guide

This document explains the codebase structure and how to extend it.

---

## 📂 Directory Structure

```
ProjectK/
├── apps/
│   ├── backend/                    # FastAPI backend (Python)
│   │   ├── main.py                 # ⭐ Entry point - app initialization
│   │   ├── registries/
│   │   │   ├── agentstore/         # 🤖 Agent definitions
│   │   │   │   ├── base.py         # UnifiedAgent class
│   │   │   │   ├── loader.py       # Agent discovery/loading
│   │   │   │   └── call_screener/  # Example agent
│   │   │   │       └── agent.yaml  # Agent config (editable)
│   │   │   └── toolstore/          # 🔧 Tool registry
│   │   │       └── registry.py     # Tool registration system
│   │   └── api/
│   │       └── v1/
│   │           └── endpoints/
│   │               ├── health.py   # Health/readiness/agents
│   │               └── chat.py     # WebSocket chat endpoint
│   │
│   └── frontend/                   # Frontend code (TBD)
│       └── src/
│
├── utils/                          # Shared utilities
├── pyproject.toml                  # Dependencies & metadata
├── .env.example                    # Template for .env
├── .env                            # Your config (create from .example)
├── README.md                       # Main documentation
├── SETUP_CHECKLIST.md              # Step-by-step setup
├── test_chat.py                    # Automated test script
└── QUICK_REFERENCE.md              # From ART analysis
```

---

## 🔧 Core Components

### 1. Agent System (`registries/agentstore/`)

**What it does:** Defines AI agents that handle conversations.

**Key Classes:**
- `UnifiedAgent` - Agent configuration (name, model, prompt, tools)
- `ModelConfig` - LLM settings (temperature, max_tokens, etc.)
- `HandoffConfig` - Agent routing rules

**How to:**

#### Add a new agent:
```bash
mkdir apps/backend/registries/agentstore/my_agent
cat > apps/backend/registries/agentstore/my_agent/agent.yaml << 'EOF'
name: my_agent
description: "What this agent does"
greeting: "Hello, I'm..."

model:
  deployment_id: gpt-4o
  temperature: 0.7
  max_tokens: 500

prompt_template: |
  You are {{ agent_role }}.
  Be professional and helpful.
EOF
```

#### Customize agent prompt:
Edit the `prompt_template` section. Available variables:
- `company_name` - From context
- `caller_phone` - From context
- `customer_name` - From context
- `risk_level` - From context
- Any custom variable you pass in context

#### Change model:
Edit `model.deployment_id` to match your Azure OpenAI deployment name.

---

### 2. Tool Registry (`registries/toolstore/`)

**What it does:** Registers tools (functions) that agents can call.

**Key Classes:**
- `ToolDefinition` - Tool metadata and executor
- `register_tool()` - Register a tool
- `execute_tool()` - Call a tool

**How to:**

#### Add a new tool:
```python
# apps/backend/registries/toolstore/my_tools.py

from registry import register_tool

async def check_fraud(arguments):
    """Check if transaction is fraudulent."""
    phone = arguments.get("phone")
    amount = arguments.get("amount")
    
    # Your logic here
    is_fraud = amount > 10000  # Example
    
    return {
        "phone": phone,
        "amount": amount,
        "is_fraud": is_fraud,
        "risk_score": 0.8 if is_fraud else 0.1
    }

# Register it
register_tool(
    name="check_fraud",
    schema={
        "type": "object",
        "properties": {
            "phone": {"type": "string"},
            "amount": {"type": "number"}
        },
        "required": ["phone", "amount"]
    },
    executor=check_fraud,
    description="Check if a transaction is fraudulent"
)
```

#### Use in agent:
```yaml
# In agent.yaml
tools:
  - check_fraud
  - lookup_customer
  - escalate_to_human
```

---

### 3. Chat Endpoint (`api/v1/endpoints/chat.py`)

**What it does:** WebSocket endpoint for chat interaction.

**How to:**

#### Test programmatically:
```python
import asyncio
import websockets
import json

async def test():
    async with websockets.connect("ws://localhost:8000/api/v1/realtime/conversation") as ws:
        msg = {
            "text": "Hello",
            "agent": "call_screener",
            "context": {
                "caller_phone": "+1-555-1234",
                "customer_name": "John",
                "company_name": "ProjectK"
            }
        }
        await ws.send(json.dumps(msg))
        response = await ws.recv()
        print(json.loads(response))

asyncio.run(test())
```

#### Customize:
- Edit agent selection logic
- Add conversation history management
- Add tool invocation handling
- Add logging/analytics

---

## 🚀 Extension Points

### Adding Multi-Agent Support

Currently: Single agent (`call_screener`)
Future: Multiple agents with routing

```yaml
# Example: Banking agent with routing
agents:
  - concierge (entry point)
  - fraud_agent
  - account_specialist
  
handoffs:
  concierge -> fraud_agent (if fraud detected)
  concierge -> account_specialist (if account issue)
```

**Code location:** `api/v1/endpoints/chat.py` - extend routing logic

---

### Adding Tool Invocation

Currently: Tools registered but not called by agents
Future: Agents call tools during conversation

**Code location:** `registries/toolstore/registry.py` - add `execute_tool()` calls in chat endpoint

**Example:**
```python
# In chat.py, after agent response
if "tool_use" in response:
    tool_name = response["tool_use"]["name"]
    args = response["tool_use"]["arguments"]
    result = await execute_tool(tool_name, args)
    # Send result back to agent
```

---

### Adding Conversation Memory

Currently: Stateless (no history)
Future: Remember previous messages

```python
# In chat.py

conversation_history = []  # Add this

# Store conversation
conversation_history.append({
    "role": "user",
    "content": user_message
})
conversation_history.append({
    "role": "assistant", 
    "content": agent_response
})

# Use in next request
response = await aoai_client.chat.completions.create(
    model=agent.model.deployment_id,
    messages=[
        {"role": "system", "content": system_prompt},
        *conversation_history  # Include full history
    ]
)
```

---

### Adding Voice Support

Future: STT (speech-to-text) and TTS (text-to-speech)

**Required services:**
- Azure Speech Services (for STT/TTS)
- Azure Communication Services (for SIP/telephony)
- Exotel (for India-specific calling)

**Code location:** Create `apps/backend/voice/` similar to ART repo

---

## 🔍 Key Files & Functions

| File | Key Functions |
|------|---|
| `main.py` | `lifespan()` - Startup/shutdown |
| `agentstore/base.py` | `UnifiedAgent.render_prompt()` |
| `agentstore/loader.py` | `discover_agents()` |
| `toolstore/registry.py` | `register_tool()`, `execute_tool()` |
| `api/v1/endpoints/chat.py` | `websocket_chat()` |

---

## 📊 Data Flow

### Startup Flow
```
main.py starts
  ↓
lifespan (startup section)
  ↓
discover_agents()  (scan agentstore/)
  ↓
initialize_tools() (register tools)
  ↓
Initialize Azure OpenAI client
  ↓
Initialize Redis (optional)
  ↓
App ready for requests
```

### Chat Flow
```
WebSocket message received
  ↓
Load agent config (from agents dict)
  ↓
Render Jinja2 prompt with context
  ↓
Call Azure OpenAI API
  ↓
Get response
  ↓
Send back via WebSocket
```

### Agent Discovery Flow
```
Scan registries/agentstore/
  ↓
For each subdirectory:
  - Find agent.yaml
  - Parse YAML
  - Create UnifiedAgent instance
  - Store in agents dict
  ↓
Return agents dict
```

---

## 🧪 Testing

### Unit Tests (Add as needed)
```python
# tests/test_agents.py
import pytest
from apps.backend.registries.agentstore.loader import discover_agents

def test_agent_discovery():
    agents = discover_agents()
    assert "call_screener" in agents
    assert agents["call_screener"].name == "call_screener"

def test_prompt_rendering():
    agent = agents["call_screener"]
    rendered = agent.render_prompt({
        "company_name": "Test Co",
        "caller_phone": "+1-555-1234"
    })
    assert "Test Co" in rendered
```

### Integration Tests
```python
# tests/test_chat.py
import pytest
from fastapi.testclient import TestClient
from main import app

def test_health():
    client = TestClient(app)
    response = client.get("/api/v1/health")
    assert response.status_code == 200
```

### Manual Testing
Use `test_chat.py`:
```bash
python test_chat.py
```

---

## 🐛 Debugging

### Enable debug logging
```python
# In main.py, after logging.basicConfig():
logger.setLevel(logging.DEBUG)
```

### Print agent config
```python
# In chat.py
print(f"Agent: {agent.name}")
print(f"Prompt: {agent.prompt_template}")
print(f"Model: {agent.model.deployment_id}")
```

### Check Azure connectivity
```bash
curl -X GET "https://<your-endpoint>/openai/models?api-version=2024-08-01-preview" \
  -H "api-key: <your-key>"
```

---

## 📈 Performance

Current implementation:
- **Latency per request:** ~500-800ms (OpenAI API call ~400ms)
- **Throughput:** Single connection per WebSocket (extend with connection pooling)
- **Memory:** ~150MB (Python runtime + libraries)

Optimization opportunities:
- Cache agent configs (already done)
- Use connection pooling for Azure OpenAI
- Add response streaming
- Implement conversation compression

---

## 🔐 Security Notes

⚠️ **Current implementation for development only:**

- ✅ API keys loaded from `.env` (not hardcoded)
- ⚠️ CORS allows all origins (`*` - restrict for production)
- ⚠️ No authentication on WebSocket
- ⚠️ No rate limiting

**For production:**
```python
# Restrict CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_methods=["GET", "POST"],
)

# Add authentication
from fastapi import HTTPException, Depends

def verify_token(token: str = Header()):
    if token != os.getenv("API_TOKEN"):
        raise HTTPException(status_code=401)
```

---

## 📚 References

- **FastAPI:** https://fastapi.tiangolo.com/
- **WebSocket:** https://fastapi.tiangolo.com/advanced/websockets/
- **Azure OpenAI:** https://learn.microsoft.com/azure/ai-services/openai/
- **Pydantic:** https://docs.pydantic.dev/
- **Jinja2:** https://jinja.palletsprojects.com/

---

**Last Updated:** May 2026  
**Version:** 1.0.0 (Chat Only)
