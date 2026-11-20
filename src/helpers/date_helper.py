"""
VoiceMate Laptop Agent - Date and Time Helper Module.
Provides Bengali localized date and time representation.
"""
import datetime

class DateHelper:
    BENGALI_DIGITS = {
        '0': '০', '1': '১', '2': '২', '3': '৩', '4': '৪',
        '5': '৫', '6': '৬', '7': '৭', '8': '৮', '9': '৯'
    }

    BENGALI_MONTHS = [
        "জানুয়ারি", "ফেব্রুয়ারি", "মার্চ", "এপ্রিল", "মে", "জুন",
        "জুলাই", "আগস্ট", "সেপ্টেম্বর", "অক্টোবর", "নভেম্বর", "ডিসেম্বর"
    ]

    @classmethod
    def to_bengali_digits(cls, number_str: str) -> str:
        """Converts English digits to Bengali digits."""
        return "".join(cls.BENGALI_DIGITS.get(ch, ch) for ch in str(number_str))

    @classmethod
    def get_current_date_bengali(cls) -> str:
        """
        Returns current date in Bengali format.
        e.g., 'আজকের তারিখ হলো ১৪ নভেম্বর ২০২৬'
        """
        now = datetime.datetime.now()
        day_bn = cls.to_bengali_digits(now.strftime("%d"))
        month_bn = cls.BENGALI_MONTHS[now.month - 1]
        year_bn = cls.to_bengali_digits(now.strftime("%Y"))
        
        return f"আজকের তারিখ হলো {day_bn} {month_bn} {year_bn}"

    @classmethod
    def get_current_time_bengali(cls) -> str:
        """Returns current time in Bengali format."""
        now = datetime.datetime.now()
        hour = now.hour
        minute = cls.to_bengali_digits(f"{now.minute:02d}")
        
        period = "সকাল" if 5 <= hour < 12 else "দুপুর" if 12 <= hour < 16 else "বিকাল" if 16 <= hour < 19 else "রাত"
        hour_12 = hour % 12 or 12
        hour_bn = cls.to_bengali_digits(str(hour_12))
        
        return f"এখন সময় হলো {period} {hour_bn}টা বেজে {minute} মিনিট"
