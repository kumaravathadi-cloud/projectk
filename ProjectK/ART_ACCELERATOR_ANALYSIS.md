# Azure ART Voice Agent Accelerator - Deep Analysis for ProjectK

**Repository**: https://github.com/Azure-Samples/art-voice-agent-accelerator  
**Last Analyzed**: May 20, 2026  
**Purpose**: Extract patterns for projectK call screening bot

---

## Executive Summary

The ART (Azure Real-Time) Voice Agent Accelerator is a production-grade framework for building omnichannel, multi-agent voice systems on Azure. It emphasizes:
- **Code-first**: YAML agent configs + Jinja2 prompts (no low-code builders required)
- **Modular**: Pluggable voice orchestrators (SpeechCascade vs VoiceLive)
- **Multi-agent**: Built-in handoff protocol for agent transfers
- **Ops-ready**: Comprehensive health checks, observability, lifecycle management

**For ProjectK**, the framework is **over-engineered** (multi-agent, handoffs, industry scenarios) but provides excellent **patterns and libraries** to reuse.

---

## 1. FRONTEND STACK: React + Vite + WebSocket

### Filesystem Layout
```
apps/artagent/frontend/
├── index.html                    # Main HTML template
├── package.json                  # Node.js dependencies + scripts
├── package-lock.json
├── vite.config.js               # Vite bundler config
├── eslint.config.js             # Code quality rules
├── entrypoint.sh                # Docker runtime: Replace placeholders
├── Dockerfile                   # Multi-stage: builder + nginx
│
├── src/
│   ├── main.jsx                 # React entry (createRoot, renders App)
│   ├── index.css                # Global styles
│   │
│   ├── components/
│   │   ├── App.jsx              # Root wrapper (~50 lines)
│   │   ├── RealTimeVoiceApp.jsx # CORE: 5200+ lines
│   │   │                        # - WebSocket management
│   │   │                        # - Chat UI + voice controls
│   │   │                        # - Agent selection
│   │   │                        # - Call state
│   │   ├── ProfileDetailsPanel.jsx   # Customer context sidebar
│   │   ├── AgentDetailsPanel.jsx     # Agent capabilities display
│   │   ├── ScenarioBuilder.jsx       # Dynamic scenario UI
│   │   ├── ConversationControls.jsx  # Call buttons (start/stop)
│   │   ├── WaveformVisualization.jsx # Audio waveform animation
│   │   └── (20+ other components)
│   │
│   ├── hooks/
│   │   ├── index.js            # useAppState(), custom hooks
│   │   ├── useSpeechRecognizer.js
│   │   ├── useWebSocket.js
│   │   └── ...
│   │
│   ├── config/
│   │   └── constants.js         # API_BASE_URL, WS_URL (runtime substitution)
│   │
│   ├── utils/
│   │   ├── logger.js           # Logging with configurable levels
│   │   ├── styles.js           # Shared CSS objects
│   │   └── ...
│   │
│   ├── assets/
│   │   ├── abstract.jpg        # Background image
│   │   ├── images.js           # Asset imports for Vite
│   │   └── ...
│   │
│   └── styles/
│       └── voiceAppStyles.js   # Component-scoped styles
│
└── public/
    └── (static assets)
```

### Framework & Libraries
| Component | Library | Version | Purpose |
|-----------|---------|---------|---------|
| **Runtime** | React | 19+ | Core UI framework |
| **Build** | Vite | 5+ | Lightning-fast bundler |
| **UI** | @mui/material | 5+ | Pre-built Material Design components |
| **Icons** | @mui/icons-material | 5+ | Material Design icons |
| **State** | Zustand (optional) | N/A | State management (not heavily used) |
| **HTTP** | Fetch API | Native | REST calls |
| **WebSocket** | Native WebSocket | Browser | Real-time comms |
| **Voice** | Web Audio API | Browser | Mic input, audio processing |
| **Speech SDK** | microsoft-cognitiveservices-speech-sdk | 1.40+ | Azure Speech recognition (optional) |
| **ACS SDK** | @azure/communication-calling | 1.0+ | Azure Communication Services (phone calls) |

### Entry Point & Initialization
```jsx
// src/main.jsx
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './components/App.jsx'

// Set up logging
configureLogLevel(import.meta.env?.VITE_APP_LOG_LEVEL)

// Mount app to DOM
createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
```

**App.jsx** → **RealTimeVoiceApp.jsx** (main UI component)

### Backend Communication

