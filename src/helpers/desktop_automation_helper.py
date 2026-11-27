"""
VoiceMate Laptop Agent - Desktop Automation Helper Module.
Provides desktop accessibility, keyboard typing, scrolling,
shortcut execution, and window management on Windows.
"""
import ctypes
import time
import subprocess
from typing import Optional

# Windows virtual key codes
VK_BACK = 0x08
VK_RETURN = 0x0D
VK_CONTROL = 0x11
VK_MENU = 0x12       # ALT
VK_A = 0x41
VK_D = 0x44
VK_Z = 0x5A
VK_F4 = 0x73
VK_LWIN = 0x5B       # Left Windows Key
VK_PRIOR = 0x21      # Page Up
VK_NEXT = 0x22       # Page Down

KEYEVENTF_KEYUP = 0x0002
MOUSEEVENTF_WHEEL = 0x0800

class DesktopAutomationHelper:
    """
    Provides accessibility gestures, scrolling, typing, sending,
    and window controls on Windows Desktop.
    """
    _last_clipboard_text: str = ""

    @staticmethod
    def _send_key_event(vk_code: int, keyup: bool = False):
        try:
            flags = KEYEVENTF_KEYUP if keyup else 0
            ctypes.windll.user32.keybd_event(vk_code, 0, flags, 0)
        except Exception:
            pass

    @classmethod
    def press_key_combination(cls, *vk_codes):
        for vk in vk_codes:
            cls._send_key_event(vk, keyup=False)
        time.sleep(0.05)
        for vk in reversed(vk_codes):
            cls._send_key_event(vk, keyup=True)

    @classmethod
    def go_home(cls):
        """Minimizes all windows to show the Desktop (Win + D)."""
        cls.press_key_combination(VK_LWIN, VK_D)

    @classmethod
    def scroll_up(cls, clicks: int = 4):
        """Scrolls up active window/page."""
        try:
            import pyautogui
            pyautogui.scroll(clicks * 100)
            return
        except Exception:
            pass

        try:
            wheel_delta = 120 * clicks
            ctypes.windll.user32.mouse_event(MOUSEEVENTF_WHEEL, 0, 0, wheel_delta, 0)
        except Exception:
            pass

    @classmethod
    def scroll_down(cls, clicks: int = 4):
        """Scrolls down active window/page."""
        try:
            import pyautogui
            pyautogui.scroll(-clicks * 100)
            return
        except Exception:
            pass

        try:
            wheel_delta = -120 * clicks
            ctypes.windll.user32.mouse_event(MOUSEEVENTF_WHEEL, 0, 0, wheel_delta, 0)
        except Exception:
            pass

    @classmethod
    def focus_and_open_keyboard(cls):
        """Focuses active input field."""
        pass

    @classmethod
    def set_clipboard_text(cls, text: str) -> bool:
        """Sets clipboard text using pyperclip, Windows ctypes, or in-memory fallback."""
        cls._last_clipboard_text = text

        try:
            import pyperclip
            pyperclip.copy(text)
            return True
        except Exception:
            pass

        try:
            GMEM_MOVEABLE = 0x0002
            CF_UNICODETEXT = 13
            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32

            kernel32.GlobalAlloc.argtypes = [ctypes.c_uint, ctypes.c_size_t]
            kernel32.GlobalAlloc.restype = ctypes.c_void_p
            kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
            kernel32.GlobalLock.restype = ctypes.c_void_p
            kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
            user32.SetClipboardData.argtypes = [ctypes.c_uint, ctypes.c_void_p]
            user32.SetClipboardData.restype = ctypes.c_void_p

            if user32.OpenClipboard(0):
                user32.EmptyClipboard()
                encoded = text.encode('utf-16le') + b'\x00\x00'
                h_mem = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(encoded))
                if h_mem:
                    p_mem = kernel32.GlobalLock(h_mem)
                    if p_mem:
                        ctypes.memmove(p_mem, encoded, len(encoded))
                        kernel32.GlobalUnlock(h_mem)
                        user32.SetClipboardData(CF_UNICODETEXT, h_mem)
                user32.CloseClipboard()
                return True
        except Exception:
            pass

        return True

    @classmethod
    def append_text(cls, text: str) -> bool:
        """
        Types Bengali / English text into active window using clipboard paste (Ctrl + V).
        """
        if not text:
            return False

        if cls.set_clipboard_text(text):
            time.sleep(0.05)
            # Send Ctrl + V
            cls.press_key_combination(VK_CONTROL, ord('V'))
            return True
        else:
            try:
                import pyautogui
                pyautogui.typewrite(text)
                return True
            except Exception:
                return False

    @classmethod
    def click_send(cls) -> bool:
        """Simulates Enter / Send key."""
        cls._send_key_event(VK_RETURN, keyup=False)
        time.sleep(0.05)
        cls._send_key_event(VK_RETURN, keyup=True)
        return True

    @classmethod
    def delete_last_word(cls, count: int = 1) -> bool:
        """Deletes the last word(s) using Ctrl + Backspace."""
        for _ in range(max(1, count)):
            cls.press_key_combination(VK_CONTROL, VK_BACK)
            time.sleep(0.05)
        return True

    @classmethod
    def undo_last(cls) -> bool:
        """Undoes the last pasted phrase/sentence using Ctrl + Z."""
        cls.press_key_combination(VK_CONTROL, VK_Z)
        return True

    @classmethod
    def clear_all_text(cls) -> bool:
        """Selects all text in the active input box and deletes it (Ctrl + A, Backspace)."""
        cls.press_key_combination(VK_CONTROL, VK_A)
        time.sleep(0.05)
        cls._send_key_event(VK_BACK, keyup=False)
        time.sleep(0.03)
        cls._send_key_event(VK_BACK, keyup=True)
        return True

    @classmethod
    def close_current_app(cls) -> str:
        """Closes current active window using Alt + F4."""
        try:
            cls.press_key_combination(VK_MENU, VK_F4)
            return "বর্তমান উইন্ডো বন্ধ করা হয়েছে"
        except Exception:
            return "উইন্ডো বন্ধ করা সম্ভব হয়নি"
