"""
Configuration settings for VoiceMate Laptop Agent.
"""
import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
CONFIG_DIR = BASE_DIR / "config"
CAPTURES_DIR = BASE_DIR / "captures"
DOCS_DIR = BASE_DIR / "documents"

# External Repository Integration Paths Helper
def resolve_repo_path(names: list, fallback: Path) -> Path:
    r"""Dynamically resolves repository paths from D:\Git hub resources or fallback."""
    candidate_roots = [
        Path(r"D:\Git hub resources"),
        BASE_DIR.parent / "Git hub resources",
        BASE_DIR.parent / "VoiceMate Repo Help",
    ]
    for root in candidate_roots:
        if not root.exists():
            continue
        for name in names:
            patterns = [
                root / f"{name}-main" / f"{name}-main",
                root / f"{name}-master" / f"{name}-master",
                root / name / name,
                root / f"{name}-main",
                root / f"{name}-master",
                root / name,
            ]
            for p in patterns:
                if p.exists():
                    return p
    return fallback

SCRAPEGRAPH_AI_REPO_DIR = resolve_repo_path(["Scrapegraph-ai", "scrapegraphai", "Scrapegraph-ai-main"], BASE_DIR.parent / "VoiceMate Repo Help" / "Scrapegraph-ai")
BROWSER_USE_REPO_DIR = resolve_repo_path(["browser-use", "browser_use"], BASE_DIR.parent / "VoiceMate Repo Help" / "browser-use")
PYMUPDF_REPO_DIR = resolve_repo_path(["PyMuPDF", "pymupdf"], BASE_DIR.parent / "VoiceMate Repo Help" / "PyMuPDF")
PLAYWRIGHT_REPO_DIR = resolve_repo_path(["playwright-python", "playwright"], BASE_DIR.parent / "VoiceMate Repo Help" / "playwright-python")
OPENHANDS_REPO_DIR = resolve_repo_path(["OpenHands", "openhands"], BASE_DIR.parent / "VoiceMate Repo Help" / "OpenHands")
AIDER_REPO_DIR = resolve_repo_path(["aider"], BASE_DIR.parent / "VoiceMate Repo Help" / "aider")
DOCLING_REPO_DIR = resolve_repo_path(["docling"], BASE_DIR.parent / "VoiceMate Repo Help" / "docling")
N8N_REPO_DIR = resolve_repo_path(["n8n"], BASE_DIR.parent / "VoiceMate Repo Help" / "n8n")
LANGGRAPH_REPO_DIR = resolve_repo_path(["langgraph"], BASE_DIR.parent / "VoiceMate Repo Help" / "langgraph")
AGENCY_AGENTS_REPO_DIR = resolve_repo_path(["agency-agents", "agency_agents"], BASE_DIR.parent / "VoiceMate Repo Help" / "agency-agents")
SOFTWARE_AGENT_SDK_REPO_DIR = resolve_repo_path(["software-agent-sdk"], BASE_DIR.parent / "VoiceMate Repo Help" / "software-agent-sdk")
VOSK_API_REPO_DIR = resolve_repo_path(["vosk-api", "vosk"], BASE_DIR.parent / "VoiceMate Repo Help" / "vosk-api")
TAKEOUT_ASSISTANT_REPO_DIR = resolve_repo_path(["takeout_assistant", "takeout-assistant"], BASE_DIR.parent / "VoiceMate Repo Help" / "takeout_assistant")
OFFLINE_VOICE_AI_REPO_DIR = resolve_repo_path(["offline-voice-ai"], BASE_DIR.parent / "VoiceMate Repo Help" / "offline-voice-ai")

PLAYWRIGHT_PROFILES_DIR = DATA_DIR / "playwright_profiles"
PLAYWRIGHT_SCREENSHOTS_DIR = CAPTURES_DIR / "web_screenshots"
CODER_BACKUPS_DIR = DATA_DIR / "code_backups"
DOCLING_OUTPUT_DIR = DATA_DIR / "docling_exports"
N8N_WORKFLOWS_DIR = DATA_DIR / "n8n_workflows"
CANVAS_WORKSPACE_DIR = BASE_DIR

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
CONFIG_DIR.mkdir(exist_ok=True)
CAPTURES_DIR.mkdir(exist_ok=True)
DOCS_DIR.mkdir(exist_ok=True)
PLAYWRIGHT_PROFILES_DIR.mkdir(exist_ok=True)
PLAYWRIGHT_SCREENSHOTS_DIR.mkdir(exist_ok=True)
CODER_BACKUPS_DIR.mkdir(exist_ok=True)
DOCLING_OUTPUT_DIR.mkdir(exist_ok=True)
N8N_WORKFLOWS_DIR.mkdir(exist_ok=True)

CONTACTS_FILE = DATA_DIR / "contacts.json"
PREFERENCES_FILE = DATA_DIR / "app_preferences.json"

# Voice & Language Settings
DEFAULT_LANGUAGE = "bn-BD"
SECONDARY_LANGUAGE = "en-US"
TTS_RATE = 160  # Words per minute
TTS_VOLUME = 1.0

# Battery Monitoring Settings
BATTERY_CHECK_INTERVAL_SECONDS = 60
LOW_BATTERY_THRESHOLD = 20

