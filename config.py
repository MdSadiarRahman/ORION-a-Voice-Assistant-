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

BROWSER_USE_REPO_DIR = resolve_repo_path(["browser-use", "browser_use"], BASE_DIR.parent / "VoiceMate Repo Help" / "browser-use")
PYMUPDF_REPO_DIR = resolve_repo_path(["PyMuPDF", "pymupdf"], BASE_DIR.parent / "VoiceMate Repo Help" / "PyMuPDF")
PLAYWRIGHT_REPO_DIR = resolve_repo_path(["playwright-python", "playwright"], BASE_DIR.parent / "VoiceMate Repo Help" / "playwright-python")
DOCLING_REPO_DIR = resolve_repo_path(["docling"], BASE_DIR.parent / "VoiceMate Repo Help" / "docling")
AGENCY_AGENTS_REPO_DIR = resolve_repo_path(["agency-agents", "agency_agents"], BASE_DIR.parent / "VoiceMate Repo Help" / "agency-agents")
VOSK_API_REPO_DIR = resolve_repo_path(["vosk-api", "vosk"], BASE_DIR.parent / "VoiceMate Repo Help" / "vosk-api")
TAKEOUT_ASSISTANT_REPO_DIR = resolve_repo_path(["takeout_assistant", "takeout-assistant"], BASE_DIR.parent / "VoiceMate Repo Help" / "takeout_assistant")
OFFLINE_VOICE_AI_REPO_DIR = resolve_repo_path(["offline-voice-ai"], BASE_DIR.parent / "VoiceMate Repo Help" / "offline-voice-ai")

PLAYWRIGHT_PROFILES_DIR = DATA_DIR / "playwright_profiles"
PLAYWRIGHT_SCREENSHOTS_DIR = CAPTURES_DIR / "web_screenshots"
DOCLING_OUTPUT_DIR = DATA_DIR / "docling_exports"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
CONFIG_DIR.mkdir(exist_ok=True)
CAPTURES_DIR.mkdir(exist_ok=True)
DOCS_DIR.mkdir(exist_ok=True)
PLAYWRIGHT_PROFILES_DIR.mkdir(exist_ok=True)
PLAYWRIGHT_SCREENSHOTS_DIR.mkdir(exist_ok=True)
DOCLING_OUTPUT_DIR.mkdir(exist_ok=True)

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

# Multimodal Document Parsing & RAG Chunking (Docling) Settings
DOCLING_ENABLED = True
DOCLING_DO_OCR = os.getenv("VOICEMATE_DOCLING_OCR", "true").lower() == "true"
DOCLING_DO_TABLES = os.getenv("VOICEMATE_DOCLING_TABLES", "true").lower() == "true"
DOCLING_CHUNK_MAX_TOKENS = int(os.getenv("VOICEMATE_DOCLING_CHUNK_TOKENS", "512"))
DOCLING_SUPPORTED_EXTS = (".pdf", ".docx", ".pptx", ".xlsx", ".html", ".epub", ".csv", ".txt", ".md")

# UI Settings
APP_NAME = "VoiceMate - Laptop Agent"
VERSION = "2.0 (Desktop Edition)"
