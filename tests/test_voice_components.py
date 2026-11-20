"""
VoiceMate Laptop Agent - Voice and TTS Components Unit Tests.
Verifies TTS and VoiceRecognizer initialization, language detection, and audio capture pipeline.
"""
import unittest
from src.helpers.tts_helper import TtsHelper
from src.helpers.voice_recognizer_helper import VoiceRecognizerHelper, SoundDeviceMicrophone


class TestVoiceComponents(unittest.TestCase):
    def test_tts_helper_init(self):
        tts = TtsHelper()
        self.assertIsNotNone(tts)
        self.assertFalse(tts.is_speaking)

    def test_tts_bengali_detection(self):
        tts = TtsHelper()
        self.assertTrue(tts._is_bengali("ভয়েস মেট প্রস্তুত"))
        self.assertFalse(tts._is_bengali("Hello world 123"))

    def test_voice_recognizer_init(self):
        errors = []
        results = []
        rec = VoiceRecognizerHelper(
            on_result=lambda r: results.append(r),
            on_error=lambda e: errors.append(e),
            language="bn-BD"
        )
        self.assertIsNotNone(rec)
        self.assertEqual(rec.language, "bn-BD")
        self.assertFalse(rec.is_listening)

    def test_sounddevice_mic_init(self):
        sd_mic = SoundDeviceMicrophone(sample_rate=16000)
        self.assertIsNotNone(sd_mic)
        self.assertEqual(sd_mic.sample_rate, 16000)


if __name__ == "__main__":
    unittest.main()
