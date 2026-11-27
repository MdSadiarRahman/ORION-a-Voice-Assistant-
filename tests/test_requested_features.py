import sys
import tempfile
import unittest
import urllib.error
import zipfile
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.document_intelligence.document_answer_service import DocumentAnswerService
from src.intelligence.requested_feature_router import RequestedFeatureRouter
from src.product_agent.product_price_search import ProductPriceSearch
from src.agent_service import AgentService
from src.helpers.desktop_automation_helper import DesktopAutomationHelper
from src.helpers.app_helper import AppHelper
from src.ui.web_window import VoiceMateBridge


class TestRequestedFeatureRouter(unittest.TestCase):
    def test_routes_supported_product_price_request_with_clean_product_name(self):
        response = RequestedFeatureRouter.process("What is the price of HP laptop?")

        self.assertEqual(response, "ACTION_PRODUCT_PRICE|hp laptop")

    def test_normalizes_bengali_product_name_and_digits_for_retailer_search(self):
        response = RequestedFeatureRouter.process("আইফোন ১৬ এর দাম কত?")

        self.assertEqual(response, "ACTION_PRODUCT_PRICE|iphone 16")

    def test_opens_bengali_app_alias(self):
        with patch(
            "src.intelligence.requested_feature_router.AppHelper.open_app",
            return_value="জিমেইল ওপেন করা হচ্ছে",
        ) as open_app:
            response = RequestedFeatureRouter.process("জিমেইল খোলো")

        self.assertEqual(response, "জিমেইল ওপেন করা হচ্ছে")
        open_app.assert_called_once_with("জিমেইল")

    def test_gmail_web_fallback_opens_the_browser(self):
        with patch.object(AppHelper, "get_all_installed_apps", return_value=[]), \
             patch("src.helpers.app_helper.AppPreferenceHelper.is_app_allowed", return_value=True), \
             patch("webbrowser.open", return_value=True) as open_browser:
            response = AppHelper.open_app("Gmail")

        self.assertIn("ওপেন করা হচ্ছে", response)
        open_browser.assert_called_once_with("https://mail.google.com")

    def test_missing_vscode_command_is_not_reported_as_opened(self):
        with patch.object(AppHelper, "get_all_installed_apps", return_value=[]), \
             patch("src.helpers.app_helper.AppPreferenceHelper.is_app_allowed", return_value=True), \
             patch("src.helpers.app_helper.shutil.which", return_value=None):
            response = AppHelper.open_app("VS Code")

        self.assertIn("খুঁজে পাওয়া যায়নি", response)

    def test_rejects_features_outside_the_requested_scope(self):
        response = RequestedFeatureRouter.process("play music")

        self.assertEqual(response, RequestedFeatureRouter.OUT_OF_SCOPE_MESSAGE)


class TestVoiceTypingScope(unittest.TestCase):
    def _service(self, typing_mode=True):
        service = AgentService.__new__(AgentService)
        service.is_typing_mode = typing_mode
        service.is_waiting_for_search = False
        service.search_target = ""
        service._is_echo_of_assistant = lambda text: False
        service._notify_state = lambda message="": None
        service.speak = Mock()
        return service

    def test_dictated_send_word_is_typed_without_sending(self):
        service = self._service()
        with patch.object(DesktopAutomationHelper, "append_text") as append_text:
            with patch.object(DesktopAutomationHelper, "click_send") as click_send:
                service.process_results("send")

        append_text.assert_called_once_with("send ")
        click_send.assert_not_called()

    def test_stop_phrase_exits_typing_mode(self):
        service = self._service()
        service.process_results("টাইপিং বন্ধ")

        self.assertFalse(service.is_typing_mode)

    def test_document_action_runs_in_background_instead_of_speaking_marker(self):
        service = self._service(typing_mode=False)
        with patch(
            "src.agent_service.CommandProcessor.process_command",
            return_value="ACTION_DOCUMENT_QA|question from report.pdf",
        ), patch("src.agent_service.threading.Thread") as thread:
            service.process_results("answer from report.pdf")

        self.assertNotIn("ACTION_DOCUMENT_QA", service.speak.call_args.args[0])
        thread.return_value.start.assert_called_once()

    def test_unrecognized_marker_cannot_reach_legacy_action_engine(self):
        service = self._service(typing_mode=False)
        service.decision_engine = Mock()
        with patch(
            "src.agent_service.CommandProcessor.process_command",
            return_value="UNKNOWN_COMMAND",
        ):
            service.process_results("unsupported command")

        service.decision_engine.process_query.assert_not_called()


