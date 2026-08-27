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
        "en": (
            "Welcome! You're in — let's find Saudia fares together.\n"
            "Use /menu for your trip summary or /search for a new trip."
        ),
        "ar": (
            "أهلاً! تم قبول المفتاح — لنبحث عن أسعار السعودية معاً.\n"
            "استخدم /menu لملخص رحلتك أو /search لبحث جديد."
        ),
    },
    "locked": {
        "en": "Session locked. Send /start to enter the access key again.",
        "ar": "تم قفل الجلسة. أرسل /start لإدخال المفتاح مرة أخرى.",
    },
    "help": {
        "en": (
            "Saudia fares demo by Parvus Media (not official Saudia).\n"
            "/search — new search\n/menu — trip summary\n/language — change language\n/lock — lock session\n/cancel — cancel current step"
        ),
        "ar": (
            "عرض أسعار السعودية من Parvus Media (ليس بوتاً رسمياً).\n"
            "/search — بحث جديد\n/menu — ملخص الرحلة\n/language — تغيير اللغة\n/lock — قفل الجلسة\n/cancel — إلغاء الخطوة الحالية"
        ),
    },
    "menu_new": {"en": "New search", "ar": "بحث جديد"},
    "menu_open": {"en": "Menu", "ar": "Menu"},
    "input_placeholder": {
        "en": "Message or tap Menu",
        "ar": "رسالة أو اضغط Menu",
    },
    "menu_keyboard_hint": {
        "en": "Keyboard updated — tap Menu for your trip summary.",
        "ar": "تم تحديث القائمة — اضغط Menu لملخص رحلتك.",
    },
    "menu_origin": {"en": "Origin", "ar": "من"},
    "menu_destination": {"en": "Destination", "ar": "إلى"},
    "menu_dates": {"en": "Dates", "ar": "التواريخ"},
    "menu_price": {"en": "Max price", "ar": "السعر الأقصى"},
    "menu_passengers": {"en": "Passengers", "ar": "المسافرون"},
    "menu_cabin": {"en": "Cabin", "ar": "الدرجة"},
    "menu_language": {"en": "Language", "ar": "اللغة"},
    "menu_cancel": {"en": "Cancel", "ar": "إلغاء"},
    "pick_origin_start": {
        "en": "Fresh start. Tap a Saudi hub below or type a 3-letter airport code.",
        "ar": "بحث جديد. اختر محوراً سعودياً أدناه أو اكتب رمز المطار من 3 أحرف.",
    },
    "pick_origin": {
        "en": "Where are you flying from? Tap a Saudi hub below or type a 3-letter airport code.",
        "ar": "من أين تريد السفر؟ اختر محوراً سعودياً أدناه أو اكتب رمز المطار من 3 أحرف.",
    },
    "pick_destination": {
        "en": "And where to? Choose your destination below or type the code.",
        "ar": "وإلى أين؟ اختر الوجهة أدناه أو اكتب الرمز.",
    },
    "pick_departure": {
        "en": "When do you want to leave? Pick a month or send DD/MM/YYYY.",
        "ar": "متى تريد المغادرة؟ اختر شهراً أو أرسل DD/MM/YYYY.",
    },
    "pick_return": {
        "en": "Return date, or tap One way if you don't need a return flight.",
        "ar": "تاريخ العودة، أو اضغط ذهاب فقط إن لم تحتج عودة.",
    },
    "pick_max_price": {
        "en": "What's your max budget in SAR? (whole number)",
        "ar": "ما هو السعر الأقصى بالريال؟ (رقم صحيح)",
    },
    "pick_passengers": {
        "en": "How many adult passengers?",
        "ar": "كم عدد المسافرين البالغين؟",
    },
    "pick_passengers_after_budget": {
        "en": "Budget up to SAR {price}. How many adult passengers?",
        "ar": "الميزانية حتى {price} ريال. كم عدد المسافرين البالغين؟",
    },
    "pick_cabin": {
        "en": "Which cabin class?",
        "ar": "ما درجة السفر؟",
    },
    "passengers_1": {"en": "1 adult", "ar": "1 بالغ"},
    "passengers_2": {"en": "2 adults", "ar": "2 بالغين"},
    "passengers_3": {"en": "3+ adults", "ar": "3+ بالغين"},
    "cabin_economy": {"en": "Economy", "ar": "اقتصادية"},
    "cabin_business": {"en": "Business", "ar": "رجال أعمال"},
    "cabin_label_economy": {"en": "Economy", "ar": "اقتصادية"},
    "cabin_label_business": {"en": "Business", "ar": "رجال أعمال"},
    "ack_origin": {
        "en": "Got it — departing from {city}. ✈️",
        "ar": "تم — الانطلاق من {city}. ✈️",
    },
    "ack_destination": {
        "en": "Perfect — ✈️ {origin} to ✈️ {destination}. Let's pick your dates.",
        "ar": "ممتاز — ✈️ {origin} إلى ✈️ {destination}. لنختر التواريخ.",
    },
    "ack_departure": {
        "en": "Outbound set: {date}.",
        "ar": "تاريخ الذهاب: {date}.",
    },
    "ack_oneway": {
        "en": "One-way trip — no return date needed.",
        "ar": "رحلة ذهاب فقط — بدون عودة.",
    },
    "ack_return": {
        "en": "Round trip: {dep} → {ret}.",
        "ar": "ذهاب وعودة: {dep} → {ret}.",
    },
    "ack_max_price": {
        "en": "Budget up to SAR {price}.",
        "ar": "الميزانية حتى {price} ريال.",
    },
    "ack_passengers": {
        "en": "{count} adult passenger(s).",
        "ar": "{count} مسافر/مسافرين بالغين.",
    },
    "ack_cabin": {
        "en": "Cabin: {cabin}.",
        "ar": "الدرجة: {cabin}.",
    },
    "menu_summary_title": {
        "en": "📋 Your trip so far",
        "ar": "📋 رحلتك حتى الآن",
    },
    "menu_summary_hint": {
        "en": "Use the buttons below to change anything, or /search to start over.",
        "ar": "استخدم الأزرار لتغيير أي حقل، أو /search للبدء من جديد.",
    },
    "status_origin": {"en": "• From: {city}", "ar": "• من: {city}"},
    "status_origin_missing": {"en": "• From: not set", "ar": "• من: غير محدد"},
    "status_destination": {"en": "• To: {city}", "ar": "• إلى: {city}"},
    "status_destination_missing": {"en": "• To: not set", "ar": "• إلى: غير محدد"},
    "status_dates_oneway": {"en": "• Dates: {date} (one way)", "ar": "• التواريخ: {date} (ذهاب فقط)"},
    "status_dates_round": {"en": "• Dates: {dep} → {ret}", "ar": "• التواريخ: {dep} → {ret}"},
    "status_dates_dep_only": {"en": "• Outbound: {dep}", "ar": "• الذهاب: {dep}"},
    "status_dates_missing": {"en": "• Dates: not set", "ar": "• التواريخ: غير محددة"},
    "status_price": {"en": "• Max price: SAR {price}", "ar": "• السعر الأقصى: {price} ريال"},
    "status_price_missing": {"en": "• Max price: not set", "ar": "• السعر الأقصى: غير محدد"},
    "status_passengers": {"en": "• Passengers: {count} adult(s)", "ar": "• المسافرون: {count} بالغ"},
    "status_passengers_missing": {"en": "• Passengers: not set", "ar": "• المسافرون: غير محدد"},
    "status_cabin": {"en": "• Cabin: {cabin}", "ar": "• الدرجة: {cabin}"},
    "status_cabin_missing": {"en": "• Cabin: not set", "ar": "• الدرجة: غير محددة"},
    "new_search_prompt": {
        "en": "Fresh start.",
        "ar": "بحث جديد.",
    },
    "one_way": {"en": "One way", "ar": "ذهاب فقط"},
    "searching": {
        "en": "Checking Saudia fares for you… ⏳",
        "ar": "أبحث عن أسعار السعودية لك… ⏳",
    },
    "search_progress_1": {
        "en": "Checking Saudia fares for you… ⏳",
        "ar": "أبحث عن أسعار السعودية لك… ⏳",
    },
    "search_progress_2": {
        "en": "Still working — querying Saudia and our fare feed…",
        "ar": "ما زلت أعمل — أتحقق من السعودية ومصدر الأسعار…",
    },
    "search_progress_3": {
        "en": "Comparing your dates and nearby days (±3)…",
        "ar": "أقارن تواريخك والأيام القريبة (±٣)…",
    },
    "search_progress_4": {
        "en": "Almost done — Saudia site can be slow; hang on…",
        "ar": "اقتربنا من النهاية — موقع السعودية قد يكون بطيء…",
    },
    "search_timeout": {
        "en": "Search took too long. Please try again in a moment.",
        "ar": "استغرق البحث وقتاً طويلاً. حاول مرة أخرى بعد قليل.",
    },
    "search_results_title": {
        "en": "Here’s what I found ✈️",
        "ar": "هذا ما وجدته ✈️",
    },
    "result_exact_badge": {
        "en": "✓ Fare for your dates",
        "ar": "✓ سعر لتواريخك",
    },
    "result_indicative_badge": {
        "en": "📅 Indicative monthly fare",
        "ar": "📅 سعر شهري تقريبي",
    },
    "result_fare_round": {
        "en": (
            "{badge}\n\n"
            "Your fare to travel from ✈️ {origin} to ✈️ {destination}, "
            "from {dep} to {ret}, is:\n\n"
            "💚 {sar} SAR  ·  ≈ {usd} USD"
        ),
        "ar": (
            "{badge}\n\n"
            "تعريفتك للسفر من ✈️ {origin} إلى ✈️ {destination}، "
            "من {dep} إلى {ret}، هي:\n\n"
            "💚 {sar} ريال  ·  ≈ {usd} دولار"
        ),
    },
    "result_fare_oneway": {
        "en": (
            "{badge}\n\n"
            "Your fare to travel from ✈️ {origin} to ✈️ {destination} "
            "on {dep} (one way) is:\n\n"
            "💚 {sar} SAR  ·  ≈ {usd} USD"
        ),
        "ar": (
            "{badge}\n\n"
            "تعريفتك للسفر من ✈️ {origin} إلى ✈️ {destination} "
            "في {dep} (ذهاب فقط) هي:\n\n"
            "💚 {sar} ريال  ·  ≈ {usd} دولار"
        ),
    },
    "result_indicative": {
        "en": "Confirm your exact dates on Saudia when booking.",
        "ar": "أكد تواريخك المحددة على موقع السعودية عند الحجز.",
    },
    "result_flex_header": {
        "en": "🔄 Nearby dates that might work better:",
        "ar": "🔄 تواريخ قريبة قد تناسبك:",
    },
    "flex_offset_before": {
        "en": "{n} days earlier",
        "ar": "قبل {n} أيام",
    },
    "flex_offset_after": {
        "en": "{n} days later",
        "ar": "بعد {n} أيام",
    },
    "flex_save": {
        "en": " · save {amount} SAR",
        "ar": " · وفّر {amount} ريال",
    },
    "result_flex_line": {
        "en": "• {offset} · ✈️ {origin} → ✈️ {dest} · {dates} — {sar} SAR{save}{over}",
        "ar": "• {offset} · ✈️ {origin} → ✈️ {dest} · {dates} — {sar} ريال{save}{over}",
    },
    "book_button": {
        "en": "Book on Saudia · {sar} SAR",
        "ar": "احجز على السعودية · {sar} ريال",
    },
    "book_tip": {
        "en": "Tap the green button below to open Saudia with your search pre-filled.",
        "ar": "اضغط الزر الأخضر أدناه لفتح موقع السعودية مع بحثك جاهزاً.",
    },
    "search_again": {
        "en": "🔍 Search again",
        "ar": "🔍 بحث جديد",
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
    "disclaimer_short": {
        "en": "Indicative demo fares — confirm on saudia.com.",
        "ar": "أسعار تجريبية — أكد على saudia.com.",
    },
    "cancelled": {"en": "Cancelled.", "ar": "تم الإلغاء."},
    "quote_failed": {
        "en": "Could not fetch live fares right now. Try again in a moment.",
        "ar": "تعذر جلب الأسعار الآن. حاول مرة أخرى بعد قليل.",
    },
}


def t(key: str, lang: Lang, **fmt: str) -> str:
    block = STRINGS.get(key)
    if not block:
        return key
    text = block.get(lang, block["en"])
    if fmt:
        return text.format(**fmt)
    return text
