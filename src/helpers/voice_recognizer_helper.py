"""
VoiceMate Laptop Agent - Voice Recognizer Helper Module.
Handles continuous speech recognition from the laptop microphone for Bengali (bn-BD) and English (en-US).
Supports both standard PyAudio and pure-Python sounddevice microphone capture backends.
Features built-in hardware muting, queue draining, and acoustic echo suppression.
"""
import time
import queue
import threading
from typing import Callable, Optional
import numpy as np


class SoundDeviceMicrophone:
    """
    Continuous audio capture engine using sounddevice.
    Acts as a 100% drop-in alternative to PyAudio on Windows with Python 3.14.
    Includes active mute and queue drain for echo cancellation.
    """
    def __init__(self, sample_rate: int = 16000, chunk_duration: float = 0.1):
        self.sample_rate = sample_rate
        self.chunk_samples = int(sample_rate * chunk_duration)
        self.audio_queue = queue.Queue()
        self.stream = None
        self._is_active = False
        self.is_muted = False

    def _audio_callback(self, indata, frames, time_info, status):
        if self._is_active and not self.is_muted:
            self.audio_queue.put(indata.copy())

    def start(self):
        import sounddevice as sd
        self._is_active = True
        self.is_muted = False
        self.stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype='int16',
            blocksize=self.chunk_samples,
            callback=self._audio_callback
        )
        self.stream.start()

    def stop(self):
        self._is_active = False
        self.is_muted = True
        if self.stream:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception:
                pass
            self.stream = None

    def drain(self):
        """Discards all pending audio frames from the queue."""
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                break

    def listen_phrase(
        self,
        stop_checker: Callable[[], bool],
        is_speaking_checker: Optional[Callable[[], bool]] = None,
        timeout: float = 5.0,
        phrase_time_limit: float = 10.0,
        silence_limit: float = 0.8
    ):
        import speech_recognition as sr

        # 1. If assistant is speaking right now, mute mic and wait until speaking finishes
        if is_speaking_checker and is_speaking_checker():
            self.is_muted = True
            self.drain()
            while is_speaking_checker() and not stop_checker():
                time.sleep(0.08)
            # Acoustic cooldown delay to allow speaker reverberation in the room to fade
            time.sleep(0.35)
            self.drain()
            self.is_muted = False

        self.drain()

        # Quick calibration to assess ambient background noise
        calib_chunks = []
        calib_start = time.time()
        while time.time() - calib_start < 0.25 and not stop_checker():
            if is_speaking_checker and is_speaking_checker():
                self.is_muted = True
                self.drain()
                return None
            try:
                chunk = self.audio_queue.get(timeout=0.1)
                data = chunk.flatten().astype(float)
                rms = np.sqrt(np.mean(data**2))
                calib_chunks.append(rms)
            except queue.Empty:
                pass

        avg_noise = sum(calib_chunks) / len(calib_chunks) if calib_chunks else 200.0
        energy_threshold = max(avg_noise * 1.5, 300.0)

        phrase_chunks = []
        is_user_speaking = False
        silence_start = None
        listen_start = time.time()
        speech_start = None

        while not stop_checker():
            # If assistant started speaking mid-turn, immediately discard and mute!
            if is_speaking_checker and is_speaking_checker():
                self.is_muted = True
                self.drain()
                return None

            if not is_user_speaking and (time.time() - listen_start > timeout):
                return None

            try:
                chunk = self.audio_queue.get(timeout=0.2)
            except queue.Empty:
                continue

            data = chunk.flatten().astype(float)
            rms = np.sqrt(np.mean(data**2))

            if rms > energy_threshold:
                if not is_user_speaking:
                    is_user_speaking = True
                    speech_start = time.time()
                silence_start = None
                phrase_chunks.append(chunk.tobytes())
            elif is_user_speaking:
                phrase_chunks.append(chunk.tobytes())
                if silence_start is None:
                    silence_start = time.time()
                elif time.time() - silence_start >= silence_limit:
                    break

            if is_user_speaking and speech_start and (time.time() - speech_start > phrase_time_limit):
                break

        if not phrase_chunks:
            return None

        return sr.AudioData(b"".join(phrase_chunks), self.sample_rate, 2)


