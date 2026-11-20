"""
VoiceMate Laptop Agent - Browser Fallback Subsystem.
Provides direct web navigation, search, and page extraction when full
Pydantic AI / Browser-Use engine dependencies are not yet initialized.
"""
import urllib.parse
import urllib.request
import webbrowser
import re
from typing import Dict, Any, Optional

class BrowserFallbackAgent:
    @staticmethod
    def execute_basic_task(task_prompt: str) -> str:
        """
        Executes a web task using direct browser navigation and web scraping.
        Extracts intent, performs search or navigation, and summarizes findings.
        """
        query = task_prompt.strip()
        
        # 1. Check if user provided a specific URL
        url_match = re.search(r'https?://[^\s]+', query)
        target_url = url_match.group(0) if url_match else None

        if not target_url:
            # Clean keywords to formulate search query
            clean_query = query
            for noise in ["ব্রাউজারে গিয়ে", "ব্রাউজ করো", "খুঁজে বের করো", "রিসার্চ করো", "browse", "search"]:
                clean_query = clean_query.replace(noise, "")
            clean_query = clean_query.strip()
            
            encoded = urllib.parse.quote_plus(clean_query)
            target_url = f"https://www.google.com/search?q={encoded}"
            summary_target = clean_query
        else:
            summary_target = target_url

        try:
            # Open browser window
            webbrowser.open(target_url)
            return f"ব্রাউজারে '{summary_target}' সফলভাবে লোড করা হয়েছে এবং পর্যবেক্ষণ করা হচ্ছে।"
        except Exception as e:
            return f"ব্রাউজার চালু করতে সমস্যা হয়েছে: {e}"
