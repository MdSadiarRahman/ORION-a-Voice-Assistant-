"""
VoiceMate Laptop Agent - Document Fallback Reader.
Handles text/markdown documents and provides fallback reading
if PyMuPDF C-binaries are not installed.
"""
from pathlib import Path
from typing import Dict, Any

class DocumentFallbackReader:
    @staticmethod
    def read_text_document(file_path: str) -> Dict[str, Any]:
        path = Path(file_path).resolve()
        if not path.exists():
            return {
                "file_name": path.name,
                "page_count": 0,
                "plain_text": f"ফাইলটি পাওয়া যায়নি: {file_path}",
                "markdown": ""
            }

        text = ""
        # Try reading plain text / markdown
        try:
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
        except UnicodeDecodeError:
            try:
                with open(path, "r", encoding="latin-1") as f:
                    text = f.read()
            except Exception as e:
                text = f"ফাইল পড়তে সমস্যা হয়েছে: {e}"

        lines = [line.strip() for line in text.split("\n") if line.strip()]
        preview = " ".join(lines[:6]) if lines else "ডকুমেন্টে কোনো লেখা নেই।"
        if len(preview) > 1000:
            preview = preview[:1000] + "..."

        return {
            "file_name": path.name,
            "page_count": 1,
            "plain_text": text,
            "markdown": text,
            "summary": f"ডকুমেন্ট '{path.name}' পড়া হয়েছে। বিষয়বস্তু: {preview}"
        }