#### Configuration
**src/config/constants.js**:
```javascript
// Placeholders replaced at Docker startup by entrypoint.sh
const API_BASE_URL = '__BACKEND_URL__'  // → http://localhost:8000 (local dev)
const WS_URL = '__WS_URL__'             // → ws://localhost:8000 (auto-derived)

// Auto-converts HTTPS ↔ WSS, HTTP ↔ WS
const toWsUrl = (url) => {
  if (/^https:\/\//i.test(url)) return url.replace(/^https:\/\//i, 'wss://')
  if (/^http:\/\//i.test(url)) return url.replace(/^http:\/\//i, 'ws://')
  return url
}
```

**Environment Variables** (.env):
```bash
VITE_BACKEND_BASE_URL=http://localhost:8000
VITE_WS_BASE_URL=ws://localhost:8000      # Optional; auto-derived if omitted
VITE_LOG_LEVEL=debug
VITE_BRANCH_NAME=finance                  # For scenario selection
```

#### REST Endpoints Called

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/api/v1/agents` | List available agents + capabilities |
| `GET` | `/api/v1/agents/{name}` | Get specific agent details |
| `GET` | `/api/v1/health` | System health (latency check) |
| `GET` | `/api/v1/readiness` or `/api/v1/ready` | Warmup completion status |
| `POST` | `/api/v1/demo-env/temporary-user` | Create demo user profile |
| `GET` | `/api/v1/tools` | List available tools |
| `GET` | `/api/v1/voices` | List TTS voices |

#### WebSocket Endpoints

| Endpoint | Purpose | Message Schema |
|----------|---------|-----------------|
| `WS /api/v1/realtime/conversation` | Main voice chat (text + audio) | `{ "text": "...", "agent": "name" }` |
| `WS /api/v1/browser/conversation` | Browser-based WebRTC audio | Binary PCM stream |
| `WS /api/v1/media/stream` | ACS media streaming | Μ-law PCM from phone |

**WebSocket Flow** (chat only):
```
Frontend → { "text": "Check my fraud status", "agent": "fraud_agent" }
           ↓
Backend  → Load agent + system prompt → Call Azure OpenAI
           ↓
Frontend ← { "text": "I found...", "choices": [...] }
```

### Key UI Components

#### RealTimeVoiceApp.jsx (Main Interface)
- **Size**: ~5200 lines (large monolithic component)
- **State**: React hooks (useState, useEffect, useCallback)
- **Key state**:
  - `messages`: Array of chat turns
  - `recording`: Is user speaking?
  - `activeAgent`: Currently selected agent
  - `sessionId`: Session context
  - `transcripts`: Full conversation history
  - `callActive`: Is call ongoing?
- **Handlers**:
  - `startCall()`: Initialize WebSocket + audio
  - `stopCall()`: Close connection
  - `sendMessage()`: Send text via WebSocket
  - `handleAudioInput()`: Process mic input

#### ProfileDetailsPanel.jsx (Context Display)
- Shows customer data (name, recent transactions, alerts)
- Fetched from demo-env endpoint
- Auto-refreshes periodically

#### AgentDetailsPanel.jsx (Agent Capabilities)
- Lists agent name, description, tools
- Shows handoff options (other agents this one can transfer to)

#### ConversationControls.jsx
- Start/Stop buttons
- Phone number input (for ACS mode)
- Agent dropdown selector

### Can Frontend Run Standalone?

**YES** ✅
- Pure SPA (Single Page Application)
- All backend logic in separate FastAPI service
- Can be deployed to:
  - Vite dev server (local): `npm run dev`
  - nginx/Apache (production)
  - Azure Static Web Apps
  - AWS S3 + CloudFront
  - Vercel, Netlify

- **Fallback config**: If backend unreachable, shows health error UI
- **Placeholders**: entrypoint.sh replaces `__BACKEND_URL__` at container startup

---

## 2. AGENT SYSTEM: YAML-Based Configuration

### Design Philosophy
> "Agent design is code-first and declarative. Define agents in YAML; orchestration is pure Python."

### Directory Structure
```
apps/artagent/backend/registries/agentstore/
├── README.md                    # Agent system documentation
├── _defaults.yaml              # Inherited by ALL agents
├── base.py                     # Python classes
│   ├── UnifiedAgent           # Agent data model
│   ├── ModelConfig            # LLM settings
│   ├── VoiceConfig            # TTS voice
│   ├── HandoffConfig          # Handoff destination
│   └── SpeechConfig           # STT settings
├── loader.py
│   ├── discover_agents()       # Find all agent.yaml files
│   ├── load_agent()            # Parse YAML → UnifiedAgent
│   ├── load_defaults()         # Load _defaults.yaml
│   ├── load_prompt()           # Render Jinja2 template
│   └── build_agent_summaries() # For API responses
├── session_manager.py
│   ├── get_session_agent()     # Get from cache/disk
│   ├── set_session_agent()     # Store custom (runtime)
│   └── remove_session_agent()  # Delete custom
│
├── fraud_agent/
│   ├── agent.yaml              # Config (overrides _defaults.yaml)
│   ├── prompts/
│   │   ├── system.jinja2      # System prompt (Jinja2 template)
│   │   ├── preamble.jinja2    # Optional preamble
│   │   └── farewell.jinja2    # Optional closing
│   └── tools.yaml             # Tools this agent can call
│
├── decline_specialist/
│   ├── agent.yaml
│   ├── prompts/
│   └── tools.yaml
│
├── compliance_desk/
├── general_agent/
├── banking_agent/
└── (20+ other industry agents...)
```

### agent.yaml Structure

**Minimal Example** (fraud_agent/agent.yaml):
```yaml
# ═══════════════════════════════════════════════════════════════════════════
# Fraud Detection Agent Configuration
# ═══════════════════════════════════════════════════════════════════════════

