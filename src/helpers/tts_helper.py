"""
VoiceMate Laptop Agent - Text-to-Speech (TTS) Helper Module.
Provides high-fidelity, thread-safe speech output with support for authentic Bengali (via gTTS)
and native English (via pyttsx3 and Windows SAPI COM) with automatic fallback.
"""
import os
import sys
import tempfile
import base64
import subprocess
import threading
from typing import Optional, Callable


class TtsHelper:
    _speak_lock = threading.Lock()

    def __init__(self, on_start: Optional[Callable] = None, on_done: Optional[Callable] = None):
        self.on_start = on_start
        self.on_done = on_done
        self.is_speaking = False
        self._engine = None
        self._active_proc: Optional[subprocess.Popen] = None
        self._speech_seq = 0
        self._init_engine()

    def _init_engine(self):
        try:
            import pyttsx3
            self._engine = pyttsx3.init()
            self._engine.setProperty('rate', 160)
            self._engine.setProperty('volume', 1.0)
            voices = self._engine.getProperty('voices')
            for voice in voices:
                if 'bengali' in voice.name.lower() or 'bangla' in voice.name.lower():
                    self._engine.setProperty('voice', voice.id)
                    break
        except Exception:
            self._engine = None

    @staticmethod
    def _is_bengali(text: str) -> bool:
        return any('\u0980' <= c <= '\u09FF' for c in text)

    def _speak_bengali_gtts(self, text: str) -> bool:
        """
        Synthesizes authentic Bengali speech using Google TTS and plays it via Windows MediaPlayer.
        """
        try:
            from gtts import gTTS
            tts = gTTS(text=text, lang='bn', slow=False)
            tmp_fd, tmp_path = tempfile.mkstemp(suffix=".mp3")
            os.close(tmp_fd)
            tts.save(tmp_path)

            ps_script = f"""
Add-Type -AssemblyName presentationCore
$player = New-Object System.Windows.Media.MediaPlayer
$player.Volume = 1.0
$player.Open([System.Uri]"{tmp_path.replace(chr(92), '/')}")
$waitCount = 0
while (-not $player.NaturalDuration.HasTimeSpan -and $waitCount -lt 30) {{
    Start-Sleep -Milliseconds 100
    $waitCount++
}}
$player.Play()
while ($player.NaturalDuration.HasTimeSpan -and $player.Position -lt $player.NaturalDuration.TimeSpan) {{
    Start-Sleep -Milliseconds 150
}}
Start-Sleep -Milliseconds 400
$player.Close()
"""
            enc = base64.b64encode(ps_script.encode("utf-16le")).decode("ascii")
            proc = subprocess.Popen(
                ["powershell.exe", "-NoProfile", "-NonInteractive", "-EncodedCommand", enc],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            self._active_proc = proc
            try:
                proc.wait(timeout=45)
            except subprocess.TimeoutExpired:
                proc.kill()
            finally:
                if self._active_proc is proc:
                    self._active_proc = None
            try:
                os.remove(tmp_path)
            except Exception:
                pass
            return True
        except Exception:
            return False

    def _speak_sapi_com(self, text: str) -> bool:
        """
        Native Windows SAPI COM speech synthesizer fallback.
        """
        try:
            escaped = text.replace('"', '`"').replace("'", "''")
            ps_script = f"""
try {{
    $voice = New-Object -ComObject SAPI.SpVoice
    $voice.Speak("{escaped}")
}} catch {{
    exit 1
}}
"""
            enc = base64.b64encode(ps_script.encode("utf-16le")).decode("ascii")
            proc = subprocess.run(
                ["powershell.exe", "-NoProfile", "-NonInteractive", "-EncodedCommand", enc],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=15
            )
            return proc.returncode == 0
        except Exception:
            return False

    def stop_speaking(self):
        """Interrupts any currently playing TTS subprocess."""
        proc = self._active_proc
        if proc is not None:
            try:
                proc.kill()
            except Exception:
                pass
            self._active_proc = None

    def speak(self, text: str, sync: bool = False):
        """
        Speaks the given text using the best available TTS backend.
        Thread-safe and non-blocking by default. Interrupts stale speech when a new utterance arrives.
        """
        if not text:
            return

        self._speech_seq += 1
        my_seq = self._speech_seq
        self.stop_speaking()

        def _worker():
            with self._speak_lock:
                if my_seq != self._speech_seq:
                    return
                self.is_speaking = True
                if self.on_start:
                    try:
                        self.on_start()
                    except Exception:
                        pass

                print(f"[VoiceMate Voice]: {text}", flush=True)
                try:
                    spoken = False

                    # 1. Authentic Bengali TTS via gTTS when Bengali characters are present
                    if self._is_bengali(text):
                        spoken = self._speak_bengali_gtts(text)

                    # 2. Native pyttsx3 engine for offline / English speech
                    if not spoken and self._engine:
                        try:
                            self._engine.say(text)
                            self._engine.runAndWait()
                            spoken = True
                        except Exception:
                            pass

                    # 3. Windows SAPI COM fallback
                    if not spoken:
                        spoken = self._speak_sapi_com(text)
                finally:
                    self.is_speaking = False
                    if self.on_done:
                        try:
                            self.on_done()
                        except Exception:
                            pass

        if sync:
            _worker()
        else:
            t = threading.Thread(target=_worker, daemon=True)
            t.start()

    def shutdown(self):
        self.stop_speaking()
        self.is_speaking = False
        if self._engine:
            try:
                self._engine.stop()
            except Exception:
                pass


# Alias for backward-compatible naming across modules
TTSHelper = TtsHelper
