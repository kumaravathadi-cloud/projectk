# ART Accelerator → ProjectK: Quick Reference & Extraction Guide

## What to Extract (Copy) vs Build Fresh

### ✅ COPY DIRECTLY (Reusable as-is)

| Component | Location | ProjectK Destination | Why |
|-----------|----------|---------------------|-----|
| **Voice Orchestrator** | `apps/artagent/backend/voice/voicelive/` | `apps/backend/voice/` | Drop-in; handles STT/TTS/latency |
| **Speech Cascade Handler** | `apps/artagent/backend/voice/speech_cascade/` | `apps/backend/voice/` | Alternative to VoiceLive; simpler |
| **Tool Registry Pattern** | `apps/artagent/backend/registries/toolstore/registry.py` | `apps/backend/registries/toolstore/` | Simple tool registration system |
| **Jinja2 Templating** | `apps/artagent/backend/registries/agentstore/loader.py` | `apps/backend/registries/agentstore/` | `load_prompt()` function |
| **YAML Agent Loader** | `apps/artagent/backend/registries/agentstore/base.py` + `loader.py` | `apps/backend/registries/agentstore/` | YAML parsing + validation |
| **Health Endpoints** | `apps/artagent/backend/api/v1/endpoints/health.py` | `apps/backend/api/v1/endpoints/` | `/health`, `/ready` probes |
| **Frontend WebSocket Handler** | `apps/artagent/frontend/src/components/RealTimeVoiceApp.jsx` | `apps/mobile/src/` | WebSocket pattern (adapt for Expo) |
| **Logging Utilities** | `utils/ml_logging.py` | `utils/ml_logging.py` | OpenTelemetry integration |

### ⚠️ ADAPT (Copy + Simplify)

| Component | Original Location | What to Change | Why |
|-----------|-------------------|-----------------|-----|
| **main.py** | `apps/artagent/backend/main.py` | Remove multi-agent routing, scenario builder, MCP servers | ProjectK: single agent |
| **Agent System** | `apps/artagent/backend/registries/agentstore/` | Keep YAML structure; remove 20+ agents; keep only call_screener | Single agent instead of multi-agent |
| **Tool Store** | `apps/artagent/backend/registries/toolstore/` | Keep only banking, fraud, compliance tools; remove insurance, etc. | Domain-specific tools |
| **API Router** | `apps/artagent/backend/api/v1/router.py` | Include only: health, realtime, browser endpoints; remove agent_builder, scenario_builder | Simpler surface area |
| **Frontend** | `apps/artagent/frontend/` | Extract chat logic; adapt Material-UI to Expo/Tamagui | Different UI framework |
| **Docker** | `apps/artagent/backend/Dockerfile` | Keep structure; adjust dependencies in pip install | Same base approach |

### ❌ SKIP (Too Complex for ProjectK)

| Component | Why Not Needed |
|-----------|-------|
| **Agent Builder UI** | ProjectK has fixed call screener agent |
| **Scenario Builder** | No industry scenario switching |
| **Multi-Agent Handoff System** | Single agent; maybe escalate to human |
| **MCP Server Integration** | Keep tool registry simple |
| **Cosmos DB Integration** | Use simpler storage or AWS DynamoDB |
| **Comprehensive Telemetry** | Basic logging sufficient |
| **Session Manager** | Keep call-scoped, not session-scoped |
| **Demo Environment** | Different architecture (Exotel) |

---

## Key Files to Reference

### Understand Agent System
1. **base.py**: `UnifiedAgent`, `ModelConfig` classes
2. **_defaults.yaml**: How defaults work
3. **loader.py**: Agent YAML parsing + Jinja2
4. **Example agent**: `fraud_agent/agent.yaml` (good template)

### Understand Backend Startup
1. **main.py**: Lines 36-71 (imports), 122-137 (lifespan)
2. **lifecycle/manager.py**: LifecycleManager orchestration
3. **lifecycle/steps.py**: Individual startup steps

### Understand WebSocket Chat
1. **browser.py**: `websocket_conversation()` endpoint
2. **RealTimeVoiceApp.jsx**: Frontend WebSocket usage (React pattern; adapt to Expo)

