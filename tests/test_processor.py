import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.command_processor import CommandProcessor
from src.helpers.date_helper import DateHelper

def run_tests():
    print("Testing DateHelper:")
    print("Date:", DateHelper.get_current_date_bengali())
    print("Time:", DateHelper.get_current_time_bengali())

    print("\nTesting CommandProcessor Queries:")
    cases = [
        ("সময় কত", "time"),
        ("তারিখ কত", "date"),
        ("চার্জ কত", "battery"),
        ("hello", "greeting"),
        ("টাইপ করো", "typing"),
        ("উপরে যাও", "scroll up"),
        ("নিচে নামো", "scroll down"),
        ("০১৭১১০০০০০১", "digits call"),
        ("ইউটিউবে গান সার্চ করো", "youtube search"),
        ("গুগলে পাইথন সার্চ করো", "google search"),
        ("ইউটিউব", "search prompt"),
        ("নোটপ্যাড ওপেন করো", "app open"),
        ("ব্রাউজারে গিয়ে ঢাকা বিশ্ববিদ্যালয়ের ওয়েবসাইট দেখো", "browser agent task"),
        ("ডকুমেন্ট পড়ো test_sample.md", "document reader task"),
        ("ইউটিউবে রবীন্দ্রসংগীত প্লে করো", "playwright media playback"),
        ("ওয়েব স্ক্রিনশট নাও https://github.com", "playwright screenshot"),
        ("হোয়াটসঅ্যাপ ওয়েব ওপেন করো", "playwright persistent session"),
        ("ডকলিং দিয়ে ওয়ার্ড ফাইল পড়ো document.docx", "docling word read"),
        ("ডকুমেন্ট চাংক করো test_sample.md", "docling semantic chunk"),
        ("এক্সেল পড়ো report.xlsx", "docling excel read"),
        ("আমার পিডিএফ ফাইল খুঁজে দাও", "local pc file search"),
        ("অ্যাসাইনমেন্ট সলভ করে দাও", "assignment solver"),
        ("মেসেজ পাঠাও ০১৭১১০০০০০১ কেমন আছেন", "sms / whatsapp send")
    ]

    for query, label in cases:
        is_cmd = CommandProcessor.is_a_command(query)
        is_greet = CommandProcessor.is_greeting(query)
        resp = CommandProcessor.process_command(query)
        print(f"[{label}] Query: '{query}' -> is_cmd={is_cmd}, is_greet={is_greet}")
        print(f"       Response: {resp}")

    print("\nAll tests completed successfully!")

if __name__ == "__main__":
    run_tests()
