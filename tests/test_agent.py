"""
Comprehensive Test Suite for VoiceMate Laptop Agent.
Includes tests for Core Voice, System, Desktop, Browser-Use, and Document Intelligence (PyMuPDF).
"""
import unittest
from unittest.mock import patch
from pathlib import Path
import tempfile
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
from src.docling_agent.docling_config import get_docling_settings
from src.docling_agent.docling_converter import DoclingConverter
from src.docling_agent.docling_chunker import DoclingHybridChunker
from src.docling_agent.docling_task_runner import DoclingTaskRunner

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

        # 6. Local PC File Search & Assignment Routing
        res_find_file = CommandProcessor.process_command("আমার পিডিএফ ফাইল খুঁজে দাও")
        self.assertTrue(res_find_file.startswith("ACTION_FIND_FILE|"))

        res_assign = CommandProcessor.process_command("অ্যাসাইনমেন্ট সলভ করে দাও")
        self.assertTrue(res_assign.startswith("ACTION_ASSIGNMENT_TASK|"))

        # 7. YouTube & Google Searches
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