# Identity
name: fraud_agent
description: "Detects suspicious patterns in customer transactions"

# LLM Overrides (inherits from _defaults.yaml)
model:
  deployment_id: gpt-4o                  # Azure OpenAI model
  temperature: 0.7                       # 0=deterministic, 1=creative
  max_tokens: 1000
  api_version: "2024-08-01-preview"

# Voice (for TTS output)
voice:
  current_voice: "en-US-AvaMultilingualNeural"

# Speech (for STT input)
speech:
  language: "en-US"
  recognition_mode: "Conversation"      # vs "Dictation" or "Interactive"

# Tools this agent can invoke
tools:
  - fraud_check                          # Check transaction for fraud markers
  - transaction_lookup                   # Get customer transaction history
  - escalate_to_human                    # Transfer to human agent
  - block_card                           # Emergency card block

# Handoff: How other agents reach this agent
handoff:
  trigger: handoff_fraud_agent           # Magic string other agents call
  message: "I'm connecting you with our fraud specialist..."
  type: discrete                         # vs "seamless" (no message)

# Jinja2 system prompt (context-aware)
system_prompt: |
  You are a fraud detection specialist at {{ company_name }}.
  
  Your mission:
  1. Ask clarifying questions about recent transactions.
  2. Identify suspicious patterns.
  3. Recommend actions (monitor, block, escalate).
  
  Customer context:
  - Name: {{ user_name }}
  - Risk level: {{ risk_level }}
  - Recent transactions: {{ transaction_count }}
  
  Always be empathetic. Customer is likely anxious about fraud.
```

### _defaults.yaml (Inheritance)

All agents inherit from this base:
```yaml
model:
  deployment_id: gpt-4o
  temperature: 0.7
  api_version: "2024-08-01-preview"
  top_p: 0.95
  
voice:
  current_voice: "en-US-AvaMultilingualNeural"
  
speech:
  language: "en-US"
  
tools: []  # Override per agent

# No handoff by default (only specific agents define it)
handoff: null
```

### Python Classes (base.py)

```python
@dataclass
class ModelConfig:
    """LLM configuration."""
    deployment_id: str           # "gpt-4o", "gpt-35-turbo"
    temperature: float = 0.7     # Creativity (0-1)
    max_tokens: int = 1000       # Response length limit
    api_version: str = "2024-08-01-preview"
    top_p: float = 0.95
    
@dataclass
class VoiceConfig:
    """TTS voice settings."""
    current_voice: str = "en-US-AvaMultilingualNeural"
    
@dataclass
class SpeechConfig:
    """STT settings."""
    language: str = "en-US"
    recognition_mode: str = "Conversation"
    
@dataclass
class HandoffConfig:
    """How to hand off to this agent."""
    trigger: str                 # e.g., "handoff_fraud_agent"
    message: str = ""            # Message to user
    type: str = "discrete"       # "discrete" or "seamless"
    
@dataclass
class UnifiedAgent:
    """Complete agent definition."""
    name: str
    description: str
    model: ModelConfig
    voice: VoiceConfig
    speech: SpeechConfig
    tools: list[str]
    system_prompt: str           # Jinja2 template (not yet rendered)
    handoff: HandoffConfig | None = None
    
    def summary(self) -> dict:
        """For API responses."""
        return {
            "name": self.name,
            "description": self.description,
            "model": {"deployment_id": self.model.deployment_id},
            "voice": {"current_voice": self.voice.current_voice},
            "tools": self.tools,
            "handoff_trigger": self.handoff.trigger if self.handoff else None,
        }
