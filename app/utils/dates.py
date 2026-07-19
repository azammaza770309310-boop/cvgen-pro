"""Date utilities."""
from __future__ import annotations

import re
from typing import Tuple


MONTHS_EN = {
    "jan": "Jan", "feb": "Feb", "mar": "Mar", "apr": "Apr", "may": "May", "jun": "Jun",
    "jul": "Jul", "aug": "Aug", "sep": "Sep", "oct": "Oct", "nov": "Nov", "dec": "Dec",
    "january": "January", "february": "February", "march": "March", "april": "April",
    "june": "June", "july": "July", "august": "August", "september": "September",
    "october": "October", "november": "November", "december": "December",
}


def split_date_range(date_str: str) -> Tuple[str, str, bool]:
    """Split 'Jan 2020 - Present' into (start, end, current)."""
    if not date_str:
        return "", "", False
    s = date_str.strip()
    current = False
    for token in ("present", "current", "now", "حتى الآن", "الآن"):
        if token.lower() in s.lower():
            current = True
            break
    # split on - or – or — or to
    parts = re.split(r"\s*(?:-|–|—|to|إلى)\s*", s, maxsplit=1, flags=re.IGNORECASE)
    start = parts[0].strip() if parts else ""
    end = parts[1].strip() if len(parts) > 1 else ""
    if current:
        end = "Present"
    return start, end, current


def normalize_year(value: str) -> str:
    """Extract a 4-digit year if present."""
    m = re.search(r"(19|20)\d{2}", value or "")
    return m.group(0) if m else (value or "").strip()
