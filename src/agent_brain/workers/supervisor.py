"""
VoiceMate Laptop Agent - Master Supervisor Node.
Evaluates user intent, manages safety guardrails, initiates human-in-the-loop interrupts,
and routes tasks to specialized worker nodes.
"""
import logging
from langchain_core.messages import AIMessage
from ..state_schema import AgentState
from ..brain_config import CONFIRMATION_KEYWORDS, MAX_CYCLIC_RETRIES

logger = logging.getLogger("VoiceMate.AgentBrain.Supervisor")

def supervisor_node(state: AgentState) -> dict:
    """
    Evaluates current conversation turn, classifies target intent,
    and determines the next worker node.
    """
    messages = state.get("messages", [])
    query = state.get("query", "")
    
    # Extract query text from latest message if not set directly
    if not query and messages:
        last_msg = messages[-1]
        query = str(last_msg.content)

    query_clean = query.lower().strip()
    retry_count = state.get("retry_count", 0)
    current_error = state.get("error")

    logger.info(f"Supervisor evaluating query: '{query_clean}' (retry: {retry_count}, error: {current_error})")

    # ১. সাইক্লিক রিট্রাই ও স্বয়ংক্রিয় সংশোধন (Self-Correction)
    if current_error and retry_count < MAX_CYCLIC_RETRIES:
        logger.warning(f"Supervisor detecting failure: {current_error}. Attempting self-correction loop.")
        # If browser failed, try system search; if docling failed, try document reader fallback
        prev_worker = state.get("next_worker", "")
        if prev_worker == "browser_worker":
            return {
                "next_worker": "system_worker",
                "intent": "system_search_fallback",
                "retry_count": retry_count + 1,
                "error": None
            }
        elif prev_worker == "document_worker":
            return {
                "next_worker": "document_worker",
                "intent": "document_reader_fallback",
                "retry_count": retry_count + 1,
                "error": None
            }

    # ২. হিউম্যান-ইন-দ্য-লুপ নিশ্চিতকরণ যাচাই (Human-In-The-Loop Confirmation)
    user_confirmed = state.get("user_confirmed", False)
    if not user_confirmed and any(kw in query_clean for kw in CONFIRMATION_KEYWORDS):
        return {
            "requires_confirmation": True,
            "next_worker": "conversation_worker",
            "intent": "await_user_confirmation",
            "final_reply": f"আপনি কি নিশ্চিত যে আপনি এটি করতে চান: '{query}'? অনুগ্রহ করে হ্যাঁ অথবা না বলুন।",
            "messages": [AIMessage(content=f"আপনি কি নিশ্চিত যে আপনি এটি করতে চান: '{query}'?")]
        }

    # ৩. ইনটেন্ট ক্লাসিফিকেশন ও ওয়ার্কার সিলেকশন (Intent Classification)
    # ক. ব্রাউজার ও ওয়েব অটোমেশন (Browser-Use & Playwright)
    browser_kws = [
        "ব্রাউজার", "browser", "ওয়েব", "web", "প্লে করো", "play", "ইউটিউবে", "youtube",
        "গান বাজাও", "ভিডিও চালাও", "স্ক্রিনশট", "screenshot", "হোয়াটসঅ্যাপ", "whatsapp"
    ]
    if any(kw in query_clean for kw in browser_kws):
        return {"next_worker": "browser_worker", "intent": "browser_automation"}

    # খ. মাল্টিমোডাল ডকুমেন্ট ও আরএজি চাংকিং (Docling & PyMuPDF)
    doc_kws = [
        "পিডিএফ", "pdf", "ডকুমেন্ট", "document", "ওয়ার্ড", "docx", "পাওয়ারপয়েন্ট", "pptx",
        "এক্সেল", "xlsx", "ডকলিং", "docling", "চাংক", "chunk", "টেবিল এক্সট্রাক্ট", "ফাইল পড়ো"
    ]
    if any(kw in query_clean for kw in doc_kws):
        return {"next_worker": "document_worker", "intent": "document_intelligence"}

    # গ. কোডিং ও ডেভেলপার ক্যানভাস (Aider & OpenHands)
    coding_kws = [
        "কোড", "code", "গিট", "git", "ক্যানভাস", "canvas", "ওপেনহ্যান্ডস", "openhands",
        "রেপো ম্যাপ", "repo map", "এডিট করো", "প্যাচ", "patch", "টার্মিনাল", "terminal",
        "কোড রিভিউ", "কোড অডিট", "search replace", "<<<<<<< search"
    ]
    if any(kw in query_clean for kw in coding_kws):
        return {"next_worker": "coding_worker", "intent": "developer_coding"}

    # ঘ. এনএইটেন এন্টারপ্রাইজ অটোমেশন (n8n Workflows)
    n8n_kws = [
        "এনএইটেন", "n8n", "ওয়ার্কফ্লো", "workflow", "অটোমেশন ফ্লো", "ওয়েবহুক", "webhook",
        "নোশন", "notion", "গুগল শিট", "sheets", "স্ল্যাক", "slack"
    ]
    if any(kw in query_clean for kw in n8n_kws):
        return {"next_worker": "automation_worker", "intent": "workflow_automation"}

    # ঙ. সিস্টেম, ব্যাটারি, এপিআই সার্ভার ও ল্যাপটপ কন্ট্রোল
    system_kws = [
        "চার্জ", "battery", "ব্যাটারি", "টাইপিং", "টাইপ", "typing", "উপরে যাও", "নিচে নামো",
        "কল", "call", "ফোন", "phone", "এপিআই", "api", "ফাস্টএপিআই", "fastapi", "সোয়েগার",
        "swagger", "ওপেন", "open", "চালু", "কাটো", "উইন্ডো বন্ধ"
    ]
    if any(kw in query_clean for kw in system_kws):
        return {"next_worker": "system_worker", "intent": "system_control"}

    # চ. সাধারণ কনভার্সেশন ও অনুসন্ধান (Conversation & Inquiries)
    return {"next_worker": "conversation_worker", "intent": "conversation"}
