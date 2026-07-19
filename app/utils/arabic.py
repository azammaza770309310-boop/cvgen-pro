"""Arabic text utilities."""
from __future__ import annotations

import re

ARABIC_RANGE = re.compile(r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]")


def contains_arabic(text: str) -> bool:
    if not text:
        return False
    return bool(ARABIC_RANGE.search(text))


def is_mostly_arabic(text: str, threshold: float = 0.3) -> bool:
    if not text:
        return False
    total = sum(1 for c in text if c.isalpha())
    if total == 0:
        return False
    arabic = sum(1 for c in text if ARABIC_RANGE.match(c))
    return (arabic / total) >= threshold


def detect_lang(text: str) -> str:
    """Return 'ar', 'en', or 'bilingual' based on the text."""
    if not text:
        return "en"
    has_ar = contains_arabic(text)
    # crude english detection: latin letters present
    has_en = bool(re.search(r"[A-Za-z]", text))
    if has_ar and has_en:
        return "bilingual"
    if has_ar:
        return "ar"
    return "en"


def normalize_arabic(text: str) -> str:
    """Light normalization: unify alef variants, remove tatweel."""
    if not text:
        return ""
    text = text.replace("\u0623", "\u0627").replace("\u0625", "\u0627").replace("\u0622", "\u0627")
    text = text.replace("\u0640", "")  # tatweel
    return text
