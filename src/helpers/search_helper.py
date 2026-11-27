"""
VoiceMate Laptop Agent - Search Helper Module.
Opens Google, YouTube, and web destinations in default laptop browser.
Includes real-time YouTube video resolver to directly play songs and videos.
"""
import urllib.parse
import urllib.request
import webbrowser
import re
from typing import Tuple


class SearchHelper:
    @staticmethod
    def search_in_google(query: str) -> str:
        """Searches Google for the given query."""
        try:
            encoded_query = urllib.parse.quote_plus(query.strip())
            url = f"https://www.google.com/search?q={encoded_query}"
            webbrowser.open(url)
            return f"গুগলে {query} সার্চ করা হচ্ছে"
        except Exception:
            return "গুগল সার্চ করতে ব্যর্থ হয়েছে"

    @staticmethod
    def search_in_youtube(query: str) -> str:
        """Searches YouTube for the given query."""
        try:
            encoded_query = urllib.parse.quote_plus(query.strip())
            url = f"https://www.youtube.com/results?search_query={encoded_query}"
            webbrowser.open(url)
            return f"ইউটিউবে {query} সার্চ করা হচ্ছে"
        except Exception:
            return "ইউটিউব সার্চ করতে ব্যর্থ হয়েছে"

    @classmethod
    def resolve_youtube_watch_url(cls, query: str) -> Tuple[str, str]:
        """
        Resolves the first direct playable watch URL (watch?v=...) and video title for a query.
        Falls back to search results URL if resolution times out.
        """
        clean_q = query.strip()
        # Clean leading action keywords
        for pfx in ["ওপেন ", "open ", "প্লে ", "play ", "চালাও ", "বাজাও ", "শোনাও "]:
            if clean_q.lower().startswith(pfx):
                clean_q = clean_q[len(pfx):].strip()

        encoded = urllib.parse.quote_plus(clean_q)
        search_url = f"https://www.youtube.com/results?search_query={encoded}"

        try:
            req = urllib.request.Request(
                search_url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            )
            with urllib.request.urlopen(req, timeout=4) as response:
                html = response.read().decode('utf-8', errors='ignore')

            # Extract video IDs
            vids = re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', html)
            if not vids:
                vids = re.findall(r'/watch\?v=([a-zA-Z0-9_-]{11})', html)

            if vids:
                first_id = vids[0]
                # Extract title
                title_match = re.search(r'"title":\{"runs":\[\{"text":"([^"]+)"\}\]', html)
                title = title_match.group(1) if title_match else clean_q
                watch_url = f"https://www.youtube.com/watch?v={first_id}&autoplay=1"
                return watch_url, title
        except Exception:
            pass

        return search_url, clean_q

    @classmethod
    def play_youtube_song(cls, query: str) -> Tuple[bool, str, str, str]:
        """
        Finds the exact video for the query and opens it in the browser with autoplay=1.
        Returns: (success, video_title, message, watch_url)
        """
        try:
            watch_url, title = cls.resolve_youtube_watch_url(query)
            webbrowser.open(watch_url)
            msg = f"ইউটিউবে '{title}' প্লে করা হচ্ছে।"
            return True, title, msg, watch_url
        except Exception as e:
            fallback_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote_plus(query)}"
            webbrowser.open(fallback_url)
            return False, query, f"ইউটিউব ওপেন করা হয়েছে ({e})", fallback_url

    @staticmethod
    def open_website(url: str) -> str:
        """Opens a website in the default browser."""
        try:
            target_url = url.strip()
            if not (target_url.startswith("http://") or target_url.startswith("https://")):
                target_url = f"https://{target_url}"
            webbrowser.open(target_url)
            return "ওয়েবসাইট ওপেন করা হচ্ছে"
        except Exception:
            return "ওয়েবসাইট ওপেন করতে ব্যর্থ হয়েছে"
