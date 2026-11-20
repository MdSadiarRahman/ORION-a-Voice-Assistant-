"""
Aider Code Editing Subsystem for VoiceMate.
Provides AI Pair Programming, resilient SEARCH/REPLACE code patch applications,
AST-based RepoMap generation, and automated Git safety nets.
"""
from src.coder_agent.coder_config import get_coder_settings
from src.coder_agent.search_replace_engine import SearchReplaceEngine
from src.coder_agent.repo_map_generator import RepoMapGenerator
from src.coder_agent.git_manager import GitSafetyManager
from src.coder_agent.coder_controller import CoderController
from src.coder_agent.coder_fallback import CoderFallbackAgent
from src.coder_agent.coder_task_runner import CoderTaskRunner

__all__ = [
    "get_coder_settings",
    "SearchReplaceEngine",
    "RepoMapGenerator",
    "GitSafetyManager",
    "CoderController",
    "CoderFallbackAgent",
    "CoderTaskRunner",
]
