"""
Browser Agent Configuration & Environment Resolver.
Ensures browser-use repository path is properly registered and configured.
"""
import sys
import os
from pathlib import Path
from config import (
    BROWSER_USE_REPO_DIR,
    BROWSER_TYPE,
    BROWSER_HEADLESS,
    BROWSER_TIMEOUT_SECONDS,
    BROWSER_LLM_MODEL
)

# Dynamically add the local browser-use repository to sys.path if not present
if BROWSER_USE_REPO_DIR.exists():
    repo_str = str(BROWSER_USE_REPO_DIR)
    if repo_str not in sys.path:
        sys.path.insert(0, repo_str)

def is_browser_use_available() -> bool:
    """Checks if the core browser_use module and its agent dependencies are importable."""
    try:
        import browser_use
        from browser_use import Agent, Browser
        return True
    except Exception:
        return False

def get_browser_settings() -> dict:
    return {
        "browser_type": BROWSER_TYPE,
        "headless": BROWSER_HEADLESS,
        "timeout": BROWSER_TIMEOUT_SECONDS,
        "model": BROWSER_LLM_MODEL,
        "repo_path": str(BROWSER_USE_REPO_DIR)
    }
