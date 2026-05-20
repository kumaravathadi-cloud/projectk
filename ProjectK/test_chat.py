#!/usr/bin/env python
"""
ProjectK Chat Test Script

Tests the backend WebSocket chat endpoint locally.
Run this after the backend server is started.

Usage:
    python test_chat.py
"""

import asyncio
import json
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))


async def test_websocket_chat():
    """Test WebSocket chat endpoint."""
    try:
        import websockets
    except ImportError:
        print("❌ websockets library not found")
        print("   Install with: pip install websockets")
        return False
    
    uri = "ws://localhost:8000/api/v1/realtime/conversation"
    
    print("\n" + "=" * 70)
    print("🧪 PROJECTK CHAT TEST")
    print("=" * 70)
    print(f"Connecting to: {uri}\n")
    
    try:
        async with websockets.connect(uri) as ws:
            print("✅ WebSocket connected!")
            
            # Test message
            message = {
                "text": "Hello! I have a question about my account.",
                "agent": "call_screener",
                "context": {
                    "caller_phone": "+1-555-123-4567",
                    "customer_name": "John Doe",
                    "risk_level": "low",
                    "interaction_id": "test_001",
                    "company_name": "ProjectK Inc"
                }
            }
            
            print("\n📤 Sending message:")
            print(f"   Text: {message['text']}")
            print(f"   Agent: {message['agent']}")
            print(f"   Context: {json.dumps(message['context'], indent=6)}")
            
            # Send message
            await ws.send(json.dumps(message))
            print("\n⏳ Waiting for response...")
            
            # Receive response
            response = await ws.recv()
            data = json.loads(response)
            
            print("\n✅ Received response!")
            print(f"   Agent: {data.get('agent')}")
            print(f"   Interaction ID: {data.get('interaction_id')}")
            print(f"   Response: {data.get('text')}")
            
            if "error" in data:
                print(f"\n❌ Error: {data['error']}")
                return False
            
            print("\n" + "=" * 70)
            print("✨ TEST PASSED!")
            print("=" * 70)
            print("\nChat interaction is working. You can now:")
            print("  1. Build a frontend UI")
            print("  2. Test more complex conversations")
            print("  3. Add more agents")
            print("  4. Integrate tools")
            print("=" * 70 + "\n")
            
            return True
    
    except ConnectionRefusedError:
        print("❌ Connection refused!")
        print("\nMake sure the backend server is running:")
        print("  cd apps/backend")
        print("  python main.py")
        return False
    
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON response: {e}")
        return False
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_rest_endpoints():
    """Test REST endpoints."""
    try:
        import aiohttp
    except ImportError:
        print("⚠️  aiohttp not found, skipping REST tests")
        return True
    
    print("\n" + "=" * 70)
    print("🔍 Testing REST Endpoints")
    print("=" * 70)
    
    base_url = "http://localhost:8000"
    endpoints = [
        ("Health Check", "/api/v1/health"),
        ("Readiness Check", "/api/v1/ready"),
        ("List Agents", "/api/v1/agents"),
    ]
    
    try:
        async with aiohttp.ClientSession() as session:
            for name, path in endpoints:
                try:
                    url = base_url + path
                    async with session.get(url) as resp:
                        data = await resp.json()
                        status = "✅" if resp.status == 200 else "⚠️ "
                        print(f"\n{status} {name} ({resp.status})")
                        print(f"   Response: {json.dumps(data, indent=4)}")
                except Exception as e:
                    print(f"\n❌ {name} failed: {e}")
    
    except Exception as e:
        print(f"⚠️  Could not test REST endpoints: {e}")
        return False
    
    return True


async def main():
    """Main test function."""
    print("\n🚀 ProjectK Backend Test Suite\n")
    
    # Test REST endpoints
    rest_ok = await test_rest_endpoints()
    
    # Test WebSocket chat
    ws_ok = await test_websocket_chat()
    
    # Summary
    if rest_ok and ws_ok:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
