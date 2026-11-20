"""
VoiceMate Laptop Agent - Vision and ML Helper Module.
Performs Optical Character Recognition (OCR) and object classification.
"""
import os
from typing import Dict, Any

class VisionHelper:
    @staticmethod
    def recognize_text(image_path: str) -> str:
        """Extracts text from image (OCR)."""
        try:
            import importlib
            pytesseract = importlib.import_module("pytesseract")
            from PIL import Image
            img = Image.open(image_path)
            text = pytesseract.image_to_string(img).strip()
            if text:
                return text
        except Exception:
            pass

        try:
            import importlib
            easyocr = importlib.import_module("easyocr")
            reader = easyocr.Reader(['bn', 'en'], gpu=False)
            results = reader.readtext(image_path, detail=0)
            text = " ".join(results).strip()
            if text:
                return text
        except Exception:
            pass

        return "ছবিতে কোনো লেখা খুঁজে পাওয়া যায়নি।"

    @staticmethod
    def detect_objects(image_path: str) -> str:
        """Detects objects/faces in image."""
        try:
            import importlib
            cv2 = importlib.import_module("cv2")
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            img = cv2.imread(image_path)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)
            if len(faces) > 0:
                return f"ছবিতে দেখা যাচ্ছে: {len(faces)} জন ব্যক্তি বা মুখমণ্ডল"
        except Exception:
            pass

        return "ছবিতে কোনো নির্দিষ্ট বস্তু খুঁজে পাওয়া যায়নি।"

    @classmethod
    def process_image(cls, image_path: str) -> str:
        """
        Processes captured image:
        1. Tries OCR text extraction
        2. Falls back to object/scene classification
        """
        text = cls.recognize_text(image_path)
        if "খুঁজে পাওয়া যায়নি" not in text and text.strip():
            return f"ছবিতে লেখা আছে: {text}"
        
        objects = cls.detect_objects(image_path)
        return objects