# Browser-Use Autonomous Agent Settings
BROWSER_USE_ENABLED = True
BROWSER_TYPE = os.getenv("VOICEMATE_BROWSER_TYPE", "chrome")  # 'chrome' or 'chromium'
BROWSER_HEADLESS = os.getenv("VOICEMATE_BROWSER_HEADLESS", "false").lower() == "true"
BROWSER_TIMEOUT_SECONDS = int(os.getenv("VOICEMATE_BROWSER_TIMEOUT", "90"))
BROWSER_LLM_MODEL = os.getenv("VOICEMATE_BROWSER_MODEL", "gpt-4o")

# Document Intelligence (PyMuPDF) Settings
DOCUMENT_RENDER_DPI = 150
DOCUMENT_MAX_VOICE_CHARS = 1200
DOCUMENT_SUPPORTED_EXTS = (".pdf", ".xps", ".epub", ".mobi", ".fb2", ".cbz", ".svg", ".txt", ".md")

# Deterministic Browser Automation (Playwright) Settings
PLAYWRIGHT_ENABLED = True
PLAYWRIGHT_DEFAULT_BROWSER = os.getenv("VOICEMATE_PLAYWRIGHT_BROWSER", "chromium")  # 'chromium', 'firefox', 'webkit'
PLAYWRIGHT_HEADLESS = os.getenv("VOICEMATE_PLAYWRIGHT_HEADLESS", "false").lower() == "true"
PLAYWRIGHT_TIMEOUT_MS = int(os.getenv("VOICEMATE_PLAYWRIGHT_TIMEOUT_MS", "30000"))
PLAYWRIGHT_SLOW_MO_MS = int(os.getenv("VOICEMATE_PLAYWRIGHT_SLOW_MO_MS", "50"))

# OpenHands Agent Canvas & Developer Control Center Settings
CANVAS_ENABLED = True
CANVAS_PORT = int(os.getenv("VOICEMATE_CANVAS_PORT", "8000"))
CANVAS_AGENT_SERVER_PORT = int(os.getenv("VOICEMATE_AGENT_SERVER_PORT", "18000"))
CANVAS_AUTOMATION_PORT = int(os.getenv("VOICEMATE_CANVAS_AUTOMATION_PORT", "18001"))
CANVAS_AUTO_OPEN_BROWSER = os.getenv("VOICEMATE_CANVAS_AUTO_OPEN", "true").lower() == "true"

# AI Pair Programming & Code Editing (Aider) Settings
CODER_ENABLED = True
CODER_AUTO_COMMIT = os.getenv("VOICEMATE_CODER_AUTO_COMMIT", "true").lower() == "true"
CODER_MAX_MAP_TOKENS = int(os.getenv("VOICEMATE_CODER_MAX_MAP_TOKENS", "1024"))

# Multimodal Document Parsing & RAG Chunking (Docling) Settings
DOCLING_ENABLED = True
DOCLING_DO_OCR = os.getenv("VOICEMATE_DOCLING_OCR", "true").lower() == "true"
DOCLING_DO_TABLES = os.getenv("VOICEMATE_DOCLING_TABLES", "true").lower() == "true"
DOCLING_CHUNK_MAX_TOKENS = int(os.getenv("VOICEMATE_DOCLING_CHUNK_TOKENS", "512"))
DOCLING_SUPPORTED_EXTS = (".pdf", ".docx", ".pptx", ".xlsx", ".html", ".epub", ".csv", ".txt", ".md")

# n8n Enterprise & AI Workflow Automation Settings
N8N_ENABLED = True
N8N_PORT = int(os.getenv("VOICEMATE_N8N_PORT", "5678"))
N8N_WEBHOOK_URL = os.getenv("VOICEMATE_N8N_WEBHOOK_URL", "http://localhost:5678/webhook/voicemate-action")
N8N_TIMEOUT_SECONDS = int(os.getenv("VOICEMATE_N8N_TIMEOUT", "15"))
N8N_AUTO_OPEN_BROWSER = os.getenv("VOICEMATE_N8N_AUTO_OPEN", "true").lower() == "true"

# FastAPI Gateway & Real-Time WebSocket Server Settings
API_GATEWAY_ENABLED = True
API_HOST = os.getenv("VOICEMATE_API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("VOICEMATE_API_PORT", "8080"))
API_AUTO_START = os.getenv("VOICEMATE_API_AUTO_START", "false").lower() == "true"
API_AUTO_OPEN_DOCS = os.getenv("VOICEMATE_API_AUTO_OPEN_DOCS", "true").lower() == "true"

# LangGraph Master Brain & Multi-Agent Orchestrator Settings
BRAIN_ENABLED = True
BRAIN_SESSION_ID = os.getenv("VOICEMATE_BRAIN_SESSION_ID", "voicemate_desktop_session")
BRAIN_MAX_RETRIES = int(os.getenv("VOICEMATE_BRAIN_MAX_RETRIES", "2"))
BRAIN_SELF_CORRECTION = os.getenv("VOICEMATE_BRAIN_SELF_CORRECTION", "true").lower() == "true"

# UI Settings
APP_NAME = "VoiceMate - Laptop Agent"
VERSION = "2.0 (Desktop Edition)"