class TestVoiceMateBridgeScope(unittest.TestCase):
    def test_bridge_rejects_removed_toolkit_actions(self):
        bridge = VoiceMateBridge(agent=None)
        bridge.send_command = Mock(return_value={"status": "ok"})

        result = bridge.run_toolkit_action("assignment_solver", "solve a file")

        self.assertEqual(result["status"], "error")
        bridge.send_command.assert_not_called()

    def test_bridge_maps_allowed_price_action_to_scoped_command(self):
        bridge = VoiceMateBridge(agent=None)
        bridge.send_command = Mock(return_value={"status": "ok"})

        result = bridge.run_toolkit_action("product_price", "HP laptop")

        self.assertEqual(result["status"], "ok")
        bridge.send_command.assert_called_once_with("price of HP laptop")


class TestProductPriceSearch(unittest.TestCase):
    def test_compares_only_matching_live_listing_prices(self):
        pages = {
            "Star Tech": """
              <div class="p-item">
                <a class="p-item-name" href="/hp-15s">HP 15s Laptop 8GB</a>
                <div class="p-item-price"><span class="price-new">55,000৳</span>
                  <span class="price-old">60,000৳</span></div>
              </div>
              <div class="p-item">
                <a class="p-item-name" href="/hp-case">HP laptop case</a>
                <div class="p-item-price"><span class="price-new">1,500৳</span></div>
              </div>
              <div class="p-item">
                <a class="p-item-name" href="/connector">UGREEN DC Connector for HP Laptop</a>
                <div class="p-item-price"><span class="price-new">400৳</span></div>
              </div>
            """,
            "UCC": """
              <div class="product-thumb">
                <a href="/hp-15s-laptop"><span class="product-name">HP 15s Laptop 8GB</span></a>
                <span class="price-normal">৳58,000.00</span>
              </div>
            """,
            "Global Brand": "<html><body>No matching products</body></html>",
        }

        def fake_fetcher(retailer, url):
            if retailer.name not in pages:
                raise urllib.error.URLError("test source unavailable")
            return pages[retailer.name]

        result = ProductPriceSearch.search("HP laptop", fetcher=fake_fetcher)

        self.assertTrue(result["success"])
        self.assertEqual(len(result["prices"]), 2)
        self.assertEqual(result["prices"][0].price_bdt, 55000)
        self.assertIn("2টি retailer source", result["message"])
        self.assertIn("যাচাইয়ের সময়", result["message"])
        self.assertEqual(result["prices"][0].retailer, "Star Tech")
        self.assertEqual(result["sources_without_matches"], ["Global Brand"])
        self.assertEqual(len(result["source_errors"]), 1)


class TestLocalDocumentAnswers(unittest.TestCase):
    @staticmethod
    def _write_docx(path: Path):
        document_xml = b"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
          <w:body>
            <w:p><w:r><w:t>Photosynthesis is the process plants use to turn light into stored chemical energy.</w:t></w:r></w:p>
          </w:body>
        </w:document>"""
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("word/document.xml", document_xml)

    def test_answers_from_local_docx_and_cites_the_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_docx(root / "science.docx")
            with patch("src.document_intelligence.document_answer_service.OllamaClient") as ollama:
                ollama.return_value.is_available.return_value = True
                ollama.return_value.answer_from_context.return_value = (
                    "Plants use light to store energy as chemical energy."
                )
                result = DocumentAnswerService.answer(
                    "answer from document: what is photosynthesis?",
                    roots=[root],
                )

        self.assertIn("Plants use light", result)
        self.assertIn("science.docx", result)

    def test_reports_local_evidence_when_ollama_is_unavailable(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self._write_docx(root / "science.docx")
            with patch("src.document_intelligence.document_answer_service.OllamaClient") as ollama:
                ollama.return_value.is_available.return_value = False
                result = DocumentAnswerService.answer(
                    "answer from document: what is photosynthesis?",
                    roots=[root],
                )

        self.assertIn("AI model দিয়ে উত্তর তৈরি করা যায়নি", result)
        self.assertIn("stored chemical energy", result)
        self.assertIn("science.docx", result)


if __name__ == "__main__":
    unittest.main()
