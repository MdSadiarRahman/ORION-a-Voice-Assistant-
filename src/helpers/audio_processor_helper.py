"""
VoiceMate Laptop Agent - Audio Processor Helper Module.
Provides ambient noise adjustment, gain control, and audio quality enhancement.
"""
from typing import Optional

class AudioProcessorHelper:
    """
    Handles audio enhancement, noise suppression, and gain control for microphone streams.
    """
    def __init__(self):
        self.is_enhancing = False

    def enhance_recognizer(self, recognizer, microphone_source):
        """
        Calibrates the speech recognizer for ambient room noise,
        applying dynamic energy thresholding and gain control.
        """
        try:
            recognizer.adjust_for_ambient_noise(microphone_source, duration=0.8)
            recognizer.dynamic_energy_threshold = True
            recognizer.dynamic_energy_adjustment_damping = 0.15
            recognizer.dynamic_energy_ratio = 1.5
            self.is_enhancing = True
        except Exception:
            self.is_enhancing = False

    def stop_enhancing(self):
        self.is_enhancing = False
