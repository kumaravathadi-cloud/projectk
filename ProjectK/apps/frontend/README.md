# ProjectK Web UI

Simple chat interface for the ProjectK AI call screening backend.

## Quick Start

### 1. Start the Backend (Terminal 1)
```bash
cd /Users/vksvarma/Desktop/ProjectK/apps/backend
python3 main.py
```

### 2. Run the Web UI (Terminal 2)
```bash
cd /Users/vksvarma/Desktop/ProjectK/apps/frontend
python3 -m http.server 3000
```

### 3. Open in Browser
```
http://localhost:3000
```

## Features

✅ Real-time Chat via WebSocket
✅ Context Configuration (caller info, company, risk level)
✅ Typing Indicator
✅ Auto-reconnect
✅ Clean, responsive UI

## How to Use

1. Configure caller details (optional)
2. Type your message
3. Get AI response from backend agent
"""

# Frontend structure to be built:
# - src/
#   - components/
#     - ChatInterface.tsx
#     - MessageList.tsx
#     - InputBox.tsx
#   - hooks/
#     - useWebSocket.ts
#   - App.tsx
#   - main.tsx
