"""
VoiceMate Laptop Agent - Contact Helper Module.
Manages contact lookup, phone dialing, and address book for the laptop agent.
"""
import json
import os
import re
import webbrowser
from typing import Optional, Tuple, List, Dict
from config import CONTACTS_FILE

class ContactHelper:
    @classmethod
    def _load_contacts(cls) -> List[Dict[str, str]]:
        if not os.path.exists(CONTACTS_FILE):
            return []
        try:
            with open(CONTACTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    @classmethod
    def _save_contacts(cls, contacts: List[Dict[str, str]]) -> bool:
        try:
            with open(CONTACTS_FILE, "w", encoding="utf-8") as f:
                json.dump(contacts, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False

    @classmethod
    def get_all_contacts(cls) -> List[Dict[str, str]]:
        return cls._load_contacts()

    @classmethod
    def add_contact(cls, name: str, phone: str, relation: str = "") -> bool:
        contacts = cls._load_contacts()
        contacts.append({"name": name, "phone": phone, "relation": relation})
        return cls._save_contacts(contacts)

    @staticmethod
    def _contains_word(text: str, word: str) -> bool:
        pattern = rf"(^|[^\w\u0980-\u09FF]){re.escape(word)}($|[^\w\u0980-\u09FF])"
        return bool(re.search(pattern, text, re.IGNORECASE))

    @classmethod
    def get_phone_number_by_name(cls, name_to_search: str) -> Optional[str]:
        """
        Finds phone number by contact name.
        Matches exact, substring, or discrete word match.
        """
        query_name = name_to_search.lower().strip()
        if not query_name:
            return None

        contacts = cls._load_contacts()
        for contact in contacts:
            c_name = contact.get("name", "").lower().strip()
            phone = contact.get("phone", "").strip()

            # ১. সরাসরি মিল থাকলে
            if c_name == query_name:
                return phone

            # ২. কন্টাক্ট নামের ভেতরে সার্চ করা নাম থাকলে
            if query_name in c_name:
                return phone

            # ৩. সার্চ করা নামের ভেতরে কন্টাক্ট নাম স্বতন্ত্র শব্দ হিসেবে থাকলে
            if cls._contains_word(query_name, c_name):
                return phone

        return None

    @classmethod
    def get_phone_number_by_last_digits(cls, last_digits: str) -> Optional[Tuple[str, str]]:
        """
        Finds contact by last digits of phone number.
        Returns (name, number) or None.
        """
        digits = re.sub(r"[^0-9]", "", last_digits)
        if not digits:
            return None

        contacts = cls._load_contacts()
        for contact in contacts:
            name = contact.get("name", "")
            raw_phone = contact.get("phone", "")
            clean_number = re.sub(r"[^0-9]", "", raw_phone)
            if clean_number.endswith(digits):
                return (name, raw_phone)

        return None

    @classmethod
    def make_call(cls, number: str, name: str) -> str:
        """
        Initiates call using Windows tel: URI handler (Phone Link, Skype, etc.)
        """
        clean_number = re.sub(r"[^0-9+]", "", number)
        try:
            webbrowser.open(f"tel:{clean_number}")
            if name == number:
                return f"{number} নাম্বারে কল করা হচ্ছে"
            else:
                return f"{name} কে কল করা হচ্ছে"
        except Exception:
            return f"{name} এর নাম্বারে কল করা সম্ভব হয়নি"
