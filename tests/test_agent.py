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

    @patch("src.intelligence.requested_feature_router.AppHelper.open_app")
    @patch("src.intelligence.requested_feature_router.SearchHelper.search_in_google")
    @patch("src.intelligence.requested_feature_router.SearchHelper.search_in_youtube")
    def test_command_processor_queries(self, mock_youtube, mock_google, mock_open_app):
        mock_open_app.return_value = "Gmail ওপেন করা হচ্ছে"
        mock_google.return_value = "গুগলে সার্চ করা হচ্ছে"
        mock_youtube.return_value = "ইউটিউবে সার্চ করা হচ্ছে"

        self.assertEqual(
            CommandProcessor.process_command("টাইপিং মোড চালু করো"),
            "ACTION_START_TYPING",
        )
        self.assertEqual(
            CommandProcessor.process_command("Gmail ওপেন করো"),
            "Gmail ওপেন করা হচ্ছে",
        )
        mock_open_app.assert_called_once_with("Gmail")

        self.assertEqual(
            CommandProcessor.process_command("গুগলে পাইথন সার্চ করো"),
            "গুগলে সার্চ করা হচ্ছে",
        )
        mock_google.assert_called_once_with("পাইথন")
        self.assertEqual(
            CommandProcessor.process_command("ইউটিউবে গান সার্চ করো"),
            "ইউটিউবে সার্চ করা হচ্ছে",
        )
        mock_youtube.assert_called_once_with("গান")

        self.assertEqual(
            CommandProcessor.process_command("HP laptop er dam koto"),
            "ACTION_PRODUCT_PRICE|hp laptop",
        )
        self.assertTrue(
            CommandProcessor.process_command("answer from report.pdf what is revenue")
            .startswith("ACTION_DOCUMENT_QA|")
        )
        self.assertIn("শুধু app খোলা", CommandProcessor.process_command("play music"))
        self.assertIn("শুধু app খোলা", CommandProcessor.process_command("ল্যাপটপের চার্জ কত আছে"))

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
        self.assertIn("শুধু app খোলা", cmd_res)

if __name__ == "__main__":
    unittest.main()
