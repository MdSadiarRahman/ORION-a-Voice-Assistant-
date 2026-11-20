"""
VoiceMate Laptop Agent - Camera Helper Module.
Handles webcam image capture and screenshot fallback for the laptop.
"""
import os
import time
import datetime
from pathlib import Path
from typing import Optional, Tuple
from config import CAPTURES_DIR

class CameraHelper:
    @classmethod
    def capture_photo(cls) -> Tuple[bool, Optional[str], str]:
        """
        Captures a photo using laptop webcam (or screenshot fallback)
        and saves it to the captures directory.
        Returns: (success, saved_image_path, status_message)
        """
        CAPTURES_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f")[:-3]
        file_path = str(CAPTURES_DIR / f"{timestamp}.jpg")

        # 1. Try OpenCV webcam if installed
        try:
            import importlib
            cv2 = importlib.import_module("cv2")
            cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            if not cap.isOpened():
                cap = cv2.VideoCapture(0)

            if cap.isOpened():
                # Warm up camera
                for _ in range(5):
                    cap.read()
                ret, frame = cap.read()
                cap.release()
                if ret and frame is not None:
                    cv2.imwrite(file_path, frame)
                    return True, file_path, "ক্যামেরা থেকে সফলভাবে ছবি তোলা হয়েছে।"
        except Exception:
            pass

        # 2. Fallback: Desktop Screenshot if webcam not opened or cv2 not installed
        try:
            from PIL import ImageGrab
            screenshot = ImageGrab.grab()
            screenshot.save(file_path, "JPEG")
            return True, file_path, "স্ক্রিন থেকে সফলভাবে ছবি তোলা হয়েছে।"
        except Exception:
            pass

        return False, None, "দুঃখিত, ছবি তোলা সম্ভব হয়নি।"
