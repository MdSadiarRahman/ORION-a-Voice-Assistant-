"""
VoiceMate Intelligence Engine Package.
Provides hybrid intent classification, context management, Ollama Qwen integration,
action verification, and safety guards.
"""
from src.intelligence.intent_engine import Intent, IntentEngine
from src.intelligence.fast_router import FastCommandRouter
from src.intelligence.context_manager import ContextManager
from src.intelligence.ollama_client import OllamaClient
from src.intelligence.action_verifier import ActionVerifier
from src.intelligence.safety_guard import SafetyGuard
from src.intelligence.decision_engine import HybridDecisionEngine

__all__ = [
    "Intent",
    "IntentEngine",
    "FastCommandRouter",
    "ContextManager",
    "OllamaClient",
    "ActionVerifier",
    "SafetyGuard",
    "HybridDecisionEngine",
]
