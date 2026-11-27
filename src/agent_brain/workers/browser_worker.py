"""
VoiceMate Laptop Agent - Browser & Web Automation Worker Node.
Executes autonomous browser navigation (browser-use) and deterministic automation (Playwright).
"""
import logging
from langchain_core.messages import AIMessage
from ..state_schema import AgentState

logger = logging.getLogger("VoiceMate.AgentBrain.BrowserWorker")

def browser_worker(state: AgentState) -> dict:
    """
    Executes web automation and browsing tasks via Playwright or Browser-Use.
    """
    query = state.get("query", "")
    logger.info(f"BrowserWorker executing task: '{query}'")

    try:
        query_lower = query.lower()
        # Product search & price research detection
        product_triggers = ["laptop", "ল্যাপটপ", "phone", "ফোন", "দাম", "price", "samsung", "hp", "খুঁজে দাও", "under"]
        if any(w in query_lower for w in product_triggers) and any(w in query_lower for w in ["laptop", "phone", "samsung", "hp", "দাম", "price"]):
            from ...product_agent.product_controller import ProductController
            from ...intelligence.intent_engine import IntentEngine
            budget = IntentEngine.extract_budget(query)
            res = ProductController.search_and_research(query, budget=budget)
            msg = res.get("voice_summary", "প্রোডাক্টের বাজার দর ও স্পেসিফিকেশন তথ্য খোঁজা সম্পন্ন হয়েছে।")
            return {
                "final_reply": msg,
                "worker_results": {"product_research": res},
                "messages": [AIMessage(content=msg)],
                "error": None
            }

        # Playwright media or screenshot detection
        if any(w in query_lower for w in ["প্লে", "play", "স্ক্রিনশট", "screenshot", "হোয়াটসঅ্যাপ"]):
            from ...playwright_agent.playwright_controller import PlaywrightController
            result = PlaywrightController.execute_task(query)
            msg = result.get("message", "প্লে-রাইট ওয়েব টাস্ক সম্পন্ন হয়েছে।")
        else:
            # Autonomous browser agent task
            from ...browser_agent.browser_fallback import BrowserFallbackAgent
            result = BrowserFallbackAgent.execute_fallback_task(query)
            msg = result.get("message", "ব্রাউজার এজেন্ট অনুসন্ধান সম্পন্ন করেছে।")

        return {
            "final_reply": msg,
            "worker_results": {"browser": result},
            "messages": [AIMessage(content=msg)],
            "error": None
        }

    except Exception as e:
        logger.error(f"BrowserWorker error: {e}")
        return {
            "error": str(e),
            "final_reply": f"ব্রাউজার অপারেশনে ত্রুটি হয়েছে: {e}"
        }