### Understand Tool Integration
1. **toolstore/registry.py**: `@register_tool` decorator
2. **toolstore/banking/**: Example tool implementations
3. **toolstore/handoffs.py**: Escalation/transfer pattern

---

## ProjectK-Specific Setup

### 1. Minimal pyproject.toml

```toml
[project]
name = "projectk-backend"
version = "1.0.0"
requires-python = ">=3.11"

dependencies = [
    # Core
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "pydantic>=2.5.0",
    
    # Azure
    "azure-openai>=1.6.0",
    "azure-cognitiveservices-speech>=1.43.0",
    "azure-communication-calling>=1.0",
    "azure-identity>=1.14.0",
    
    # Config
    "python-dotenv>=1.0.0",
    "pyyaml>=6.0",
    "jinja2>=3.0.0",
    
    # Exotel (for telephony)
    "requests>=2.31.0",
    "aiohttp>=3.9.0",
    
    # Cache
    "redis>=5.0.0",  # for session state
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-asyncio>=0.21.0",
]
```

### 2. Minimal Agent YAML

```yaml
# apps/backend/registries/agentstore/call_screener/agent.yaml

name: call_screener
description: "AI-powered call screening agent for inbound calls"

model:
  deployment_id: gpt-4o
  temperature: 0.7
  max_tokens: 500
  api_version: "2024-08-01-preview"

voice:
  current_voice: "en-US-AvaMultilingualNeural"

tools:
  - fraud_check
  - customer_lookup
  - transaction_verify
  - escalate_to_human

system_prompt: |
  You are a professional call screener for {{ company_name }}.
  
  Caller Information:
  - Phone: {{ caller_phone }}
  - Identified as: {{ customer_name }}
  - Risk Level: {{ risk_level }}
  - Recent fraud flags: {{ fraud_flags }}
  
  Your mission:
  1. Politely greet and identify the purpose of the call
  2. Perform fraud/verification checks as needed
  3. Route appropriately (accept, escalate, or decline)
  4. Always document the interaction
  
  Be friendly but professional. Prioritize security.
```

### 3. Minimal main.py

```python
# apps/backend/main.py

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import yaml
from pathlib import Path

from apps.backend.registries.agentstore.loader import discover_agents, load_prompt
from apps.backend.registries.toolstore.registry import initialize_tools
from utils.ml_logging import get_logger

logger = get_logger("main")

# ═════════════════════════════════════════════════════════════════════════════
# LIFECYCLE
# ═════════════════════════════════════════════════════════════════════════════

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Initializing ProjectK backend...")
    
    # Load call_screener agent
    agents = discover_agents()
    app.state.agents = agents
    logger.info(f"✅ Loaded agent: {list(agents.keys())}")
    
    # Initialize tools
    initialize_tools()
    logger.info("✅ Tools initialized")
    
    # Initialize Azure OpenAI
    from azure.openai import AsyncAzureOpenAI
    app.state.aoai_client = AsyncAzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version="2024-08-01-preview",
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    )
    logger.info("✅ Azure OpenAI ready")
    
    # Initialize Redis
    try:
        import redis.asyncio as redis
        app.state.redis = await redis.from_url("redis://localhost:6379")
        logger.info("✅ Redis connected")
    except:
        logger.warning("⚠️  Redis unavailable (session storage disabled)")
        app.state.redis = None
    
    yield  # App runs
    
    # Shutdown
    if app.state.redis:
        await app.state.redis.close()

# ═════════════════════════════════════════════════════════════════════════════
# APP
# ═════════════════════════════════════════════════════════════════════════════

app = FastAPI(
    title="ProjectK Call Screening API",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ═════════════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ═════════════════════════════════════════════════════════════════════════════

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/ready")
async def ready():
    return {"status": "ready" if app.state.agents else "not_ready"}

@app.websocket("/api/v1/realtime/conversation")
async def websocket_chat(ws: WebSocket):
    """Call screening chat via WebSocket."""
    await ws.accept()
    
    try:
        while True:
            data = await ws.receive_json()
            
            # Get agent & context
            agent = app.state.agents["call_screener"]
            
            context = {
                "company_name": "ProjectK",
                "caller_phone": data.get("phone", "unknown"),
                "customer_name": data.get("customer_name", "Unknown"),
                "risk_level": data.get("risk_level", "low"),
                "fraud_flags": data.get("fraud_flags", []),
            }
            
            # Load prompt
            system_prompt = load_prompt(agent, context)
            
            # Call LLM
            response = await app.state.aoai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": data.get("text", "")},
                ],
                temperature=0.7,
                max_tokens=500,
            )
            
            # Send back
            await ws.send_json({
                "text": response.choices[0].message.content,
                "call_id": data.get("call_id"),
            })
    
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await ws.send_json({"error": str(e)})
    finally:
        await ws.close()

# ═════════════════════════════════════════════════════════════════════════════
# RUN
# ═════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 4. Exotel WebHook Handler

```python
# apps/backend/api/v1/endpoints/calls.py

from fastapi import APIRouter, Request
from utils.ml_logging import get_logger

logger = get_logger("calls")
router = APIRouter()

@router.post("/webhook/exotel")
async def exotel_webhook(request: Request):
    """
    Handle incoming call from Exotel.
    
    Exotel payload (example):
    {
        "MessageType": "NewCall",
        "CallSid": "...",
        "CallerId": "+91...",
        "ToNumber": "+91...",
        "Direction": "Inbound",
        "Timestamp": "..."
    }
    """
    data = await request.json()
    
    if data.get("MessageType") == "NewCall":
        call_sid = data.get("CallSid")
        caller = data.get("CallerId")
        
        logger.info(f"📞 Incoming call: {call_sid} from {caller}")
        
        # Lookup customer risk
        risk = await lookup_customer_risk(caller)
        
        # Initiate screening
        await start_screening(call_sid, caller, risk)
    
    return {"status": "ok"}

async def lookup_customer_risk(phone: str) -> str:
    """Lookup customer fraud risk from DB."""
    # TODO: Query Cosmos DB / ProjectK DB
    return "low"

async def start_screening(call_sid: str, caller: str, risk: str):
    """Start call screening via WebSocket to mobile app."""
    # TODO: Push to mobile app via Firebase Cloud Messaging
    pass
```

---

## Integration Points with ProjectK

### Mobile App ↔ Backend

**OpenAI Realtime API Path** (Voice-to-Voice):
```
Phone Call
  ↓ Exotel SIP
  ↓ Cloud DID (forwarded)
  ↓ ProjectK Backend (media handler)
  ↓ Azure VoiceLive SDK
  ├─ STT (speech → text)
  ├─ LLM (gpt-4o with context)
  └─ TTS (response → speech)
  ↓ Back to Exotel
  ↓ Phone Speaker
```

**Chat Path** (Mobile UI for testing):
```
Mobile App (Expo)
  ↓ WebSocket
  ↓ ProjectK Backend /api/v1/realtime/conversation
  ├─ Load call_screener agent
  ├─ Render Jinja2 prompt with call context
  ├─ Call Azure OpenAI
  └─ Return response
  ↓ Mobile App Chat UI
```

### Call Context Variables

**Available in Jinja2 templates**:
```python
context = {
    "caller_phone": "+918888888888",
    "customer_name": "Alice Brown",
    "customer_id": "cust_12345",
    "risk_level": "high",  # from fraud-check tool
    "recent_calls": 3,      # last 24h
    "recent_fraud_flags": ["card_reported_lost"],
    "account_status": "active",
    "last_transaction": "2025-05-20T10:15:00Z",
    "transaction_amount": 50000,
    "is_known_device": False,
    "company_name": "ProjectK",
}
```

---

## Deployment Checklist

### Local Development
- [ ] Copy `apps/artagent/backend/registries/` → `apps/backend/registries/`
- [ ] Copy voice orchestration → `apps/backend/voice/`
- [ ] Create minimal `main.py` (see above)
- [ ] Create `call_screener/agent.yaml`
- [ ] Create `pyproject.toml`
- [ ] Install: `uv sync`
- [ ] Test: `uvicorn apps.backend.main:app --reload`
- [ ] Hit `GET /health` → `{"status": "healthy"}`
- [ ] WebSocket test via frontend

### Azure Container Apps
- [ ] Create Backend Dockerfile (based on ARTAgent's)
- [ ] Push to ACR
- [ ] Create Container App with environment variables:
  - `AZURE_OPENAI_API_KEY`
  - `AZURE_OPENAI_ENDPOINT`
  - `REDIS_URL`
  - `EXOTEL_API_KEY`
  - `EXOTEL_SID`
- [ ] Create App Configuration for dynamic config
- [ ] Test `/health` endpoint
- [ ] Configure Exotel webhook to POST to `/api/v1/webhook/exotel`

### Frontend (Mobile)
- [ ] Update WebSocket URL to backend FQDN
- [ ] Test chat endpoint before voice integration
- [ ] Implement voice capture (native modules)
- [ ] Connect to media handler

---

## Performance Baselines

From ARTAgent benchmarks:

| Metric | Baseline | Target |
|--------|----------|--------|
| Chat latency (text input → response) | 500-700ms | <1s |
| Voice latency (STT → LLM → TTS) | 200-400ms (VoiceLive) | <500ms |
| Call accept time (ring → pick up) | 1-2s | <3s |
| Concurrent calls @ 100 users | 20-30 concurrent | 5-10 (Exotel shared DID) |

---

## Next Steps

1. **Week 1**: Extract agentstore + toolstore patterns; build minimal main.py
2. **Week 2**: Integrate Azure OpenAI; test chat endpoint
3. **Week 3**: Add Exotel webhook; test end-to-end call routing
4. **Week 4**: Voice orchestration (VoiceLive or SpeechCascade)
5. **Week 5-6**: Mobile app integration + testing

---

## References & Resources

- **ART Accelerator Repo**: https://github.com/Azure-Samples/art-voice-agent-accelerator
- **Key Files**: 
  - Main: `apps/artagent/backend/main.py`
  - Agents: `apps/artagent/backend/registries/agentstore/`
  - Voice: `apps/artagent/backend/voice/`
- **Azure OpenAI**: https://learn.microsoft.com/en-us/azure/ai-services/openai/
- **FastAPI WebSocket**: https://fastapi.tiangolo.com/advanced/websockets/
- **Jinja2**: https://jinja.palletsprojects.com/

