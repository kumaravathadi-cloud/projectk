# ProjectK Setup Checklist

Before you can test the chat, complete these steps:

## ✅ Step 1: Python Environment

- [ ] Python 3.11+ installed
  ```bash
  python --version
  ```
  
- [ ] Virtual environment created (optional but recommended)
  ```bash
  python -m venv venv
  source venv/bin/activate  # On Windows: venv\Scripts\activate
  ```

## ✅ Step 2: Install Dependencies

- [ ] Install project in editable mode
  ```bash
  cd /Users/vksvarma/Desktop/ProjectK
  pip install -e .
  ```
  
- [ ] Verify installation
  ```bash
  pip list | grep fastapi
  pip list | grep azure-openai
  ```

## ✅ Step 3: Azure Setup

- [ ] Azure Subscription access
- [ ] Create/access Azure OpenAI resource
- [ ] Verify deployment named `gpt-4o` exists
- [ ] Get API Key and Endpoint from Portal

## ✅ Step 4: Environment Configuration

- [ ] Copy `.env.example` to `.env`
  ```bash
  cp .env.example .env
  ```
  
- [ ] Edit `.env` with your Azure credentials:
  - `AZURE_OPENAI_API_KEY` = (your key)
  - `AZURE_OPENAI_ENDPOINT` = (your endpoint)
  
- [ ] Verify `.env` is in the project root
  ```bash
  ls -la .env
  ```

## ✅ Step 5: Start Backend Server

- [ ] Navigate to backend directory
  ```bash
  cd apps/backend
  ```
  
- [ ] Start the server
  ```bash
  python main.py
  ```
  
- [ ] Verify startup messages:
  - `✅ Agents loaded: ['call_screener']`
  - `✅ Azure OpenAI client ready`
  - `Uvicorn running on http://0.0.0.0:8000`

## ✅ Step 6: Test Endpoints

- [ ] Health check
  ```bash
  curl http://localhost:8000/api/v1/health
  ```
  
- [ ] List agents
  ```bash
  curl http://localhost:8000/api/v1/agents
  ```
  
- [ ] API docs (open in browser)
  - http://localhost:8000/docs

## ✅ Step 7: Test WebSocket Chat

Use one of these methods:

### Option A: Python Script (test_chat.py)

```python
import asyncio
import websockets
import json

async def test_chat():
    uri = "ws://localhost:8000/api/v1/realtime/conversation"
    async with websockets.connect(uri) as ws:
        message = {
            "text": "Hello, can you help me?",
            "agent": "call_screener",
            "context": {
                "caller_phone": "+1-555-1234",
                "customer_name": "John Doe",
                "risk_level": "low",
                "interaction_id": "test_001",
                "company_name": "ProjectK Inc"
            }
        }
        
        await ws.send(json.dumps(message))
        response = await ws.recv()
        print("Response:", json.loads(response))

asyncio.run(test_chat())
```

Run with:
```bash
pip install websockets
python test_chat.py
```

### Option B: Browser Console

Open http://localhost:8000/docs and test the WebSocket endpoint using Swagger UI.

---

## 🔍 Verification

Once all steps complete, you should see:

1. **Server Output:**
   ```
   ✨ PROJECTK BACKEND READY
   INFO:     Uvicorn running on http://0.0.0.0:8000
   ```

2. **Health Check Response:**
   ```json
   {
     "status": "healthy",
     "service": "ProjectK Call Screening",
     "version": "1.0.0"
   }
   ```

3. **WebSocket Response:**
   ```json
   {
     "text": "Hello! Thank you for calling ProjectK Inc. How can I assist you today?",
     "agent": "call_screener",
     "interaction_id": "test_001"
   }
   ```

---

## 🆘 If Something Goes Wrong

### Check these first:

1. **Server not starting?**
   - Check Python version: `python --version`
   - Check dependencies installed: `pip list`
   - Check `.env` file exists and is readable
   - Check port 8000 is free: `lsof -i :8000`

2. **Module not found error?**
   - Make sure you're in the project root: `pwd`
   - Reinstall: `pip install -e .`
   - Check Python path: `python -c "import sys; print(sys.path)"`

3. **Azure auth error?**
   - Double-check credentials in `.env`
   - Test in Azure Portal directly
   - Check API key hasn't expired

4. **WebSocket connection refused?**
   - Ensure server is running (should see in terminal)
   - Check firewall/network settings
   - Try `http://localhost:8000/docs` in browser (should load)

5. **No response from OpenAI?**
   - Verify Azure OpenAI deployment exists
   - Check Azure subscription has available quota
   - Look at server logs for detailed errors

---

## 📞 Contact

If stuck, provide:
1. Full error message from terminal
2. Output of `pip list`
3. Contents of `.env` (hide sensitive parts)
4. Output of `curl http://localhost:8000/health`

---

**Status:** 🟢 Ready to start testing once checklist complete
