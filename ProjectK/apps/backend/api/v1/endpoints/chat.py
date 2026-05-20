"""WebSocket chat endpoint for call screening."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from openai import AsyncAzureOpenAI
import json
import logging
from datetime import datetime
from typing import Optional
from registries.agentstore.loader import get_agent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["chat"])


@router.websocket("/realtime/conversation")
async def websocket_chat(websocket: WebSocket):
    """
    WebSocket endpoint for chat interaction with call screener agent.
    
    Expected message format from client:
    {
        "text": "user message",
        "agent": "call_screener",
        "context": {
            "caller_phone": "+1234567890",
            "customer_name": "John Doe",
            "risk_level": "low",
            "interaction_id": "call_123"
        }
    }
    
    Response format:
    {
        "text": "agent response",
        "agent": "call_screener",
        "interaction_id": "call_123"
    }
    """
    await websocket.accept()
    
    # Get app state
    agents = websocket.app.state.agents or {}
    aoai_client: AsyncAzureOpenAI = websocket.app.state.aoai_client
    
    conversation_history = []
    current_agent_name = "call_screener"
    interaction_context = {}
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            user_message = data.get("text", "")
            current_agent_name = data.get("agent", "call_screener")
            interaction_context = data.get("context", {})
            interaction_id = interaction_context.get("interaction_id", "unknown")
            
            logger.info(
                f"📨 Received message from {interaction_id}: {user_message[:50]}..."
            )
            
            # Validate agent exists
            if current_agent_name not in agents:
                error_msg = f"Agent '{current_agent_name}' not found"
                logger.error(error_msg)
                await websocket.send_json({
                    "error": error_msg,
                    "interaction_id": interaction_id,
                })
                continue
            
            # Get agent config
            agent = get_agent(agents, current_agent_name)
            
            # Build context for prompt rendering
            render_context = {
                "company_name": interaction_context.get("company_name", "Our Company"),
                "caller_phone": interaction_context.get("caller_phone", "Unknown"),
                "customer_name": interaction_context.get("customer_name", "Valued Customer"),
                "risk_level": interaction_context.get("risk_level", "medium"),
                "interaction_id": interaction_id,
                "current_date": datetime.now().strftime("%Y-%m-%d"),
                "call_started_at": interaction_context.get("call_started_at", ""),
            }
            
            # Render system prompt
            try:
                system_prompt = agent.render_prompt(render_context)
            except Exception as e:
                logger.error(f"Failed to render prompt: {e}")
                system_prompt = agent.prompt_template
            
            # Add user message to conversation
            conversation_history.append({
                "role": "user",
                "content": user_message,
            })
            
            # Call Azure OpenAI
            try:
                logger.info(f"🔄 Calling Azure OpenAI for {interaction_id}...")
                
                response = await aoai_client.chat.completions.create(
                    model=agent.model.deployment_id,
                    messages=[
                        {
                            "role": "system",
                            "content": system_prompt,
                        },
                        *conversation_history,
                    ],
                    temperature=agent.model.temperature,
                    max_tokens=agent.model.max_tokens,
                )
                
                assistant_message = response.choices[0].message.content
                
                # Add assistant response to history
                conversation_history.append({
                    "role": "assistant",
                    "content": assistant_message,
                })
                
                logger.info(
                    f"✅ Got response for {interaction_id}: {assistant_message[:50]}..."
                )
                
                # Send response back to client
                await websocket.send_json({
                    "text": assistant_message,
                    "agent": current_agent_name,
                    "interaction_id": interaction_id,
                })
                
            except Exception as e:
                logger.error(f"❌ OpenAI API error: {e}")
                error_response = f"I encountered an error. Please try again. Error: {str(e)}"
                await websocket.send_json({
                    "error": error_response,
                    "interaction_id": interaction_id,
                })
    
    except WebSocketDisconnect:
        logger.info(f"👋 Client disconnected from {interaction_id}")
    except Exception as e:
        logger.error(f"❌ WebSocket error: {e}")
        try:
            await websocket.send_json({
                "error": f"Unexpected error: {str(e)}",
            })
        except:
            pass
