"""
VoiceMate Laptop Agent - LangGraph Central Brain Configuration.
Settings for state persistence, cyclic retry limits, checkpointing, and intent routing.
"""
import os
from pathlib import Path
from typing import List, Dict, Any

# LangGraph Reference Repository Path
LANGGRAPH_REPO_DIR = Path(r"E:\BAUST_3.2\Artificial Intelligence Sessional\VoiceMate Repo Help\langgraph")

# Session & Checkpointing
CHECKPOINT_DIR = Path("data") / "checkpoints"
CHECKPOINT_DB_FILE = CHECKPOINT_DIR / "brain_memory.sqlite"
DEFAULT_SESSION_ID = os.getenv("VOICEMATE_BRAIN_SESSION_ID", "voicemate_desktop_session")

# Resilience & Cyclic Limits
MAX_CYCLIC_RETRIES = int(os.getenv("VOICEMATE_BRAIN_MAX_RETRIES", "2"))
ENABLE_CYCLIC_SELF_CORRECTION = os.getenv("VOICEMATE_BRAIN_SELF_CORRECTION", "true").lower() == "true"

# Critical Action Safety & Confirmation (Human-In-The-Loop)
CONFIRMATION_KEYWORDS: List[str] = [
    "ডিলিট", "delete", "মুছে ফেলো", "মুছে দাও",
    "রোলব্যাক", "rollback", "আনডু",
    "সার্ভার বন্ধ", "বন্ধ করে দাও", "উইন্ডো কাটো"
]

def get_brain_settings() -> Dict[str, Any]:
    """Returns runtime settings dictionary for the LangGraph brain orchestrator."""
    return {
        "repo_path": str(LANGGRAPH_REPO_DIR),
        "checkpoint_dir": str(CHECKPOINT_DIR),
        "checkpoint_file": str(CHECKPOINT_DB_FILE),
        "session_id": DEFAULT_SESSION_ID,
        "max_retries": MAX_CYCLIC_RETRIES,
        "self_correction": ENABLE_CYCLIC_SELF_CORRECTION,
        "confirmation_keywords": CONFIRMATION_KEYWORDS
    }
