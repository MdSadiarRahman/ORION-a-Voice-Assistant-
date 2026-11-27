"""
VoiceMate Laptop Agent - FastAPI Gateway Configuration Module.
Central configuration for VoiceMate's high-performance REST API and WebSocket server.
"""
import os
import socket
from pathlib import Path
from typing import List

# FastAPI Server Configuration
FASTAPI_REPO_DIR = Path(__file__).resolve().parent

# Server Network Configuration
API_HOST = os.getenv("VOICEMATE_API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("VOICEMATE_API_PORT", "8080"))
API_RELOAD = os.getenv("VOICEMATE_API_RELOAD", "false").lower() == "true"
API_AUTO_OPEN_DOCS = os.getenv("VOICEMATE_API_AUTO_OPEN_DOCS", "true").lower() == "true"

# CORS configuration
CORS_ORIGINS: List[str] = ["*"]
CORS_ALLOW_CREDENTIALS: bool = True
CORS_ALLOW_METHODS: List[str] = ["*"]
CORS_ALLOW_HEADERS: List[str] = ["*"]

# Endpoints
API_BASE_URL = f"http://{API_HOST}:{API_PORT}"
API_DOCS_URL = f"http://{API_HOST}:{API_PORT}/docs"
API_REDOC_URL = f"http://{API_HOST}:{API_PORT}/redoc"
API_OPENAPI_URL = f"http://{API_HOST}:{API_PORT}/openapi.json"

def is_port_in_use(port: int, host: str = API_HOST) -> bool:
    """Checks whether the target TCP port is currently in use."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            return s.connect_ex((host, port)) == 0
    except Exception:
        return False

def is_api_server_running() -> bool:
    """Checks if VoiceMate FastAPI server is actively responding on its port."""
    return is_port_in_use(API_PORT, API_HOST)
