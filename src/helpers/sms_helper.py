"""
VoiceMate Laptop Agent - SMS and Messaging Helper Module.
Handles WhatsApp messaging and web-based messaging on the laptop.
"""
import re
import urllib.parse
import webbrowser

class SmsHelper:
    @staticmethod
    def send_sms(phone_number: str, message: str) -> str:
        """
        Sends message to given phone number via WhatsApp / Web SMS.
        """
        clean_number = re.sub(r"[^0-9]", "", phone_number)
        if clean_number.startswith("0"):
            clean_number = "88" + clean_number
            
        encoded_msg = urllib.parse.quote(message)
        wa_url = f"https://api.whatsapp.com/send?phone={clean_number}&text={encoded_msg}"
        try:
            webbrowser.open(wa_url)
            return f"{phone_number} নাম্বারে মেসেজ পাঠানোর জন্য উইন্ডো খোলা হয়েছে।"
        except Exception:
            return "মেসেজ পাঠানো সম্ভব হয়নি।"

    @staticmethod
    def can_send_sms() -> bool:
        return True
