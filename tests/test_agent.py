"""
Comprehensive Test Suite for VoiceMate Laptop Agent.
Includes tests for Core Voice, System, Desktop, Browser-Use, and Document Intelligence (PyMuPDF).
"""
import unittest
from unittest.mock import patch
from pathlib import Path
import sys
import os

# Add root directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.command_processor import CommandProcessor
from src.helpers.date_helper import DateHelper
from src.helpers.contact_helper import ContactHelper
from src.helpers.battery_helper import BatteryHelper
from src.helpers.desktop_automation_helper import DesktopAutomationHelper
from src.browser_agent.browser_config import get_browser_settings
from src.browser_agent.browser_fallback import BrowserFallbackAgent
from src.document_agent.document_config import get_document_settings
from src.document_agent.document_task_runner import DocumentTaskRunner
from src.document_agent.document_fallback import DocumentFallbackReader
from src.playwright_agent.playwright_config import get_playwright_settings
from src.playwright_agent.playwright_fallback import PlaywrightFallbackAgent
from src.playwright_agent.playwright_task_runner import PlaywrightTaskRunner
from src.canvas_agent.canvas_config import get_canvas_settings
from src.canvas_agent.canvas_event_stream import CanvasEventStream, EventKind
from src.canvas_agent.canvas_workspace_runner import CanvasWorkspaceRunner
from src.canvas_agent.canvas_task_runner import CanvasTaskRunner
from src.coder_agent.coder_config import get_coder_settings
from src.coder_agent.search_replace_engine import SearchReplaceEngine
from src.coder_agent.repo_map_generator import RepoMapGenerator
from src.coder_agent.git_manager import GitSafetyManager
from src.coder_agent.coder_task_runner import CoderTaskRunner
from src.docling_agent.docling_config import get_docling_settings
from src.docling_agent.docling_converter import DoclingConverter
from src.docling_agent.docling_chunker import DoclingHybridChunker
from src.docling_agent.docling_task_runner import DoclingTaskRunner
from src.n8n_agent.n8n_config import get_n8n_settings
from src.n8n_agent.n8n_workflow_template import N8nWorkflowTemplate
from src.n8n_agent.n8n_fallback import N8nFallbackAgent
from src.n8n_agent.n8n_task_runner import N8nTaskRunner
from src.api_gateway.api_config import API_HOST, API_PORT, API_DOCS_URL
from src.api_gateway.schemas import (
    CommandRequest, CommandResponse, SystemStatusResponse,
    AutomationTaskRequest, AutomationTaskResponse, WebhookPayload
)
from src.api_gateway.server_controller import APIServerController
from src.api_gateway.api_fallback import APIFallbackHandler
from src.agent_brain.brain_config import get_brain_settings
from src.agent_brain.brain_controller import LangGraphBrainController
from src.agent_brain.brain_fallback import BrainFallbackOrchestrator
from src.agent_brain.state_schema import AgentState

