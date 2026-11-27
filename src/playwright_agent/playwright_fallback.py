"""Browser-opening fallbacks for Playwright tasks when browser binaries are unavailable."""

import urllib.parse
import webbrowser
from typing import Any


class PlaywrightFallbackAgent:
    @staticmethod
    def _open(url: str, action: str) -> dict[str, Any]:
        try:
            opened = webbrowser.open(url)
        except Exception as exc:
            return {
                "success": False,
                "action": action,
                "url": url,
                "message": f"ব্রাউজার খুলতে সমস্যা হয়েছে: {exc}",
            }
        return {
            "success": bool(opened),
            "action": action,
            "url": url,
            "message": (
                "ডিফল্ট ব্রাউজারে খোলা হয়েছে।"
                if opened
                else "ডিফল্ট ব্রাউজার URL খোলার অনুরোধ গ্রহণ করেনি।"
            ),
        }

    @classmethod
    def play_youtube_video(cls, query: str) -> dict[str, Any]:
        url = "https://www.youtube.com/results?" + urllib.parse.urlencode(
            {"search_query": query.strip()}
        )
        return cls._open(url, "play_youtube")

    @classmethod
    def search_web(cls, query: str) -> dict[str, Any]:
        url = "https://www.google.com/search?" + urllib.parse.urlencode(
            {"q": query.strip()}
        )
        return cls._open(url, "search_web")

    @classmethod
    def open_website(cls, url: str) -> dict[str, Any]:
        target = url.strip()
        if not target.startswith(("http://", "https://")):
            target = "https://" + target
        return cls._open(target, "open_website")
