"""English and Arabic UI strings."""

from __future__ import annotations

from typing import Literal

Lang = Literal["en", "ar"]

STRINGS: dict[str, dict[Lang, str]] = {
    "choose_language": {
        "en": "Choose language:",
        "ar": "اختر اللغة:",
    },
    "lang_en": {"en": "English", "ar": "English"},
    "lang_ar": {"en": "العربية", "ar": "العربية"},
    "private_only": {
        "en": "This demo bot works in private chat only. Open t.me/flightsdemobot and message me directly.",
        "ar": "هذا البوت للمحادثات الخاصة فقط. افتح t.me/flightsdemobot وتحدث معي مباشرة.",
    },
    "enter_access_key": {
        "en": "Enter the access key shared by Parvus Media:",
        "ar": "أدخل مفتاح الوصول الذي شاركه Parvus Media:",
    },
    "access_denied": {
        "en": "Access key not accepted. Check the key and try again.",
        "ar": "مفتاح الوصول غير صحيح. تحقق من المفتاح وحاول مرة أخرى.",
    },
    "access_ok": {
        "en": "Access granted. Use the menu below to search Saudia fares.",
        "ar": "تم قبول المفتاح. استخدم القائمة أدناه للبحث عن أسعار السعودية.",
    },
    "locked": {
        "en": "Session locked. Send /start to enter the access key again.",
        "ar": "تم قفل الجلسة. أرسل /start لإدخال المفتاح مرة أخرى.",
    },
    "help": {
        "en": (
            "Saudia fares demo by Parvus Media (not official Saudia).\n"
            "/search — new search\n/language — change language\n/lock — lock session\n/cancel — cancel current step"
        ),
        "ar": (
            "عرض أسعار السعودية من Parvus Media (ليس بوتاً رسمياً).\n"
            "/search — بحث جديد\n/language — تغيير اللغة\n/lock — قفل الجلسة\n/cancel — إلغاء الخطوة الحالية"
        ),
    },
    "menu_new": {"en": "New search", "ar": "بحث جديد"},
    "menu_origin": {"en": "Origin", "ar": "من"},
    "menu_destination": {"en": "Destination", "ar": "إلى"},
    "menu_dates": {"en": "Dates", "ar": "التواريخ"},
    "menu_price": {"en": "Max price", "ar": "السعر الأقصى"},
    "menu_language": {"en": "Language", "ar": "اللغة"},
    "menu_cancel": {"en": "Cancel", "ar": "إلغاء"},
    "pick_origin": {
        "en": "Select origin (Saudi hubs or type a 3-letter IATA code):",
        "ar": "اختر نقطة الانطلاق (محاور سعودية أو اكتب رمز IATA من 3 أحرف):",
    },
    "pick_destination": {
        "en": "Select destination (Saudi hubs or type a 3-letter IATA code):",
        "ar": "اختر الوجهة (محاور سعودية أو اكتب رمز IATA من 3 أحرف):",
    },
    "pick_departure": {
        "en": "Pick outbound date (Gregorian) or send DD/MM/YYYY:",
        "ar": "اختر تاريخ الذهاب (ميلادي) أو أرسل DD/MM/YYYY:",
    },
    "pick_return": {
        "en": "Pick return date or One way:",
        "ar": "اختر تاريخ العودة أو ذهاب فقط:",
    },
    "pick_max_price": {
        "en": "Max price in SAR (integer):",
        "ar": "السعر الأقصى بالريال السعودي (رقم صحيح):",
    },
    "one_way": {"en": "One way", "ar": "ذهاب فقط"},
    "searching": {
        "en": "Looking up Saudia fares…",
        "ar": "جاري البحث عن أسعار السعودية…",
    },
    "invalid_iata": {
        "en": "Use a valid 3-letter IATA code.",
        "ar": "استخدم رمز IATA صالح من 3 أحرف.",
    },
    "invalid_date": {
        "en": "Invalid or past date. Use the calendar or DD/MM/YYYY.",
        "ar": "تاريخ غير صالح أو في الماضي. استخدم التقويم أو DD/MM/YYYY.",
    },
    "invalid_price": {
        "en": "Enter a positive integer amount in SAR.",
        "ar": "أدخل مبلغاً صحيحاً موجباً بالريال السعودي.",
    },
    "return_before_depart": {
        "en": "Return must be after outbound date.",
        "ar": "تاريخ العودة يجب أن يكون بعد تاريخ الذهاب.",
    },
    "same_origin_dest": {
        "en": "Origin and destination must differ.",
        "ar": "نقطة الانطلاق والوجهة يجب أن تكونا مختلفتين.",
    },
    "section_exact": {"en": "Your dates", "ar": "تواريخك"},
    "section_flex": {"en": "Cheaper ±3 days", "ar": "أرخص ±٣ أيام"},
    "no_under_budget": {
        "en": "No fares under your max price.",
        "ar": "لا توجد أسعار تحت السعر الأقصى.",
    },
    "over_budget": {"en": "Over budget", "ar": "فوق الميزانية"},
    "book": {"en": "Book", "ar": "احجز"},
    "outbound": {"en": "Outbound", "ar": "ذهاب"},
    "return": {"en": "Return", "ar": "إياب"},
    "disclaimer": {
        "en": "Demo by Parvus Media. Fares subject to availability at saudia.com. Not an official Saudia bot.",
        "ar": "عرض من Parvus Media. الأسعار خاضعة للتوفر على saudia.com. ليس بوتاً رسمياً للسعودية.",
    },
    "cancelled": {"en": "Cancelled.", "ar": "تم الإلغاء."},
    "quote_failed": {
        "en": "Could not fetch live fares right now. Try again in a moment.",
        "ar": "تعذر جلب الأسعار الآن. حاول مرة أخرى بعد قليل.",
    },
}


def t(key: str, lang: Lang) -> str:
    block = STRINGS.get(key)
    if not block:
        return key
    return block.get(lang, block["en"])