```

### Agent Discovery & Loading (loader.py)

```python
def discover_agents(agents_dir=AGENTS_DIR) -> dict[str, UnifiedAgent]:
    """
    Scan agentstore/ and load all agent.yaml files.
    
    Returns:
        {
            "fraud_agent": UnifiedAgent(...),
            "decline_specialist": UnifiedAgent(...),
            ...
        }
    """
    defaults = load_defaults()
    agents = {}
    
    for agent_dir in agents_dir.glob("*/"):
        agent_file = agent_dir / "agent.yaml"
        if not agent_file.exists():
            continue
        
        # Parse YAML
        config = yaml.safe_load(agent_file.read_text())
        
        # Merge with defaults
        merged = {**defaults, **config}
        
        # Create UnifiedAgent
        agent = UnifiedAgent.from_dict(merged)
        agents[agent.name] = agent
    
    return agents

def load_prompt(agent: UnifiedAgent, context: dict) -> str:
    """
    Load and render Jinja2 prompt with context.
    
    Args:
        agent: UnifiedAgent instance
        context: Variables available in template
            - user_name, company_name, risk_level, etc.
    
    Returns:
        Rendered system prompt (ready for AOAI)
    """
    template = jinja2.Template(agent.system_prompt)
    return template.render(context)
```

### Runtime Agent Management (session_manager.py)

```python
class SessionManager:
    """Manage agents at runtime (per session)."""
    
    def __init__(self, base_agents: dict[str, UnifiedAgent]):
        self._base_agents = base_agents
        self._custom_agents = {}  # For dynamic agents created at runtime
    
    def get_session_agent(self, name: str) -> UnifiedAgent:
        """Get agent (custom first, then base)."""
        if name in self._custom_agents:
            return self._custom_agents[name]
        
        agent = self._base_agents.get(name)
        if not agent:
            raise ValueError(f"Unknown agent: {name}")
        return agent
    
    def set_session_agent(self, name: str, agent: UnifiedAgent) -> None:
        """Store custom agent (created via /api/v1/agent-builder)."""
        self._custom_agents[name] = agent
    
    def list_session_agents(self) -> list[str]:
        """All agents available in this session."""
        return list(self._base_agents.keys()) + list(self._custom_agents.keys())
```

### Handoff Protocol

**Example**: Fraud Agent detects unauthorized access → Handoff to Security Agent

```python
# In agent's tool definition (toolstore/handoffs.py):
@register_tool("escalate_to_fraud_agent")
async def escalate_to_fraud_agent(reason: str) -> dict:
    """
    Handoff trigger. Called by current agent.
    """
    return {
        "action": "handoff",
        "trigger": "handoff_fraud_agent",
        "reason": reason,
        "message": "Connecting you with fraud specialist...",
    }

# Orchestrator receives this, loads target agent:
target_agent = get_unified_agent(app, "fraud_agent")
# Continue conversation with new agent
```

### Jinja2 Prompt Rendering

**Agent YAML**:
```yaml
system_prompt: |
  You are {{ agent_role }}.
  Customer: {{ user_name }} (Risk: {{ risk_level }})
  Recent activity: {{ activity_summary }}
  
  Compliance: {{ compliance_status }}
```

**Rendering at Runtime**:
```python
context = {
    "agent_role": "Fraud Specialist",
    "user_name": "Alice Brown",
    "risk_level": "high",
    "activity_summary": "3 transactions in last 5 mins",
    "compliance_status": "AML compliant",
}
rendered = load_prompt(agent, context)
# → "You are Fraud Specialist. Customer: Alice Brown (Risk: high)..."
```

---

## 3. MINIMAL BACKEND API FOR CHAT-ONLY

### Entry Point: main.py

**Location**: `apps/artagent/backend/main.py`

**Core Responsibility**: 
- Create FastAPI app
- Load agents at startup
- Configure middleware & routes
- Manage application lifecycle

### Minimal Implementation

```python
# apps/artagent/backend/main.py

from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio

# ═════════════════════════════════════════════════════════════════════════════
# IMPORTS
# ═════════════════════════════════════════════════════════════════════════════

from apps.artagent.backend.registries.agentstore.loader import discover_agents
from apps.artagent.backend.config.settings import ALLOWED_ORIGINS, DEBUG_MODE
from apps.artagent.backend.src.utils.aoai import get_aoai_client
from utils.ml_logging import get_logger

logger = get_logger("main")

