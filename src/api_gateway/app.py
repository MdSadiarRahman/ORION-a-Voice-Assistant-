"""
VoiceMate Laptop Agent - Core FastAPI Application.
Assembles all routers, CORS middleware, lifespan events, and interactive API documentation.
"""
from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api_config import (
    CORS_ORIGINS,
    CORS_ALLOW_CREDENTIALS,
    CORS_ALLOW_METHODS,
    CORS_ALLOW_HEADERS,
)
from .routes import voice_router, system_router, automation_router, websocket_router

logger = logging.getLogger("VoiceMate.APIGateway.App")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown procedures."""
    logger.info("Starting up VoiceMate Core FastAPI Gateway...")
    yield
    logger.info("Shutting down VoiceMate Core FastAPI Gateway...")

def create_app() -> FastAPI:
    """Factory function creating and configuring the primary FastAPI application."""
    app = FastAPI(
        title="VoiceMate Core Agent API",
        description=(
            "উচ্চক্ষমতাসম্পন্ন ডিস্ট্রিবিউটেড এপিআই গেটওয়ে ও রিয়েল-টাইম ওয়েবস্যকেট সার্ভার। "
            "Enables remote voice command execution, telemetry monitoring, n8n webhook reception, "
            "and real-time audio/event streaming."
        ),
        version="2.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan
    )

    # Enable CORS Middleware for mobile apps & web dashboards
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=CORS_ALLOW_CREDENTIALS,
        allow_methods=CORS_ALLOW_METHODS,
        allow_headers=CORS_ALLOW_HEADERS,
    )

    # Register modular routers
    app.include_router(voice_router.router)
    app.include_router(system_router.router)
    app.include_router(automation_router.router)
    app.include_router(websocket_router.router)

    @app.get("/", tags=["Root"])
    async def root():
        return {
            "name": "VoiceMate Core Agent API",
            "version": "2.0.0",
            "status": "online",
            "docs": "/docs",
            "redoc": "/redoc"
        }

    return app

# Canonical instance
app = create_app()
