# Agent ↔ Backend ↔ Frontend Communication Architecture (Chat-Only)

## Simplified Message Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SETUP PHASE (App Load)                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│ Frontend (React)                  Backend (FastAPI)      Azure Services      │
│ ============================================================================ │
│                                                                              │
│  1. App mounts                                                               │
│     └─ useEffect(() => {                                                   │
│           // Fetch agents                                                   │
│           fetch('/api/v1/agents')  ──────────→  GET /api/v1/agents          │
│                                                 Load from app.state.agents   │
│                                                 Return: [{name, desc, tools}]│
│           ←──────── [agent1, agent2, ...]                                  │
│           // Check health                                                   │
│           fetch('/api/v1/health')  ──────────→  GET /api/v1/health          │
│           ←──────── {status: "healthy"}                                     │
│        })                                                                     │
│                                                                              │
│  2. User selects agent (dropdown)                                           │
│     └─ Banking Agent selected                                               │
│                                                                              │
│  3. Show "Ready to chat" UI                                                 │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│                       CHAT PHASE (WebSocket)                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│ Frontend (React)                Backend (FastAPI)       Azure Services      │
│ ============================================================================ │
│                                                                              │
│  1. User types: "Check my balance"                                          │
│     └─ State: messages = [{role: "user", text: "..."}]                    │
│                                                                              │
│  2. Click "Send"                                                            │
│     └─ handleSendMessage(text, agentName)                                   │
│        websocket.send({                                                      │
│          "text": "Check my balance",                                        │
│          "agent": "banking_agent",                                          │
│          "session_id": "sess_xyz"                                           │
│        })                                                                     │
│                 │                                                           │
│                 │ WebSocket: WS /api/v1/realtime/conversation               │
│                 ├─────────────────────────→ @app.websocket("/api/v1/...")   │
│                 │                          │                                │
│                 │                          ├─ Accept connection             │
│                 │                          │  await ws.accept()             │
│                 │                          │                                │
│                 │                          ├─ Receive JSON                  │
│                 │                          │  data = await ws.receive_json()│
│                 │                          │                                │
│                 │                          ├─ Get agent                     │
│                 │                          │  agent = app.state.agents      │
│                 │                          │          ["banking_agent"]     │
│                 │                          │                                │
│                 │                          ├─ Load system prompt            │
│                 │                          │  prompt = load_prompt(         │
│                 │                          │    agent,                      │
│                 │                          │    context={                   │
│                 │                          │      user_name: "...",         │
│                 │                          │      account_balance: 5234.56  │
│                 │                          │    }                           │
│                 │                          │  )                             │
│                 │                          │  # Renders Jinja2 template     │
│                 │                          │                                │
│                 │                          ├─ Prepare messages              │
│                 │                          │  messages = [                  │
│                 │                          │    {"role": "system",          │
│                 │                          │     "content": prompt},        │
│                 │                          │    {"role": "user",            │
│                 │                          │     "content": "Check balance"}│
│                 │                          │  ]                             │
│                 │                          │                                │
│                 │                          ├─ Call Azure OpenAI             │
│                 │                          │  response = await             │
│                 │                          │    aoai_client.chat.           │
│                 │                          │    completions.create(         │
│                 │                          │      model="gpt-4o",           │
│                 │                          │      messages=messages,        │
│                 │                          │      temperature=0.7,          │
│                 │                          │      max_tokens=1000           │
│                 │                          │    )                           │
│                 │                          │  ──────────────→ OpenAI       │
│                 │                          │                 Process       │
│                 │                          │                 Generate      │
│                 │                          │  ←────────────── Response     │
│                 │                          │                                │
│                 │                          ├─ Extract response              │
│                 │                          │  reply = response.choices[0]   │
│                 │                          │    .message.content            │
│                 │                          │  # = "Your balance is $5234..." │
│                 │                          │                                │
│                 │                          ├─ Send back JSON                │
│                 │                          │  await ws.send_json({         │
│                 │                          │    "text": reply,              │
│                 │                          │    "agent": "banking_agent",   │
│                 │                          │    "session_id": "sess_xyz"    │
│                 │                          │  })                            │
│                 │                          │                                │
│  3. Receive JSON response                 │  │                             │
│     {"text": "Your balance...",                                             │
│      "agent": "banking_agent"}             │  │                             │
│     ←──────────────────────────────────────┘  │                             │
│                                                │                             │
│  4. Update state                                                            │
│     messages = [                                                            │
│       {role: "user", text: "Check balance"},                               │
│       {role: "assistant", text: "Your balance..."}                         │
│     ]                                                                       │
│                                                                              │
│  5. Render chat UI                                                         │
│     ┌──────────────────────────────────┐                                   │
│     │ You: Check my balance            │                                   │
│     │ Agent: Your balance is $5234.56  │                                   │
│     │                                  │                                   │
│     │ [Type message...] [Send]         │                                   │
│     └──────────────────────────────────┘                                   │
│                                                                              │
│  6. User sends next message → Loop back to step 2                           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│                         CLEANUP PHASE (Disconnect)                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│ Frontend (React)                Backend (FastAPI)                           │
│ ============================================================================ │
│                                                                              │
│  User closes tab / clicks "End Call"                                        │
│  └─ websocket.close()                                                       │
│     │                                                                       │
│     └─ WebSocket close frame ──────→ @app.websocket() finally block         │
│                                       logger.info("Client disconnected")    │
│                                       await ws.close()                      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Per-Request Lifecycle Detail

### Request: User sends "Check balance"

