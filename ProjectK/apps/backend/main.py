"""
ProjectK Backend - Call Screening Chat Service

Main entry point for the FastAPI application.
Minimal, chat-focused implementation without deployment infrastructure.
"""

import os
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Import app components
from registries.agentstore.loader import discover_agents
from registries.toolstore.registry import initialize_tools
from api.v1.endpoints.health import router as health_router
from api.v1.endpoints.chat import router as chat_router


# ═══════════════════════════════════════════════════════════════════════════
# LIFESPAN - Startup & Shutdown
# ═══════════════════════════════════════════════════════════════════════════

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown."""
    
    # ─────────────────────────────────────────────────────────────────────
    # STARTUP
    # ─────────────────────────────────────────────────────────────────────
    logger.info("=" * 70)
    logger.info("🚀 PROJECTK BACKEND STARTUP")
    logger.info("=" * 70)
    
    try:
        # 1. Load agents
        logger.info("📦 Loading agents...")
        agents = discover_agents()
        if not agents:
            logger.warning("⚠️  No agents found!")
        app.state.agents = agents
        logger.info(f"✅ Agents loaded: {list(agents.keys())}")
        
        # 2. Initialize tools
        logger.info("🔧 Initializing tools...")
        initialize_tools()
        logger.info("✅ Tools initialized")
        
        # 3. Initialize Azure OpenAI
        logger.info("🤖 Initializing Azure OpenAI...")
        from openai import AsyncAzureOpenAI
        
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        
        if not api_key or not endpoint:
            logger.warning("⚠️  AZURE_OPENAI_API_KEY or AZURE_OPENAI_ENDPOINT not set")
            logger.warning("   Chat will not work until these are configured")
            app.state.aoai_client = None
        else:
            app.state.aoai_client = AsyncAzureOpenAI(
                api_key=api_key,
                api_version="2024-08-01-preview",
                azure_endpoint=endpoint,
            )
            logger.info("✅ Azure OpenAI client ready")
        
        # 4. Optional: Initialize Redis (for session management)
        logger.info("💾 Initializing Redis (optional)...")
        try:
            import redis.asyncio as redis
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
            app.state.redis = await redis.from_url(redis_url)
            await app.state.redis.ping()
            logger.info(f"✅ Redis connected: {redis_url}")
        except Exception as e:
            logger.warning(f"⚠️  Redis unavailable: {e}")
            logger.warning("   Session storage disabled (OK for local testing)")
            app.state.redis = None
        
        logger.info("=" * 70)
        logger.info("✨ PROJECTK BACKEND READY")
        logger.info("=" * 70)
        
    except Exception as e:
        logger.error(f"❌ STARTUP FAILED: {e}", exc_info=True)
        raise
    
    # Application runs here (yield)
    yield
    
    # ─────────────────────────────────────────────────────────────────────
    # SHUTDOWN
    # ─────────────────────────────────────────────────────────────────────
    logger.info("🛑 PROJECTK BACKEND SHUTDOWN")
    
    try:
        if hasattr(app.state, "redis") and app.state.redis:
            await app.state.redis.close()
            logger.info("✅ Redis closed")
    except Exception as e:
        logger.error(f"Error closing Redis: {e}")


# ═══════════════════════════════════════════════════════════════════════════
# APP CREATION
# ═══════════════════════════════════════════════════════════════════════════

app = FastAPI(
    title="ProjectK Call Screening API",
    description="Minimal chat-based call screening service",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (configure as needed)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ═══════════════════════════════════════════════════════════════════════════
# ROUTES
# ═══════════════════════════════════════════════════════════════════════════

# Health & info endpoints
app.include_router(health_router)

# Chat endpoints
app.include_router(chat_router)


# ═══════════════════════════════════════════════════════════════════════════
# ROOT
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "service": "ProjectK Call Screening",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/health",
        "endpoints": {
            "health": "GET /api/v1/health",
            "ready": "GET /api/v1/ready",
            "agents": "GET /api/v1/agents",
            "chat": "WebSocket /api/v1/realtime/conversation",
        },
    }


# ═══════════════════════════════════════════════════════════════════════════
# RUN
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    reload = os.getenv("ENV", "dev") == "dev"
    
    logger.info(f"Starting server at http://{host}:{port}")
    logger.info(f"API docs at http://localhost:{port}/docs")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
    )