class TestVoiceMateAgent(unittest.TestCase):

    def test_date_and_time_helper(self):
        date_str = DateHelper.get_current_date_bengali()
        time_str = DateHelper.get_current_time_bengali()
        self.assertTrue("আজকের তারিখ হলো" in date_str)
        self.assertTrue("এখন সময় হলো" in time_str or "বেজে" in time_str)

    def test_contact_helper(self):
        number = ContactHelper.get_phone_number_by_name("বাবা")
        self.assertEqual(number, "01711000001")

        res = ContactHelper.get_phone_number_by_last_digits("001")
        self.assertIsNotNone(res)
        self.assertEqual(res[0], "বাবা")
        self.assertEqual(res[1], "01711000001")

    def test_battery_helper(self):
        info = BatteryHelper.get_battery_info()
        self.assertIn("percent", info)
        self.assertIn("charging", info)
        self.assertIn("is_laptop", info)

    @patch("webbrowser.open")
    @patch("subprocess.Popen")
    def test_command_processor_queries(self, mock_popen, mock_web_open):
        mock_web_open.return_value = True

        # 1. Typing Mode
        res_typing = CommandProcessor.process_command("টাইপ করা শুরু করো")
        self.assertEqual(res_typing, "ACTION_START_TYPING")

        # 2. Autonomous Browser Agent Task (Browser-Use 1.0)
        res_browser = CommandProcessor.process_command("ব্রাউজারে গিয়ে ঢাকা বিশ্ববিদ্যালয়ের ওয়েবসাইট দেখো")
        self.assertTrue(res_browser.startswith("ACTION_BROWSER_TASK|"))
        self.assertIn("ঢাকা বিশ্ববিদ্যালয়", res_browser)

        # 3. Document Intelligence Task (PyMuPDF)
        res_doc = CommandProcessor.process_command("ডকুমেন্ট পড়ো test_sample.md")
        self.assertTrue(res_doc.startswith("ACTION_DOCUMENT_TASK|"))
        self.assertIn("test_sample.md", res_doc)

        # 4. Docling Multimodal Document Intelligence & RAG Chunking
        res_docling_word = CommandProcessor.process_command("ডকলিং দিয়ে ওয়ার্ড ফাইল পড়ো report.docx")
        self.assertTrue(res_docling_word.startswith("ACTION_DOCLING_TASK|"))
        self.assertIn("report.docx", res_docling_word)

        res_docling_chunk = CommandProcessor.process_command("ডকুমেন্ট চাংক করো test_sample.md")
        self.assertTrue(res_docling_chunk.startswith("ACTION_DOCLING_TASK|"))

        # 5. Playwright Deterministic Automation (Media Playback, Screenshot, Session)
        res_pw_play = CommandProcessor.process_command("ইউটিউবে রবীন্দ্রসংগীত প্লে করো")
        self.assertTrue(res_pw_play.startswith("ACTION_PLAYWRIGHT_TASK|"))
        self.assertIn("রবীন্দ্রসংগীত", res_pw_play)

        res_pw_shot = CommandProcessor.process_command("ওয়েব স্ক্রিনশট নাও https://github.com")
        self.assertTrue(res_pw_shot.startswith("ACTION_PLAYWRIGHT_TASK|"))

        res_pw_session = CommandProcessor.process_command("হোয়াটসঅ্যাপ ওয়েব ওপেন করো")
        self.assertTrue(res_pw_session.startswith("ACTION_PLAYWRIGHT_TASK|"))

        # 5. OpenHands Developer Canvas & Workspace Tasks
        res_canvas_launch = CommandProcessor.process_command("ওপেনহ্যান্ডস ক্যানভাস চালু করো")
        self.assertTrue(res_canvas_launch.startswith("ACTION_CANVAS_TASK|"))

        res_canvas_audit = CommandProcessor.process_command("কোড অডিট করো")
        self.assertTrue(res_canvas_audit.startswith("ACTION_CANVAS_TASK|"))

        res_canvas_git = CommandProcessor.process_command("গিট স্ট্যাটাস দেখো")
        self.assertTrue(res_canvas_git.startswith("ACTION_CANVAS_TASK|"))

        res_canvas_tree = CommandProcessor.process_command("ফাইল ট্রি দেখাও")
        self.assertTrue(res_canvas_tree.startswith("ACTION_CANVAS_TASK|"))

        # 6. Aider AI Pair Programming & Code Editing Tasks
        res_coder_map = CommandProcessor.process_command("রেপো ম্যাপ তৈরি করো")
        self.assertTrue(res_coder_map.startswith("ACTION_CODER_TASK|"))

        res_coder_edit = CommandProcessor.process_command("কোড এডিট করো")
        self.assertTrue(res_coder_edit.startswith("ACTION_CODER_TASK|"))

        res_coder_rb = CommandProcessor.process_command("কোড রোলব্যাক করো")
        self.assertTrue(res_coder_rb.startswith("ACTION_CODER_TASK|"))

        res_coder_raw = CommandProcessor.process_command("<<<<<<< SEARCH\nfoo\n=======\nbar\n>>>>>>> REPLACE")
        self.assertTrue(res_coder_raw.startswith("ACTION_CODER_TASK|"))

        # 7. n8n Enterprise Workflow Automation Tasks
        res_n8n_open = CommandProcessor.process_command("এনএইটেন ওপেন করো")
        self.assertTrue(res_n8n_open.startswith("ACTION_N8N_TASK|"))

        res_n8n_flow = CommandProcessor.process_command("অটোমেশন ফ্লো চালাও ইমেইল পাঠাও")
        self.assertTrue(res_n8n_flow.startswith("ACTION_N8N_TASK|"))

        res_n8n_notion = CommandProcessor.process_command("নোশনে পাঠাও আজকের মিটিং নোট")
        self.assertTrue(res_n8n_notion.startswith("ACTION_N8N_TASK|"))

        # 8. FastAPI Gateway Commands
        res_api_open = CommandProcessor.process_command("এপিআই ওপেন করো")
        self.assertTrue(res_api_open.startswith("ACTION_API_GATEWAY_TASK|"))

        res_api_status = CommandProcessor.process_command("এপিআই স্ট্যাটাস দেখো")
        self.assertTrue(res_api_status.startswith("ACTION_API_GATEWAY_TASK|"))

        res_api_docs = CommandProcessor.process_command("সোয়েগার ডক দেখাও")
        self.assertTrue(res_api_docs.startswith("ACTION_API_GATEWAY_TASK|"))

        # 9. LangGraph Brain Commands
        res_brain_status = CommandProcessor.process_command("ব্রেন স্ট্যাটাস দেখাও")
        self.assertTrue(res_brain_status.startswith("ACTION_BRAIN_TASK|"))

        res_brain_hist = CommandProcessor.process_command("ব্রেন হিস্ট্রি দেখো")
        self.assertTrue(res_brain_hist.startswith("ACTION_BRAIN_TASK|"))

        res_brain_run = CommandProcessor.process_command("ল্যাংগ্রাফ মাল্টি এজেন্ট চালাও")
        self.assertTrue(res_brain_run.startswith("ACTION_BRAIN_TASK|"))

        # 10. YouTube & Google Searches
        res_yt = CommandProcessor.process_command("ইউটিউবে গান সার্চ করো")
        self.assertIn("ইউটিউবে", res_yt)
        self.assertIn("সার্চ করা হচ্ছে", res_yt)

        res_gg = CommandProcessor.process_command("গুগলে পাইথন কি সার্চ করো")
        self.assertIn("গুগলে", res_gg)
        self.assertIn("সার্চ করা হচ্ছে", res_gg)

        # 5. Call by keyword
        res_call = CommandProcessor.process_command("বাবা কে কল দাও")
        self.assertIn("কল করা হচ্ছে", res_call)

        # 6. Direct 11-digit call
        res_direct_num = CommandProcessor.process_command("০১৭১১০০০০০১")
        self.assertIn("01711000001", res_direct_num)

        # 7. Scrolling
        self.assertEqual(CommandProcessor.process_command("উপরে যাও"), "উপরে যাওয়া হচ্ছে")
        self.assertEqual(CommandProcessor.process_command("নিচে নামো"), "নিচে যাওয়া হচ্ছে")

        # 8. Battery
        res_bat = CommandProcessor.process_command("ল্যাপটপের চার্জ কত আছে")
        self.assertIn("চার্জ", res_bat)

        # 9. Greetings
        self.assertTrue(CommandProcessor.is_greeting("হ্যালো"))
        self.assertTrue(CommandProcessor.is_greeting("hello"))

        # 10. App opening
        res_app = CommandProcessor.process_command("নোটপ্যাড ওপেন করো")
        self.assertIn("notepad ওপেন করা হচ্ছে", res_app)

    def test_desktop_automation_clipboard(self):
        text = "পরীক্ষামূলক বাংলা লেখা"
        success = DesktopAutomationHelper.set_clipboard_text(text)
        self.assertTrue(success)

    @patch("webbrowser.open")
    def test_browser_agent_subsystem(self, mock_web_open):
        mock_web_open.return_value = True

        settings = get_browser_settings()
        self.assertIn("browser_type", settings)
        self.assertIn("repo_path", settings)

        fallback_result = BrowserFallbackAgent.execute_basic_task("আজকের আবহাওয়ার খবর")
        self.assertIn("ব্রাউজারে", fallback_result)

    def test_document_intelligence_subsystem(self):
        doc_settings = get_document_settings()
        self.assertIn("supported_extensions", doc_settings)
        self.assertIn("render_dpi", doc_settings)
        self.assertIn("repo_path", doc_settings)

        # Resolve sample document
        doc_path = DocumentTaskRunner.resolve_document_path("test_sample.md")
        self.assertIsNotNone(doc_path)
        self.assertTrue(doc_path.exists())

        # Test reading sample document
        res = DocumentFallbackReader.read_text_document(str(doc_path))
        self.assertIn("file_name", res)
        self.assertEqual(res["file_name"], "test_sample.md")
        self.assertIn("VoiceMate", res["plain_text"])

    @patch("webbrowser.open")
    def test_playwright_subsystem(self, mock_web_open):
        mock_web_open.return_value = True

        pw_settings = get_playwright_settings()
        self.assertIn("default_browser", pw_settings)
        self.assertIn("repo_path", pw_settings)
        self.assertIn("profiles_dir", pw_settings)

        # 1. Fallback YouTube play
        res_yt = PlaywrightFallbackAgent.play_youtube_video("রবীন্দ্রসংগীত")
        self.assertTrue(res_yt["success"])
        self.assertEqual(res_yt["action"], "play_youtube")
        self.assertIn("youtube.com", res_yt["url"])

        # 2. Fallback Web search
        res_search = PlaywrightFallbackAgent.search_web("পাইথন প্রোগ্রামিং")
        self.assertTrue(res_search["success"])
        self.assertEqual(res_search["action"], "search_web")

        # 3. Task Runner Parser
        parsed_play = PlaywrightTaskRunner._parse_and_execute("ইউটিউবে নজরুলগীতি প্লে করো")
        self.assertEqual(parsed_play["action"], "play_youtube")

        parsed_shot = PlaywrightTaskRunner._parse_and_execute("ওয়েব স্ক্রিনশট নাও https://github.com")
        self.assertEqual(parsed_shot["action"], "screenshot")

    def test_canvas_subsystem(self):
        settings = get_canvas_settings()
        self.assertIn("repo_path", settings)
        self.assertIn("workspace_dir", settings)
        self.assertIn("canvas_port", settings)

        # 1. Event Stream
        stream = CanvasEventStream.get_instance()
        received_events = []
        def listener(ev):
            received_events.append(ev)
        stream.subscribe(listener)
        stream.emit(EventKind.THINKING, "টেস্টিং ইভেন্ট")
        self.assertTrue(len(received_events) > 0)
        self.assertEqual(received_events[-1].kind, EventKind.THINKING)
        stream.unsubscribe(listener)

        # 2. Workspace Safety Checks
        self.assertTrue(CanvasWorkspaceRunner.is_safe_command("dir"))
        self.assertTrue(CanvasWorkspaceRunner.is_safe_command("python --version"))
        self.assertFalse(CanvasWorkspaceRunner.is_safe_command("format c:"))
        self.assertFalse(CanvasWorkspaceRunner.is_safe_command("rm -rf /"))

        # 3. Terminal Execution
        term_res = CanvasWorkspaceRunner.execute_terminal_command("echo hello_openhands")
        self.assertTrue(term_res["success"])
        self.assertIn("hello_openhands", term_res["output"])

        # 4. Codebase Audit
        audit_res = CanvasWorkspaceRunner.audit_codebase()
        self.assertTrue(audit_res["success"])
        self.assertTrue(audit_res["valid_files"] > 0)
        self.assertEqual(len(audit_res["syntax_errors"]), 0)

        # 5. File Tree
        tree_res = CanvasWorkspaceRunner.get_file_tree(max_depth=1)
        self.assertTrue(tree_res["success"])
        self.assertTrue(any(x in tree_res["tree"] for x in ["voicemate-main", "ORION-a-Voice-Assistant-", "src"]))

        # 6. Task Runner Parser
        parsed_audit = CanvasTaskRunner._parse_and_execute("কোড অডিট করো")
        self.assertTrue(parsed_audit["success"])

    def test_coder_subsystem(self):
        coder_settings = get_coder_settings()
        self.assertIn("repo_path", coder_settings)
        self.assertIn("workspace_dir", coder_settings)
        self.assertIn("backups_dir", coder_settings)

        # 1. SearchReplaceEngine - Find Blocks
        sample_edit = """calculator.py
<<<<<<< SEARCH
def add(a, b):
    return a + b
=======
def add(a, b):
    return a + b

def multiply(a, b):
    return a * b
>>>>>>> REPLACE"""
        blocks = SearchReplaceEngine.find_original_update_blocks(sample_edit)
        self.assertEqual(len(blocks), 1)
        fname, search, replace = blocks[0]
        self.assertEqual(fname, "calculator.py")
        self.assertIn("def add", search)
        self.assertIn("def multiply", replace)

        # 2. SearchReplaceEngine - Apply Replacement
        original_code = "def add(a, b):\n    return a + b\n"
        new_code, success, strategy = SearchReplaceEngine.apply_replacement(original_code, search, replace)
        self.assertTrue(success)
        self.assertIn("def multiply", new_code)

        # 3. RepoMap Generator
        map_res = RepoMapGenerator.generate_repo_map(max_files=10)
        self.assertTrue(map_res["success"])
        self.assertTrue(map_res["scanned_files"] > 0)
        self.assertIn("class ", map_res["repo_map"])

        # 4. GitSafetyManager Backup
        dummy_file = Path(__file__).resolve()
        backup_path = GitSafetyManager.create_backup(dummy_file)
        self.assertTrue(backup_path.exists())
        self.assertTrue(backup_path.stat().st_size > 0)

        # 5. Task Runner Parser
        parsed_map = CoderTaskRunner._parse_and_execute("রেপো ম্যাপ তৈরি করো")
        self.assertTrue(parsed_map["success"])

    def test_docling_subsystem(self):
        docling_settings = get_docling_settings()
        self.assertIn("repo_path", docling_settings)
        self.assertIn("output_dir", docling_settings)
        self.assertIn("supported_extensions", docling_settings)

        # 1. Resolve sample document
        sample_path = DoclingConverter.resolve_file_path("test_sample.md")
        self.assertIsNotNone(sample_path)
        self.assertTrue(sample_path.exists())

        # 2. Conversion & Markdown Export
        res = DoclingConverter.convert_file("test_sample.md", export_chunks=True)
        self.assertTrue(res["success"])
        self.assertIn("markdown", res)
        self.assertIn("VoiceMate", res["markdown"])
        self.assertTrue("chunks" in res)
        self.assertTrue(len(res["chunks"]) > 0)

        # 3. Hybrid Chunker (Pattern C)
        test_md = "# Introduction\nVoiceMate is an assistant.\n\n## Subsystem\nDocling handles multimodal parsing."
        chunks = DoclingHybridChunker.chunk(test_md, max_tokens=100)
        self.assertTrue(len(chunks) > 0)
        self.assertIn("headings", chunks[0])

        # 4. Task Runner Parser
        parsed_chunk_task = DoclingTaskRunner._parse_and_execute("ডকুমেন্ট চাংক করো test_sample.md")
        self.assertTrue(parsed_chunk_task["success"])

    def test_n8n_subsystem(self):
        settings = get_n8n_settings()
        self.assertIn("repo_path", settings)
        self.assertIn("workflows_dir", settings)
        self.assertIn("webhook_url", settings)
        self.assertEqual(settings["port"], 5678)

        # 1. Starter Workflow Generation (Step 2)
        wf_path = N8nWorkflowTemplate.export_starter_workflow()
        self.assertTrue(wf_path.exists())
        self.assertTrue(wf_path.stat().st_size > 0)

        # 2. Emulate Local Workflow (Fallback)
        res_mail = N8nFallbackAgent.emulate_local_workflow("টিমকে ইমেইল পাঠাও")
        self.assertTrue(res_mail["success"])
        self.assertEqual(res_mail["action"], "email_emulation")
        self.assertIn("ইমেইল", res_mail["message"])

        res_notion = N8nFallbackAgent.emulate_local_workflow("নোশনে সেভ করো")
        self.assertTrue(res_notion["success"])
        self.assertEqual(res_notion["action"], "notion_emulation")

        # 3. Task Runner Parser
        parsed_status = N8nTaskRunner._parse_and_execute("এনএইটেন স্ট্যাটাস")
        self.assertTrue(parsed_status["success"])
        self.assertIn("সার্ভার বর্তমানে", parsed_status["message"])

    def test_fastapi_subsystem(self):
        # 1. Config & Network Settings
        self.assertEqual(API_PORT, 8080)
        self.assertIn("8080", API_DOCS_URL)
        self.assertIn("/docs", API_DOCS_URL)

        # 2. Schemas & Type Validation (Pydantic v2)
        cmd_req = CommandRequest(command="সময় কত", source="mobile")
        self.assertEqual(cmd_req.command, "সময় কত")
        self.assertEqual(cmd_req.source, "mobile")

        cmd_resp = CommandResponse(
            status="success",
            action_taken="time",
            spoken_reply="এখন সময় হলো রাত ১২টা"
        )
        self.assertEqual(cmd_resp.status, "success")
        self.assertEqual(cmd_resp.action_taken, "time")

        sys_resp = SystemStatusResponse(
            cpu_percent=5.5,
            battery_percent=94,
            is_plugged=True,
            memory_percent=45.0,
            active_modules=["voice_agent", "fastapi_gateway"]
        )
        self.assertEqual(sys_resp.battery_percent, 94)
        self.assertTrue(sys_resp.is_plugged)

        auto_req = AutomationTaskRequest(
            subsystem="browser",
            task="গুগলে সার্চ করো",
            payload={"headless": False}
        )
        self.assertEqual(auto_req.subsystem, "browser")

        webhook_event = WebhookPayload(
            event="incoming_email",
            data={"sender": "boss@company.com", "subject": "Urgent Meeting"}
        )
        self.assertEqual(webhook_event.event, "incoming_email")

        # 3. Server Controller Status Inspection
        status = APIServerController.get_status()
        self.assertIn("host", status)
        self.assertIn("port", status)
        self.assertIn("docs_url", status)
        self.assertEqual(status["port"], 8080)

        # 4. Fallback Handler (Zero-Crash Emulation)
        fallback_res = APIFallbackHandler.execute_local_command("সময় কত")
        self.assertEqual(fallback_res["status"], "success_local_fallback")
        self.assertIn("সময়", fallback_res["spoken_reply"])

        fallback_sys = APIFallbackHandler.get_local_system_status()
        self.assertEqual(fallback_sys["status"], "offline_local")
        self.assertFalse(fallback_sys["server_running"])

    def test_langgraph_brain_subsystem(self):
        # 1. Config & Settings
        settings = get_brain_settings()
        self.assertIn("repo_path", settings)
        self.assertIn("session_id", settings)
        self.assertEqual(settings["max_retries"], 2)

        # 2. StateGraph Compilation & Architecture
        graph = LangGraphBrainController.get_graph()
        self.assertIsNotNone(graph)
        status = LangGraphBrainController.get_status()
        self.assertTrue(status["graph_compiled"])
        self.assertIn("supervisor", status["nodes"])
        self.assertIn("browser_worker", status["nodes"])
        self.assertIn("document_worker", status["nodes"])
        self.assertIn("coding_worker", status["nodes"])

        # 3. Graph Invocation (Multi-turn turn execution)
        turn_result = LangGraphBrainController.execute_turn("আজকের তারিখ কত", thread_id="test_session_1")
        self.assertTrue(turn_result["success"])
        self.assertEqual(turn_result["thread_id"], "test_session_1")
        self.assertIn("তারিখ", turn_result["final_reply"])

        # 4. Human-In-The-Loop Safety Guardrails
        confirm_turn = LangGraphBrainController.execute_turn("সব ডেটা ডিলিট করো", thread_id="test_session_safe")
        self.assertTrue(confirm_turn["success"])
        self.assertTrue(confirm_turn["requires_confirmation"])
        self.assertIn("নিশ্চিত", confirm_turn["final_reply"])

        # 5. Fallback Orchestrator (Zero-Crash Emulation)
        fallback_res = BrainFallbackOrchestrator.execute_fallback_turn("ল্যাপটপের চার্জ কত")
        self.assertTrue(fallback_res["success"])
        self.assertTrue(fallback_res["fallback"])
        self.assertIn("চার্জ", fallback_res["final_reply"])

    def test_permission_and_messaging_helpers(self):
        from src.helpers.permission_helper import PermissionHelper
        from src.helpers.sms_helper import SmsHelper

        # 1. Permission & Capability Diagnostics
        status = PermissionHelper.get_system_status()
        self.assertIn("os", status)
        self.assertIn("python_version", status)
        self.assertIn("has_mic", status)
        self.assertIn("has_camera", status)

        diag = PermissionHelper.get_diagnostics()
        self.assertIn("diagnostic_notes", diag)

        # 2. SMS Helper URL formatting
        msg_res = SmsHelper.send_sms("01711000001", "Hello VoiceMate")
        self.assertIn("উইন্ডো খোলা হয়েছে", msg_res)

        # 3. SMS routing in CommandProcessor
        cmd_res = CommandProcessor.process_command("মেসেজ পাঠাও ০১৭১১০০০০০১ কেমন আছেন")
        self.assertIn("উইন্ডো খোলা হয়েছে", cmd_res)

if __name__ == "__main__":
    unittest.main()
