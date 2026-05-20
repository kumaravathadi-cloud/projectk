"""Health check endpoints."""

from fastapi import APIRouter, Request
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["health"])


@router.get("/health")
async def health_check(request: Request):
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "ProjectK Call Screening",
        "version": "1.0.0",
    }


@router.get("/ready")
async def readiness_check(request: Request):
    """Readiness check - returns 200 only if fully initialized."""
    agents = request.app.state.agents
    if not agents:
        return {"status": "not_ready", "reason": "Agents not loaded"}, 503
    
    return {
        "status": "ready",
        "agents_loaded": len(agents),
        "available_agents": list(agents.keys()),
    }


@router.get("/agents")
async def list_agents(request: Request):
    """List all available agents."""
    agents = request.app.state.agents or {}
    return {
        "agents": [
            {
                "name": agent.name,
                "description": agent.description,
                "greeting": agent.greeting,
                "tools": agent.tools,
            }
            for agent in agents.values()
        ]
    }
