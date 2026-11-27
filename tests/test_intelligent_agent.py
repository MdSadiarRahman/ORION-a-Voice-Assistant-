"""
VoiceMate Intelligence - Automated Test Suite.
Tests Natural Language Understanding (Bangla, English, Banglish),
Intelligent YouTube Interaction Workflow, Context Management, Fast Routing,
Safety Guard Protocol, and Action Verification.
"""
import unittest
import time
from src.intelligence.intent_engine import Intent, IntentEngine
from src.intelligence.fast_router import FastCommandRouter
from src.intelligence.context_manager import ContextManager
from src.intelligence.ollama_client import OllamaClient
from src.intelligence.safety_guard import SafetyGuard
from src.intelligence.action_verifier import ActionVerifier
from src.intelligence.decision_engine import HybridDecisionEngine
from src.helpers.media_controller import MediaController


class TestIntelligentAgent(unittest.TestCase):
    def setUp(self):
        self.engine = HybridDecisionEngine()

    def test_nlu_song_variations(self):
        """1. Natural Language Understanding for song requests across dialects."""
        test_phrases = [
            ("Play Kamariya song", "Kamariya"),
            ("Kamariya chalao", "Kamariya"),
            ("একটা কামারিয়া গান চালাও", "কামারিয়া"),
            ("I want to listen to Kamariya", "Kamariya"),
            ("Can you play Kamariya for me?", "Kamariya"),
            ("ইউটিউবে রবীন্দ্রসংগীত বাজাও", "রবীন্দ্রসংগীত"),
            ("গান বাজাও", "bangla top song"),
        ]

        for phrase, expected_song in test_phrases:
            intent_res, reply = self.engine.process_query(phrase)
            self.assertEqual(intent_res.intent, Intent.PLAY_MUSIC, f"Failed on: {phrase}")
            extracted = intent_res.parameters.get("song_name", "")
            self.assertTrue(
                expected_song.lower() in extracted.lower() or extracted.lower() in expected_song.lower(),
                f"For query '{phrase}', expected '{expected_song}', got '{extracted}'"
            )
            self.assertIn("ইউটিউবে", reply)

    def test_youtube_multi_turn_workflow(self):
        """2. Multi-turn YouTube conversational interaction."""
        # Turn 1: User says "Open YouTube"
        res1, reply1 = self.engine.process_query("Open YouTube")
        self.assertEqual(res1.intent, Intent.OPEN_APPLICATION)
        self.assertIn("ইউটিউব ওপেন করা হয়েছে", reply1)
        self.assertEqual(self.engine.context.active_app, "youtube")
        self.assertEqual(self.engine.context.awaiting_slot, "youtube_query")

        # Turn 2: User responds with song title "Kamariya"
        res2, reply2 = self.engine.process_query("Kamariya")
        self.assertEqual(res2.intent, Intent.PLAY_MUSIC)
        song_name_lower = res2.parameters.get("song_name", "").lower()
        self.assertTrue("কামারিয়া" in song_name_lower or "kamariya" in song_name_lower)
        self.assertIn("ইউটিউবে", reply2)

        # Turn 3: User commands "Pause"
        res3, reply3 = self.engine.process_query("Pause")
        self.assertEqual(res3.intent, Intent.MEDIA_CONTROL)
        self.assertEqual(res3.action, "pause")
        self.assertIn("পজ", reply3)

        # Turn 4: User commands "Volume baraw" (Banglish)
        res4, reply4 = self.engine.process_query("Volume baraw")
        self.assertEqual(res4.intent, Intent.VOLUME_CONTROL)
        self.assertEqual(res4.parameters.get("direction"), "up")
        self.assertIn("বাড়ানো", reply4)

        # Turn 5: User commands "Volume komaw" (Banglish)
        res5, reply5 = self.engine.process_query("Volume komaw")
        self.assertEqual(res5.intent, Intent.VOLUME_CONTROL)
        self.assertEqual(res5.parameters.get("direction"), "down")
        self.assertIn("কমানো", reply5)

        # Turn 6: User commands "Resume playback"
        res6, reply6 = self.engine.process_query("Resume playback")
        self.assertEqual(res6.intent, Intent.MEDIA_CONTROL)
        self.assertEqual(res6.action, "resume")
        self.assertIn("পুনরায় চালু", reply6)

    def test_fast_router_speed(self):
        """3. Performance test: Fast Command Router must execute in under 15ms."""
        start = time.perf_counter()
        for _ in range(50):
            FastCommandRouter.match("Play Kamariya song")
            FastCommandRouter.match("সময় কত")
            FastCommandRouter.match("Pause")
            FastCommandRouter.match("Volume up")
        elapsed = time.perf_counter() - start
        avg_per_call = (elapsed / 200) * 1000
        self.assertLess(avg_per_call, 15.0, f"Router too slow: {avg_per_call:.2f}ms")

    def test_safety_guard_protocol(self):
        """4. Safety Guard enforces explicit confirmation for destructive operations."""
        # Unsafe file deletion query
        res, reply = self.engine.process_query("delete file report.docx")
        self.assertIn("সতর্কতা", reply)
        self.assertEqual(self.engine.context.awaiting_slot, "confirmation")

        # Confirming with "হ্যাঁ"
        res_conf, reply_conf = self.engine.process_query("হ্যাঁ")
        self.assertEqual(res_conf.intent, Intent.CONFIRM_ACTION)
        self.assertIn("অনুমতি পাওয়া গেছে", reply_conf)

        # Testing cancellation
        res_del2, _ = self.engine.process_query("মুছে ফেলো ফাইল notes.txt")
        self.assertEqual(self.engine.context.awaiting_slot, "confirmation")
        res_canc, reply_canc = self.engine.process_query("না")
        self.assertEqual(res_canc.intent, Intent.CANCEL_ACTION)
        self.assertIn("বাতিল", reply_canc)

    def test_action_verifier(self):
        """5. Action Verifier accurately validates action outcomes."""
        # Valid watch URL
        ok, msg = ActionVerifier.verify_youtube_playback("https://www.youtube.com/watch?v=12345", "Test Song")
        self.assertTrue(ok)
        self.assertIn("সফলভাবে চালু হয়েছে", msg)

        # Empty watch URL
        bad_ok, bad_msg = ActionVerifier.verify_youtube_playback("", "Test Song")
        self.assertFalse(bad_ok)

        # App launch verification
        app_ok, app_msg = ActionVerifier.verify_app_launch("notepad", "notepad ওপেন করা হচ্ছে")
        self.assertTrue(app_ok)

        app_fail, _ = ActionVerifier.verify_app_launch("fake_app", "অ্যাপ্লিকেশনটি খুঁজে পাওয়া যায়নি")
        self.assertFalse(app_fail)

    def test_ollama_graceful_fallback(self):
        """6. Ollama client falls back gracefully when offline without crashing."""
        client = OllamaClient(host="http://localhost:99999", timeout_seconds=0.5)
        self.assertFalse(client.is_available())
        res = client.analyze_query("Something complex")
        self.assertIsNone(res)


if __name__ == "__main__":
    unittest.main()