**Timing** (~500-800ms total):
- Frontend→Backend: 10ms (network)
- Backend processing: 50ms (load agent, render prompt)
- Backend→Azure: 100ms (AOAI API call start)
- Azure processing: 300-500ms (LLM inference, token generation)
- Azure→Backend: 50ms (response streaming/completion)
- Backend→Frontend: 10ms (send JSON)
- Frontend render: 20ms (React update)

**Total**: ~500-700ms (user perceives as "instant")

---

## Agent Configuration Lookup

```
User sends: {"agent": "banking_agent", ...}
                │
                ├─ app.state.agents["banking_agent"]
                │  └─ UnifiedAgent(
                │       name="banking_agent",
                │       description="...",
                │       model=ModelConfig(
                │         deployment_id="gpt-4o",
                │         temperature=0.7,
                │         max_tokens=1000
                │       ),
                │       voice=VoiceConfig(
                │         current_voice="en-US-AvaMultilingualNeural"
                │       ),
                │       tools=["account_lookup", "balance_check", "escalate"],
                │       system_prompt="You are a banking specialist...\n"
                │                      "Customer: {{ user_name }}\n"
                │                      "Balance: {{ balance }}"
                │     )
                │
                └─ load_prompt(agent, context={
                     user_name="Alice Brown",
                     balance=5234.56
                   })
                   └─ Render Jinja2 template
                      Result: "You are a banking specialist...\n"
                              "Customer: Alice Brown\n"
                              "Balance: 5234.56"
```

---

## JSON Message Schemas

### Frontend → Backend (WebSocket Send)

```json
{
  "text": "Check my balance",
  "agent": "banking_agent",
  "session_id": "sess_12345",  // optional
  "metadata": {}                // optional
}
```

**Required**: `text`, `agent`  
**Optional**: `session_id`, other fields

### Backend → Frontend (WebSocket Response)

```json
{
  "text": "Your current balance is $5,234.56...",
  "agent": "banking_agent",
  "session_id": "sess_12345",
  "timestamp": "2025-05-20T14:30:45Z"
}
```

### Error Response

```json
{
  "error": "Agent 'unknown_agent' not found",
  "status_code": 404
}
```

---

## Core Code References

### Frontend (src/components/RealTimeVoiceApp.jsx)

```jsx
// WebSocket initialization
const [websocket, setWebsocket] = useState(null);
const [messages, setMessages] = useState([]);

useEffect(() => {
  const ws = new WebSocket(`${WS_URL}/api/v1/realtime/conversation`);
  
  ws.onopen = () => console.log("Connected");
  
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    setMessages(prev => [...prev, {
      role: "assistant",
      text: data.text,
      agent: data.agent
    }]);
  };
  
  ws.onerror = (error) => console.error("WebSocket error:", error);
  
  setWebsocket(ws);
  
  return () => ws.close();
}, []);

// Send message
const handleSendMessage = (text, agentName) => {
  websocket.send(JSON.stringify({
    text,
    agent: agentName,
    session_id: currentSessionId
  }));
  
  setMessages(prev => [...prev, {
    role: "user",
    text
  }]);
};
```

### Backend (apps/artagent/backend/main.py)

```python
@app.websocket("/api/v1/realtime/conversation")
async def websocket_conversation(websocket: WebSocket):
    await websocket.accept()
    
    try:
        while True:
            # Receive
            data = await websocket.receive_json()
            text = data.get("text", "")
            agent_name = data.get("agent", "general_agent")
            
            # Load agent
            agent = app.state.agents[agent_name]
            
            # Render prompt
            from registries.agentstore.loader import load_prompt
            system_prompt = load_prompt(agent, {
                "user_name": "User",
                "session_id": data.get("session_id")
            })
            
            # Call AOAI
            response = await app.state.aoai_client.chat.completions.create(
                model=agent.model.deployment_id,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ],
                temperature=agent.model.temperature,
                max_tokens=agent.model.max_tokens
            )
            
            # Send back
            await websocket.send_json({
                "text": response.choices[0].message.content,
                "agent": agent_name,
                "session_id": data.get("session_id")
            })
    
    except Exception as e:
        await websocket.send_json({"error": str(e)})
    finally:
        await websocket.close()
```

### Agent YAML (apps/artagent/backend/registries/agentstore/banking_agent/agent.yaml)

```yaml
name: banking_agent
description: "Banking assistant for account inquiries"

model:
  deployment_id: gpt-4o
  temperature: 0.7
  max_tokens: 1000

voice:
  current_voice: "en-US-AvaMultilingualNeural"

tools:
  - account_lookup
  - balance_check
  - transaction_history
  - escalate_to_human

system_prompt: |
  You are a professional banking assistant for {{ company_name }}.
  
  Customer Information:
  - Name: {{ user_name }}
  - Account Number: {{ account_id }}
  - Risk Level: {{ risk_level }}
  
  You can:
  1. Check account balance and status
  2. Review recent transactions
  3. Explain fees and policies
  4. Escalate to a human agent
  
  Always be polite and thorough. Never share full account numbers in responses.
```

---

## Minimal Dependency Tree

```
Project K Backend
├── Framework
│   ├── fastapi (web)
│   ├── uvicorn (ASGI server)
│   └── pydantic (validation)
├── Azure
│   ├── azure-openai (LLM)
│   ├── azure-identity (auth)
│   └── azure-cognitiveservices-speech (STT/TTS, if voice)
├── Config
│   ├── pyyaml (agent YAML parsing)
│   ├── jinja2 (prompt templating)
│   └── python-dotenv (env vars)
└── Infrastructure (optional)
    ├── redis (session cache)
    ├── opentelemetry (observability)
    └── azure-monitor-opentelemetry (Azure logging)
```

**Total minimal**: ~12 packages  
**With voice**: +2 packages  
**With logging**: +3 packages  
**With persistence**: +2 packages

