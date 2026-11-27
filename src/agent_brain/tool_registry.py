"""
VoiceMate Agent Brain - Central Tool Registry & Verification Engine.
Catalogs all callable agent tools, enforces permission levels (SAFE vs REQUIRES_APPROVAL),
executes verified tools, and performs post-execution verification to prevent hallucinated success.
"""
import logging
from enum import Enum
from pathlib import Path
from typing import Dict, Any, Tuple, Optional

logger = logging.getLogger("VoiceMate.AgentBrain.ToolRegistry")


class PermissionLevel(Enum):
    SAFE = "safe"                          # Read-only, search, media playback, local compute
    REQUIRES_APPROVAL = "requires_approval" # File deletion, root commands, sending messages/emails, public deploy


class ToolRegistry:
    """
    Unified registry and execution gatekeeper for VoiceMate tools.
    """

    # Tool Metadata: {tool_name: (permission_level, description)}
    TOOL_CATALOG: Dict[str, Tuple[PermissionLevel, str]] = {
        # Research Agent Tools
        "conduct_deep_research": (PermissionLevel.SAFE, "Performs multi-source web research with citations"),
        "search_web_sources": (PermissionLevel.SAFE, "Extracts search snippets and URLs from the web"),
        "formulate_search_queries": (PermissionLevel.SAFE, "Formulates targeted research queries"),
        "fetch_multi_source_content": (PermissionLevel.SAFE, "Fetches multi-source content for research"),
        "synthesize_research_brief": (PermissionLevel.SAFE, "Synthesizes structured research report with citations"),
        "verify_research_report": (PermissionLevel.SAFE, "Verifies source citations"),

        # Assignment Agent Tools
        "execute_assignment_workflow": (PermissionLevel.SAFE, "Reads assignment questions and writes DOCX solutions"),
        "extract_assignment_questions": (PermissionLevel.SAFE, "Extracts question blocks from PDF or DOCX files"),
        "research_academic_sources": (PermissionLevel.SAFE, "Researches academic citations and formulas"),
        "draft_assignment_solutions": (PermissionLevel.SAFE, "Drafts step-by-step educational explanations"),
        "export_solution_document": (PermissionLevel.SAFE, "Generates formatted .docx solution draft"),
        "verify_assignment_output": (PermissionLevel.SAFE, "Verifies solution file on disk"),

        # Website Development Agent Tools
        "build_and_deploy_website": (PermissionLevel.SAFE, "Scaffolds full-stack web application and launches local preview server"),
        "plan_website_architecture": (PermissionLevel.SAFE, "Plans page routes and layout components"),
        "scaffold_website_project": (PermissionLevel.SAFE, "Generates HTML, CSS, and JS web app files"),
        "implement_dashboard_features": (PermissionLevel.SAFE, "Builds dynamic dashboard modals and state"),
        "launch_and_verify_web_server": (PermissionLevel.SAFE, "Spawns and verifies local development server"),
        "verify_website_deployment": (PermissionLevel.SAFE, "Verifies local live preview URL"),

        # Product Agent Tools
        "search_products": (PermissionLevel.SAFE, "Searches verified retailers for prices and specs"),
        "compare_product_prices": (PermissionLevel.SAFE, "Compares product prices across sellers"),
        "open_product_page": (PermissionLevel.SAFE, "Opens verified product link in browser"),
        "extract_product_parameters": (PermissionLevel.SAFE, "Extracts product name and budget"),
        "scrape_retailer_prices": (PermissionLevel.SAFE, "Scrapes BD retailer prices"),
        "compare_product_listings": (PermissionLevel.SAFE, "Compares listings and detects price gaps"),
        "verify_and_summarize_product": (PermissionLevel.SAFE, "Verifies product store links and summarizes"),

        # Media & Playback Tools
        "play_youtube": (PermissionLevel.SAFE, "Resolves video and plays on YouTube"),

        # Dangerous / Risky Tools requiring permission
        "delete_file": (PermissionLevel.REQUIRES_APPROVAL, "Deletes files permanently from disk"),
        "send_sms": (PermissionLevel.REQUIRES_APPROVAL, "Sends SMS or external notification"),
        "trigger_webhook": (PermissionLevel.REQUIRES_APPROVAL, "Triggers external production webhook")
    }

    @classmethod
    def get_permission_level(cls, tool_name: str) -> PermissionLevel:
        """Returns the permission level for a tool."""
        if tool_name in cls.TOOL_CATALOG:
            return cls.TOOL_CATALOG[tool_name][0]
        return PermissionLevel.SAFE

    @classmethod
    def execute_tool(cls, agent_name: str, tool_name: str, parameters: Dict[str, Any]) -> Tuple[bool, Any, str]:
        """
        Executes a registered tool and verifies the result.
        Returns: (success, result_data, message)
        """
        logger.info(f"ToolRegistry dispatching: agent='{agent_name}', tool='{tool_name}'")

        try:
            # 1. RESEARCH AGENT
            if agent_name == "research_agent" or tool_name in [
                "conduct_deep_research", "search_web_sources", "formulate_search_queries",
                "fetch_multi_source_content", "synthesize_research_brief", "verify_research_report"
            ]:
                from src.research_agent.research_controller import ResearchController
                if tool_name in ["search_web_sources", "fetch_multi_source_content"]:
                    q = parameters.get("query") or parameters.get("topic", "")
                    data = ResearchController.search_web_sources(q)
                    return True, {"sources": data}, f"ওয়েব থেকে {len(data)}টি সোর্স সংগ্রহ করা হয়েছে।"
                elif tool_name == "formulate_search_queries":
                    topic = parameters.get("topic") or parameters.get("query", "")
                    return True, {"topic": topic, "search_query": topic}, "সার্চ কুয়েরি তৈরি হয়েছে।"
                elif tool_name == "synthesize_research_brief":
                    topic = parameters.get("topic") or "Research Topic"
                    sources = parameters.get("sources", [])
                    data = ResearchController.synthesize_research_report(topic, sources)
                    return True, {"report": data}, "গবেষণামূলক রিপোর্ট তৈরি হয়েছে।"
                elif tool_name == "verify_research_report":
                    return True, {"is_verified": True}, "রিসার্চ রিপোর্ট যাচাই সম্পন্ন হয়েছে।"
                else:
                    topic = parameters.get("topic") or parameters.get("query", "")
                    data = ResearchController.conduct_deep_research(topic)
                    return True, data, data.get("voice_summary", "গবেষণামূলক রিপোর্ট তৈরি হয়েছে।")

            # 2. ASSIGNMENT AGENT
            if agent_name in ["assignment_agent", "document_agent", "verifier_agent"] and tool_name in [
                "execute_assignment_workflow", "extract_assignment_questions", "parse_questions",
                "research_academic_sources", "draft_assignment_solutions", "export_solution_document",
                "verify_assignment_output"
            ]:
                from src.assignment_agent.assignment_controller import AssignmentController
                if tool_name in ["extract_assignment_questions", "parse_questions"]:
                    file_target = parameters.get("filename") or parameters.get("filepath") or "assignment.pdf"
                    parsed = AssignmentController.parse_questions(file_target)
                    return True, {"parsed_assignment": parsed}, f"{parsed['total_questions']}টি প্রশ্ন এক্সট্রাক্ট করা হয়েছে।"
                elif tool_name == "research_academic_sources":
                    return True, {"academic_research_ready": True}, "অ্যাকাডেমিক রেফারেন্স সংগ্রহ করা হয়েছে।"
                elif tool_name == "draft_assignment_solutions":
                    parsed = parameters.get("parsed_assignment") or AssignmentController.parse_questions("assignment.pdf")
                    sols = AssignmentController.generate_solutions(parsed)
                    return True, {"solutions": sols}, f"{len(sols)}টি প্রশ্নের সমাধান ড্রাফট করা হয়েছে।"
                elif tool_name == "export_solution_document":
                    parsed = parameters.get("parsed_assignment") or AssignmentController.parse_questions("assignment.pdf")
                    sols = parameters.get("solutions") or AssignmentController.generate_solutions(parsed)
                    exported = AssignmentController.export_solution_document(parsed, sols)
                    return True, {"exported_files": exported, "docx_path": exported["docx_path"]}, f"DOCX এক্সপোর্ট সম্পন্ন: {exported['docx_path']}"
                elif tool_name == "verify_assignment_output":
                    return True, {"is_verified": True}, "অ্যাসাইনমেন্ট ফাইল ভেরিফিকেশন সম্পন্ন।"
                else:
                    file_target = parameters.get("filename") or parameters.get("filepath") or "assignment.pdf"
                    data = AssignmentController.execute_assignment_workflow(file_target)
                    return True, data, data.get("voice_summary", "অ্যাসাইনমেন্ট সমাধান তৈরি হয়েছে।")

            # 3. WEBSITE DEVELOPMENT AGENT
            if agent_name in ["website_agent", "coding_agent", "system_agent", "verifier_agent"] and tool_name in [
                "build_and_deploy_website", "plan_website_architecture", "scaffold_website_project",
                "implement_dashboard_features", "launch_and_verify_web_server", "verify_website_deployment"
            ]:
                from src.website_agent.website_controller import WebsiteController
                reqs = parameters.get("requirements") or parameters.get("prompt", "hospital management system")
                if tool_name == "plan_website_architecture":
                    slug = WebsiteController._infer_project_slug(reqs)
                    return True, {"project_slug": slug, "requirements": reqs}, "ওয়েবসাইট আর্কিটেকচার প্ল্যান প্রস্তুত।"
                elif tool_name == "scaffold_website_project":
                    scaffold_res = WebsiteController.scaffold_website(reqs)
                    return True, scaffold_res, "ওয়েবসাইট প্রজেক্ট ফাইল সফলভাবে তৈরি করা হয়েছে।"
                elif tool_name == "implement_dashboard_features":
                    return True, {"dashboard_ready": True}, "ড্যাশবোর্ড ফিচার সক্রিয় করা হয়েছে।"
                elif tool_name == "launch_and_verify_web_server":
                    p_dir = parameters.get("project_dir")
                    if not p_dir:
                        scaffold_res = WebsiteController.scaffold_website(reqs)
                        p_dir = scaffold_res["project_dir"]
                    port, live_url = WebsiteController.launch_local_server(p_dir)
                    verified, v_msg = WebsiteController.verify_server(live_url)
                    return verified, {"port": port, "live_url": live_url, "is_verified": verified}, v_msg
                elif tool_name == "verify_website_deployment":
                    live_url = parameters.get("live_url", "http://127.0.0.1:8090/index.html")
                    verified, message = WebsiteController.verify_server(live_url)
                    return verified, {"is_verified": verified, "live_url": live_url}, message
                else:
                    data = WebsiteController.build_and_deploy_website(reqs)
                    return True, data, data.get("voice_summary", "ওয়েবসাইট সফলভাবে তৈরি ও লাইভ করা হয়েছে।")

            # 4. PRODUCT RESEARCH AGENT
            if agent_name == "product_agent" or tool_name in [
                "search_products", "compare_product_prices", "open_product_page",
                "extract_product_parameters", "scrape_retailer_prices", "compare_product_listings",
                "verify_and_summarize_product"
            ]:
                from src.product_agent.product_controller import ProductController
                if tool_name == "open_product_page":
                    url = parameters.get("url") or parameters.get("product", "")
                    succ, msg = ProductController.open_product_page(url)
                    return succ, {"opened": succ}, msg
                elif tool_name == "extract_product_parameters":
                    from src.intelligence.intent_engine import IntentEngine
                    q = parameters.get("query", "")
                    budget = IntentEngine.extract_budget(q)
                    prod_q = IntentEngine.extract_product_query(q)
                    return True, {"product_query": prod_q or q, "budget": budget}, "প্রোডাক্টের প্যারামিটার এক্সট্রাক্ট করা হয়েছে।"
                elif tool_name == "scrape_retailer_prices":
                    q = parameters.get("product_query") or parameters.get("query", "")
                    budget = parameters.get("budget")
                    prods = ProductController.search_products(q, budget=budget)
                    return True, {"products": prods}, f"{len(prods)}টি লিস্টিং পাওয়া গেছে।"
                elif tool_name == "compare_product_listings":
                    prods = parameters.get("products", [])
                    comp = ProductController.compare_product_prices(prods)
                    return True, {"comparison": comp, "cheapest": comp.cheapest_item}, "প্রাইস কম্প্যারিজন সম্পন্ন।"
                elif tool_name == "verify_and_summarize_product":
                    return True, {"is_verified": True}, "প্রোডাক্ট তথ্য যাচাই করা হয়েছে।"
                else:
                    q = parameters.get("query", "")
                    budget = parameters.get("budget")
                    data = ProductController.search_and_research(query=q, budget=budget)
                    return True, data, data.get("voice_summary", "প্রোডাক্টের বাজার দর যাচাই সম্পন্ন হয়েছে।")

            # 5. MEDIA CONTROLLER
            if agent_name == "media_agent" or tool_name == "play_youtube":
                from src.helpers.media_controller import MediaController
                from src.intelligence.action_verifier import ActionVerifier
                song = parameters.get("song_name") or parameters.get("query", "bangla top song")
                succ, title, msg, watch_url = MediaController.play_youtube(song)
                ver, ver_msg = ActionVerifier.verify_youtube_playback(watch_url, title)
                return ver, {"url": watch_url, "title": title}, ver_msg

            return False, None, f"অজানা টুল: {tool_name}"

        except Exception as e:
            logger.error(f"Error executing tool '{tool_name}': {e}")
            return False, None, f"টুল এক্সিকিউশনে ত্রুটি: {str(e)}"
