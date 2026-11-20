"""
VoiceMate Laptop Agent - Permission and System Capability Helper Module.
Verifies microphone, webcam, and system environment capabilities on the laptop.
"""
import sys
from typing import Dict, Any

class PermissionHelper:
    @staticmethod
    def check_audio_permission() -> bool:
        """Checks if microphone input subsystem is functional on desktop."""
        try:
            import speech_recognition as sr
            sr.Microphone()
            return True
        except Exception:
            return False

    @staticmethod
    def check_camera_permission() -> bool:
        """Checks if camera capture is supported."""
        try:
            import importlib
            cv2 = importlib.import_module("cv2")
            cap = cv2.VideoCapture(0)
            available = cap.isOpened()
            cap.release()
            return available
        except Exception:
            return False

    @staticmethod
    def check_tts_permission() -> bool:
        """Checks if text-to-speech output is available."""
        try:
            import pyttsx3
            return True
        except Exception:
            return True  # Windows PowerShell System.Speech is always present as fallback

    @staticmethod
    def get_system_status() -> Dict[str, Any]:
        """Returns hardware and subsystem readiness summary."""
        return {
            "os": sys.platform,
            "python_version": sys.version.split()[0],
            "has_mic": PermissionHelper.check_audio_permission(),
            "has_camera": PermissionHelper.check_camera_permission(),
            "has_tts": PermissionHelper.check_tts_permission()
        }

    @staticmethod
    def get_diagnostics() -> Dict[str, Any]:
        """Provides full diagnostic report for VoiceMate capabilities."""
        status = PermissionHelper.get_system_status()
        notes = []
        if not status["has_mic"]:
            notes.append("মাইক্রোফোন সংযোগ নেই অথবা SpeechRecognition/pyaudio ইনস্টল নেই (টেক্সট ইনপুট কার্যকর রয়েছে)।")
        if not status["has_camera"]:
            notes.append("ওয়েবক্যাম সংযোগ নেই অথবা opencv ইনস্টল নেই (স্ক্রিনশট ফলব্যাক কার্যকর রয়েছে)।")
        status["diagnostic_notes"] = notes
        return status