class VoiceRecognizerHelper:
    def __init__(
        self,
        on_result: Callable[[str], None],
        on_error: Callable[[str], None],
        on_ready: Optional[Callable[[], None]] = None,
        language: str = "bn-BD",
        is_speaking_checker: Optional[Callable[[], bool]] = None
    ):
        self.on_result = on_result
        self.on_error = on_error
        self.on_ready = on_ready
        self.language = language
        self.is_speaking_checker = is_speaking_checker
        self.is_listening = False
        self._stop_requested = False
        self._listen_thread: Optional[threading.Thread] = None
        self._sd_mic: Optional[SoundDeviceMicrophone] = None

    def start_listening(self):
        """
        Starts listening continuously from the laptop's default microphone.
        """
        if self.is_listening:
            return

        self._stop_requested = False
        self._listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._listen_thread.start()

    def _listen_loop(self):
        try:
            import speech_recognition as sr
        except ImportError:
            self.is_listening = False
            self.on_error("মাইক্রোফোন লাইব্রেরি পাওয়া যায়নি। টেক্সট বক্সে টাইপ করে কমান্ড দিতে পারেন।")
            return

        recognizer = sr.Recognizer()

        # Strategy 1: Try PyAudio sr.Microphone
        use_sd = False
        sr_mic = None
        try:
            sr_mic = sr.Microphone()
            with sr_mic as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
        except Exception:
            use_sd = True

        # Strategy 2: Use sounddevice if PyAudio is not available
        if use_sd:
            try:
                self._sd_mic = SoundDeviceMicrophone()
                self._sd_mic.start()
            except Exception as e:
                self.is_listening = False
                self.on_error(f"মাইক্রোফোন ডিভাইস পাওয়া যায়নি। টেক্সট বক্সে টাইপ করে কমান্ড দিতে পারেন। ({e})")
                return

        self.is_listening = True

        while not self._stop_requested:
            # If assistant is speaking, wait until speaking ends before advertising ready state
            if self.is_speaking_checker and self.is_speaking_checker():
                time.sleep(0.1)
                continue

            if self.on_ready:
                try:
                    self.on_ready()
                except Exception:
                    pass

            audio = None
            try:
                if use_sd and self._sd_mic:
                    audio = self._sd_mic.listen_phrase(
                        stop_checker=lambda: self._stop_requested,
                        is_speaking_checker=self.is_speaking_checker,
                        timeout=5.0,
                        phrase_time_limit=10.0
                    )
                elif sr_mic:
                    if self.is_speaking_checker and self.is_speaking_checker():
                        time.sleep(0.2)
                        continue
                    with sr_mic as source:
                        audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)

                # Discard audio if assistant was speaking when audio arrived
                if self.is_speaking_checker and self.is_speaking_checker():
                    if self._sd_mic:
                        self._sd_mic.drain()
                    continue

                if audio is not None and not self._stop_requested:
                    text = None
                    # 1. Primary: Online Google Speech Recognition (Bengali)
                    try:
                        text = recognizer.recognize_google(audio, language=self.language)
                    except sr.UnknownValueError:
                        # 2. Secondary: Online Google Speech Recognition (English)
                        try:
                            text = recognizer.recognize_google(audio, language="en-US")
                        except Exception:
                            pass
                    except Exception:
                        # Network dropped or timed out; will fall through to offline Vosk
                        pass

                    # 3. Tertiary: Offline Vosk Speech Recognition (Zero Network Required)
                    if not text:
                        try:
                            raw_vosk = recognizer.recognize_vosk(audio)
                            if raw_vosk:
                                import json
                                try:
                                    parsed = json.loads(raw_vosk)
                                    text = parsed.get("text", "").strip()
                                except Exception:
                                    text = str(raw_vosk).strip()
                        except Exception:
                            pass

                    if text:
                        self.on_result(text)

            except sr.WaitTimeoutError:
                continue
            except Exception as e:
                if not self._stop_requested:
                    self.on_error(str(e))
                time.sleep(0.3)

        if self._sd_mic:
            self._sd_mic.stop()
            self._sd_mic = None

        self.is_listening = False

    def stop_listening(self):
        self._stop_requested = True
        if self._sd_mic:
            self._sd_mic.stop()
        self.is_listening = False

    def destroy(self):
        self.stop_listening()
