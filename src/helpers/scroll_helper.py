"""
VoiceMate Laptop Agent - Scroll Helper Module.
Routes scrolling actions to the desktop automation subsystem.
"""
from src.helpers.desktop_automation_helper import DesktopAutomationHelper

class ScrollHelper:
    @staticmethod
    def scroll(direction: str) -> str:
        d = direction.lower().strip()
        if d in ["up", "উপরে", "উঠো"]:
            DesktopAutomationHelper.scroll_up()
            return "উপরে যাওয়া হচ্ছে"
        elif d in ["down", "নিচে", "নামো"]:
            DesktopAutomationHelper.scroll_down()
            return "নিচে যাওয়া হচ্ছে"
        else:
            return "স্ক্রল ফিচারটি কার্যকর করা হয়েছে"