# ═════════════════════════════════════════════════════════════════════════════
# LIFECYCLE
# ═════════════════════════════════════════════════════════════════════════════

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle."""
    
    # STARTUP
    logger.info("🚀 Starting application...")
    
    # Load agents from YAML
    agents = discover_agents()
    app.state.agents = agents
    logger.info(f"✅ Loaded {len(agents)} agents: {list(agents.keys())}")
    
    # Initialize Azure OpenAI
    app.state.aoai_client = await get_aoai_client()
    logger.info("✅ Azure OpenAI client ready")
    
    # Initialize Redis (optional)
    try:
        import redis.asyncio as redis
        app.state.redis = await redis.from_url("redis://localhost:6379")
        logger.info("✅ Redis connected")
    except Exception as e:
        logger.warning(f"⚠️  Redis unavailable: {e}")
        app.state.redis = None
    
    yield  # Application runs here
    
    # SHUTDOWN
    logger.info("🛑 Shutting down...")
    if app.state.redis:
        await app.state.redis.close()

# ═════════════════════════════════════════════════════════════════════════════
# APP FACTORY
# ═════════════════════════════════════════════════════════════════════════════

def create_app() -> FastAPI:
    """Create FastAPI app with config."""
    return FastAPI(
        title="Real-Time Voice Agent API",
        description="Multi-agent voice orchestration",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs" if DEBUG_MODE else None,
        redoc_url="/redoc" if DEBUG_MODE else None,
    )

app = create_app()

# ═════════════════════════════════════════════════════════════════════════════
# MIDDLEWARE
# ═════════════════════════════════════════════════════════════════════════════

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # ["*"] for dev, ["example.com"] for prod
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# ═════════════════════════════════════════════════════════════════════════════
# REST ENDPOINTS
# ═════════════════════════════════════════════════════════════════════════════

@app.get("/health")
async def health():
    """Liveness probe."""
    return {
        "status": "healthy",
        "version": "1.0.0",
    }

@app.get("/ready")
async def ready():
    """Readiness probe (checks agent loading)."""
    if not hasattr(app.state, 'agents'):
        raise HTTPException(status_code=503, detail="Agents not loaded")
    return {
        "status": "ready",
        "agents": len(app.state.agents),
    }

@app.get("/api/v1/agents")
async def list_agents():
    """List all available agents."""
    agents = app.state.agents
    return {
        "agents": [agent.summary() for agent in agents.values()],
        "count": len(agents),
    }

@app.get("/api/v1/agents/{agent_name}")
async def get_agent(agent_name: str):
    """Get specific agent details."""
    agent = app.state.agents.get(agent_name)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")
    return agent.summary()

# ═════════════════════════════════════════════════════════════════════════════
# WEBSOCKET: MAIN CHAT ENDPOINT
# ═════════════════════════════════════════════════════════════════════════════

@app.websocket("/api/v1/realtime/conversation")
async def websocket_conversation(websocket: WebSocket):
    """
    Real-time chat via WebSocket.
    
    Client sends:
        {"text": "message", "agent": "agent_name", "session_id": "..."}
    
    Server responds:
        {"text": "response", "choices": [...]}
    """
    await websocket.accept()
    logger.info(f"📞 WebSocket connected: {websocket.client}")
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            text = data.get("text", "").strip()
            agent_name = data.get("agent", "general_agent")
            session_id = data.get("session_id")
            
            if not text:
                await websocket.send_json({"error": "Empty message"})
                continue
            
            # Get agent
            agent = app.state.agents.get(agent_name)
            if not agent:
                await websocket.send_json({"error": f"Agent '{agent_name}' not found"})
                continue
            
            logger.info(f"💬 [{agent_name}] User: {text[:50]}")
            
            # Load and render system prompt with context
            from apps.artagent.backend.registries.agentstore.loader import load_prompt
            
            context = {
                "user_name": "User",
                "company_name": "ACME Corp",
                "session_id": session_id,
                # Add more context as needed
            }
            system_prompt = load_prompt(agent, context)
            
            # Call Azure OpenAI
            aoai_client = app.state.aoai_client
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text},
            ]
            
            response = await aoai_client.chat.completions.create(
                model=agent.model.deployment_id,
                messages=messages,
                temperature=agent.model.temperature,
                max_tokens=agent.model.max_tokens,
            )
            
            # Extract response
            reply = response.choices[0].message.content
            logger.info(f"🤖 [{agent_name}] Assistant: {reply[:50]}")
            
            # Send back
            await websocket.send_json({
                "text": reply,
                "agent": agent_name,
                "session_id": session_id,
            })
    
    except Exception as e:
        logger.error(f"❌ WebSocket error: {e}", exc_info=True)
        await websocket.send_json({"error": str(e)})
    
    finally:
        await websocket.close()
        logger.info(f"📞 WebSocket closed: {websocket.client}")

# ═════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=DEBUG_MODE,
    )
```

### Key Startup Steps

From `lifecycle/steps.py` (actual framework):

1. **Core State** (Redis, config)
2. **Agents** (Load from YAML)
3. **Azure OpenAI** (Warm up connection)
4. **Speech Pools** (Pre-fetch STT/TTS tokens, optional)
5. **Event Handlers** (Telemetry, tracing)
6. **Deferred Startup** (Background warmup)

### Required Azure Services

| Service | Required | Alternative | Purpose |
|---------|----------|-------------|---------|
| **Azure OpenAI** | ✅ Yes | No | LLM inference (gpt-4o) |
| **Redis** | ⚠️ Recommended | In-memory dict | Session state, caching |
| **Azure Speech** | ❌ No | Azure OpenAI Realtime | STT/TTS (voice features) |
| **Azure Communication Services** | ❌ No | Third-party telephony | Phone integration |
| **Cosmos DB** | ❌ No | Postgres, MongoDB | Message history, user profiles |
| **Application Insights** | ❌ No | Serilog, DataDog | Observability |

### Minimal Required

For **chat-only** (text):
- ✅ Azure OpenAI (required)
- ⚠️ Redis (optional; use local memory for single-process dev)

For **voice**:
- ✅ Azure OpenAI (required)
- ✅ Azure Speech Services (required for STT/TTS)
- ⚠️ Redis (recommended for multi-turn state)

---

## 4. CORE DEPENDENCIES & VERSIONS

### From pyproject.toml

```toml
[project]
name = "art-voice-agent-accelerator"
version = "1.0.0"
requires-python = ">=3.11"

dependencies = [
    # Web Framework (required)
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "pydantic>=2.5.0",
    "pydantic-settings>=2.0",
    
    # Azure AI/Voice (required for voice; optional for chat-only)
    "azure-ai-voicelive>=1.0.0",        # VoiceLive SDK (voice mode)
    "azure-cognitiveservices-speech>=1.43.0",  # STT/TTS (voice mode)
    "azure-openai>=1.6.0",              # LLM (required)
    
    # Azure Communication Services (optional; for phone)
    "azure-communication-calling>=1.0",
    "azure-communication-callautomation>=1.0",
    
    # Authentication (required)
    "azure-identity>=1.14.0",
    
    # Cache & Database (optional)
    "redis>=5.0.0",                     # Session cache
    "pymongo>=4.6.0",                   # Cosmos DB Python client
    "azure-cosmos>=4.7.0",              # Cosmos DB SDK
    
    # Config & Templating (required)
    "python-dotenv>=1.0.0",             # .env loading
    "pyyaml>=6.0",                      # YAML parsing (agents)
    "jinja2>=3.0.0",                    # Prompt templating
    
    # HTTP (required)
    "httpx>=0.25.0",                    # Async HTTP (MCP servers)
    "aiohttp>=3.9.0",                   # Async HTTP client
    
    # Logging & Telemetry (optional)
    "opentelemetry-api>=1.20.0",
    "opentelemetry-sdk>=1.20.0",
    "azure-monitor-opentelemetry>=1.0.0",
    
    # Crypto (optional)
    "cryptography>=41.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-asyncio>=0.21.0",
    "black>=23.0",
    "ruff>=0.1.0",
    "mypy>=1.0",
]

audio = [
    "pyaudio>=0.2.13",                  # Mic input (local dev only)
    "sounddevice>=0.4.5",               # Cross-platform audio
]

docs = [
    "mkdocs>=1.6.1",
    "mkdocs-material>=9.4.0",
    "mkdocstrings[python]>=0.20.0",
    "pymdown-extensions>=10.0.0",
]
```

### Version Constraints

| Package | Version | Constraint | Reason |
|---------|---------|-----------|--------|
| Python | 3.11+ | Hard | async/await, type hints |
| FastAPI | 0.109+ | Soft | Latest features; older versions work |
| Pydantic | v2.0+ | Hard | Breaking changes from v1 |
| Azure SDKs | Latest | Soft | Auto-updated via Dependabot |
| Uvicorn | 0.27+ | Soft | ASGI server; flexible |

### Optional vs Core

**MUST HAVE**:
- fastapi, uvicorn, pydantic
- azure-openai (LLM)
- pyyaml, jinja2 (agent config)
- azure-identity (auth)
- python-dotenv (env vars)

**SHOULD HAVE**:
- redis (session state for multi-turn)

**NICE TO HAVE**:
- azure-cognitiveservices-speech (voice mode)
- azure-communication-* (phone integration)
- pymongo, azure-cosmos (persistence)
- opentelemetry (observability)
- mkdocs (documentation)

**DEV ONLY**:
- pytest, black, ruff, mypy
- pyaudio, sounddevice (audio input for local testing)

---

## 5. COMMUNICATION ARCHITECTURE FOR CHAT

### High-Level Flow

```
┌──────────────────────────────────────────────────────────────┐
│ 1. FRONTEND (React on :5173)                                 │
│                                                               │
│  User enters: "What's my account status?"                    │
│  Selects agent: "banking_agent"                              │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ RealTimeVoiceApp.jsx                                    │ │
│  │  • handleSendMessage(text, agentName)                   │ │
│  │  • WebSocket.send({text, agent})                        │ │
│  └─────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
    │
    │ WebSocket: WS /api/v1/realtime/conversation
    │ Message: {"text": "What's my account status?", "agent": "banking_agent"}
    │
    ▼
┌──────────────────────────────────────────────────────────────┐
│ 2. BACKEND (FastAPI on :8000)                                │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ main.py: WebSocket handler                              │ │
│  │                                                          │ │
│  │  1. accept(websocket)                                   │ │
│  │  2. data = receive_json()                               │ │
│  │  3. agent = app.state.agents["banking_agent"]           │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ Orchestration                                           │ │
│  │                                                          │ │
│  │  1. Load agent YAML config                              │ │
│  │  2. Load system_prompt (Jinja2 template)                │ │
│  │  3. Render prompt with context:                         │ │
│  │     - user_name                                         │ │
│  │     - account_details                                   │ │
│  │     - recent_transactions                               │ │
│  │  4. Prepare messages:                                   │ │
│  │     - system: "You are a banking agent..."              │ │
│  │     - user: "What's my account status?"                 │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ Azure OpenAI Call                                       │ │
│  │                                                          │ │
│  │  aoai_client.chat.completions.create(                   │ │
│  │    model="gpt-4o",                                      │ │
│  │    messages=[...],                                      │ │
│  │    temperature=0.7,                                     │ │
│  │  )                                                       │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                               │
└──────────────────────────────────────────────────────────────┘
    │
    │ Azure: gpt-4o (2024-08 version)
    │ Input: system + user message
    │ Output: Assistant response
    │
    ▼
┌──────────────────────────────────────────────────────────────┐
│ 3. RESPONSE (via WebSocket)                                  │
│                                                               │
│  Backend sends:                                              │
│  {                                                           │
│    "text": "Your checking account has $5,234.56...",        │
│    "agent": "banking_agent",                                │
│    "session_id": "sess_12345"                               │
│  }                                                           │
│                                                               │
│  Frontend receives & renders in chat UI                     │
│  ✅ User sees response in ~500ms (AOAI latency)             │
└──────────────────────────────────────────────────────────────┘
```

### REST Calls (Setup Phase)

**1. Get Available Agents**
```javascript
// Frontend: App startup
fetch('http://localhost:8000/api/v1/agents')
  .then(r => r.json())
  .then(data => {
    // data.agents = [
    //   { name: "banking_agent", description: "...", tools: [...] },
    //   { name: "fraud_agent", description: "...", tools: [...] },
    // ]
    setAgents(data.agents);
  })
```

**2. Check System Health**
```javascript
// Frontend: Before connecting WebSocket
fetch('http://localhost:8000/api/v1/health')
  .then(r => r.json())
  // { "status": "healthy", "version": "1.0.0" }
```

**3. Check Readiness (Optional)**
```javascript
// Wait for startup tasks to complete
fetch('http://localhost:8000/api/v1/ready')
  .then(r => {
    if (r.status === 200) {
      // Ready: all warmup done
      connectWebSocket();
    } else {
      // Still starting up (503)
      setTimeout(() => check again, 1000);
    }
  })
```

### WebSocket Message Flow

**Text Chat (no audio)**

```
Client ──────→ {"text": "Hello", "agent": "general_agent", "session_id": "..."}
                         ↓
                [Backend processes]
                         ↓
Client ←────── {"text": "Hello! How can I help?", "agent": "general_agent"}


Client ──────→ {"text": "Check my balance", "agent": "general_agent"}
                         ↓
                [Try to call tool: "balance_lookup"]
                [Call tool → get result]
                [Feed result back to LLM]
                         ↓
Client ←────── {"text": "Your balance is $...", "agent": "general_agent"}
```

### Error Handling

**Invalid Agent**:
```javascript
// Client
websocket.send(JSON.stringify({
  text: "Hello",
  agent: "nonexistent_agent"  // ❌
}))

// Server response
{"error": "Agent 'nonexistent_agent' not found"}
```

**WebSocket Disconnect**:
```python
# Server
try:
    while True:
        data = await websocket.receive_json()
        # process...
except WebSocketDisconnect:
    logger.info("Client disconnected")
except Exception as e:
    await websocket.send_json({"error": str(e)})
    await websocket.close()
```

---

## 6. KEY DIFFERENCES: ARTAgent vs ProjectK

### ARTAgent (This Framework)
✅ **What It Excels At**:
- Multi-agent orchestration with handoffs
- Industry-specific agents (banking, insurance, healthcare)
- Dynamic agent creation (Agent Builder UI)
- Comprehensive tool ecosystem (100+ tools)
- Voice orchestration (VoiceLive + SpeechCascade)
- Compliance & audit tracking
- Multi-tenant scenarios

❌ **Complexity You Don't Need**:
- Scenario Builder (industry/role selection)
- Complex handoff protocol
- MCP server integration
- Full observability stack (OpenTelemetry)
- Cosmos DB for history
- Session management system

### ProjectK (Simplified)
✅ **What You Need**:
- Single primary agent (call screener)
- Text-to-speech (respond to caller)
- Simple tool set (fraud check, lookup, escalate)
- Agent prompts with context (call history, customer risk)
- Minimal health checks

### Reusable Patterns from ARTAgent

| Pattern | Location | Reuse? | Notes |
|---------|----------|--------|-------|
| **YAML Agent Config** | agentstore/agent.yaml | ✅ Yes | Perfect for call screener persona |
| **Jinja2 Prompts** | agent.yaml system_prompt | ✅ Yes | Context-aware prompts for calls |
| **Tool Registry** | toolstore/registry.py | ✅ Yes | Simple tools for banking/fraud |
| **Voice Orchestrator** | voice/voicelive/ | ✅ Yes | Drop-in for call handling |
| **Handoff Protocol** | toolstore/handoffs.py | ⚠️ Maybe | Only if you want escalation |
| **Multi-Agent System** | registries/ + orchestration/ | ❌ No | Too complex for single agent |
| **Scenario Builder** | Agent Builder UI | ❌ No | Overkill |
| **Cosmos DB Integration** | src/cosmosdb/ | ⚠️ Maybe | Only for persistence |

### Recommended ProjectK Architecture

```
ProjectK/
├── apps/
│   ├── mobile/                    # Expo app
│   └── backend/
│       ├── main.py               # Minimal FastAPI (from ARTAgent)
│       ├── voice/
│       │   └── (inherit from ARTAgent)
│       ├── registries/
│       │   ├── agentstore/
│       │   │   ├── call_screener/
│       │   │   │   ├── agent.yaml  # 1 agent config
│       │   │   │   └── prompts/
│       │   │   │       └── system.jinja2
│       │   │   └── _defaults.yaml
│       │   └── toolstore/
│       │       ├── banking/       # Reuse from ARTAgent
│       │       ├── fraud/         # Reuse from ARTAgent
│       │       └── registry.py
│       └── config/
│           └── settings.py
├── infra/
│   └── bicep/                     # Azure IaC
└── pyproject.toml                 # Minimal deps
```

---

## SUMMARY: Architecture Diagram (Chat Flow)

```
BROWSER                          BACKEND                     AZURE
┌──────────────────┐            ┌──────────────┐           ┌─────────────┐
│  React App       │            │  FastAPI     │           │ OpenAI      │
│                  │            │              │           │ gpt-4o      │
│  [User: "Hello"] │            │              │           │             │
│        │         │            │              │           │             │
│        ├─ HTTP ──┼──────────→ │ GET /agents  │           │             │
│        │ REST    │            │ (startup)    │           │             │
│        │ (setup) │←───────────┼──────────────┤           │             │
│        │         │            │              │           │             │
│        ├─ WS ────┼──────────→ │ /realtime/   │           │             │
│        │ JSON    │            │ conversation │           │             │
│        │ (chat)  │            │   1. Load    │           │             │
│        │         │            │      agent   │           │             │
│        │         │            │   2. Render  │           │             │
│        │         │            │      prompt  │           │             │
│        │         │            │   3. Prepare │           │             │
│        │         │            │      messages│           │             │
│        │         │            │   4. Call ──┼──────────→ │ POST /chat/ │
│        │         │            │      AOAI    │           │ completions │
│        │         │            │              │           │             │
│        │         │            │              │←──────────┼─ response   │
│        │         │            │   5. Format  │           │             │
│        │         │            │      & send  │           │             │
│        │         │←───────────┼──────────────┤           │             │
│        │         │   WS JSON  │              │           │             │
│        │         │   response │              │           │             │
│        │ Chat UI │            │              │           │             │
│        ├─ Display│            │              │           │             │
│        │ message │            │              │           │             │
│        │         │            │              │           │             │
│        ├─ User   │            │              │           │             │
│        │ "Next?" │            │              │           │             │
│        │   ├─ WS─┼──────────→ │ /realtime/   │────────→ │  (repeat)   │
│        │   ...   │            │              │           │             │
│        │         │            │              │           │             │
└────────┴─────────┘            └──────────────┘           └─────────────┘
```

---

## References

- **Repository**: https://github.com/Azure-Samples/art-voice-agent-accelerator
- **Documentation**: https://aiappsgbbfactory.github.io/art-voice-agent-accelerator/
- **License**: MIT
- **Status**: Active (2025 updates; VoiceLive integration recent)

---

**Document Version**: 1.0  
**Last Updated**: May 20, 2026  
**Purpose**: ProjectK integration planning
