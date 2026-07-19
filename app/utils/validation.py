"""Validation utilities — deterministic contact + section detection."""
from __future__ import annotations

import re
from typing import List, Tuple

# ---------------------------------------------------------------------------
# Contact extractors (deterministic, never AI)
# ---------------------------------------------------------------------------

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
# international + US phone
PHONE_RE = re.compile(
    r"(\+?\d{1,3}[\s.-]?)?(\(?\d{2,4}\)?[\s.-]?)?\d{3,4}[\s.-]?\d{3,4}"
)
LINKEDIN_RE = re.compile(
    r"(?:https?://)?(?:www\.)?linkedin\.com/(?:in|pub|profile)/[A-Za-z0-9_\-%]+/?",
    re.IGNORECASE,
)
GITHUB_RE = re.compile(
    r"(?:https?://)?(?:www\.)?github\.com/[A-Za-z0-9_\-]+/?", re.IGNORECASE
)
WEBSITE_RE = re.compile(
    r"(?:https?://)?(?:www\.)?[a-zA-Z0-9][a-zA-Z0-9\-]*\.[a-zA-Z]{2,}(?:/[^\s]*)?",
    re.IGNORECASE,
)
URL_RE = re.compile(r"https?://[^\s]+", re.IGNORECASE)


def extract_email(text: str) -> str:
    m = EMAIL_RE.search(text or "")
    return m.group(0).strip() if m else ""


def extract_phone(text: str) -> str:
    if not text:
        return ""
    # try to find a phone-like chunk
    for m in PHONE_RE.finditer(text):
        chunk = m.group(0)
        digits = re.sub(r"\D", "", chunk)
        if 7 <= len(digits) <= 15:
            return chunk.strip()
    return ""


def extract_linkedin(text: str) -> str:
    m = LINKEDIN_RE.search(text or "")
    return m.group(0).strip() if m else ""


def extract_github(text: str) -> str:
    m = GITHUB_RE.search(text or "")
    return m.group(0).strip() if m else ""


def extract_website(text: str) -> str:
    """Extract a personal website, excluding linkedin/github/social."""
    if not text:
        return ""
    for m in WEBSITE_RE.finditer(text):
        url = m.group(0).strip().rstrip(".,")
        low = url.lower()
        if any(b in low for b in ("linkedin.com", "github.com", "facebook.com", "twitter.com", "x.com", "instagram.com")):
            continue
        if not url.startswith("http"):
            url = "https://" + url
        return url
    return ""


def is_contact_token(s: str) -> bool:
    """True if the token looks like contact info (email/phone/url)."""
    if not s:
        return False
    return bool(
        EMAIL_RE.search(s)
        or PHONE_RE.fullmatch(s.strip())
        or URL_RE.search(s)
        or LINKEDIN_RE.search(s)
        or GITHUB_RE.search(s)
    )


# ---------------------------------------------------------------------------
# Section heading detection (EN + AR aliases)
# ---------------------------------------------------------------------------

SECTION_ALIASES: dict[str, list[str]] = {
    "summary": [
        "summary", "professional summary", "profile", "about", "about me",
        "objective", "career objective", "الملخص", "نبذة", "نبذة عني", "الهدف المهني", "الخلاصة",
    ],
    "objective": ["objective", "career objective", "الهدف", "الهدف المهني"],
    "experience": [
        "experience", "work experience", "professional experience", "employment",
        "work history", "career history", "الخبرات", "الخبرة العملية", "الخبرة المهنية", "العمل",
    ],
    "education": [
        "education", "academic background", "التعليم", "المؤهلات العلمية", "الدراسة",
    ],
    "skills": [
        "skills", "technical skills", "core skills", "المهارات", "المهارات التقنية", "المهارات الفنية",
    ],
    "soft_skills": ["soft skills", "المهارات الشخصية", "المهارات الناعمة"],
    "courses": ["courses", "training", "الدورات", "الدورات التدريبية", "التدريب"],
    "certifications": [
        "certifications", "certificates", "licenses", "الشهادات", "الشهادات المهنية", "التراخيص",
    ],
    "languages": ["languages", "اللغات", "اللغة"],
    "projects": ["projects", "personal projects", "المشاريع", "المشاريع الشخصية"],
    "volunteering": ["volunteering", "volunteer work", "التطوع", "العمل التطوعي"],
    "achievements": ["achievements", "awards", "الإنجازات", "الجوائز", "التكريمات"],
    "references": ["references", "المراجع", "المعرفون"],
}


def detect_section(line: str) -> str | None:
    """Return canonical section id if the line is a section heading."""
    if not line:
        return None
    s = line.strip().strip(":：•-—").strip().lower()
    if not s or len(s) > 40:
        return None
    for sid, aliases in SECTION_ALIASES.items():
        for a in aliases:
            if s == a:
                return sid
    return None


# ---------------------------------------------------------------------------
# Deduplication
# ---------------------------------------------------------------------------


def dedup_strings(items: List[str]) -> List[str]:
    seen = set()
    out = []
    for it in items or []:
        if not it:
            continue
        key = it.strip().lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(it.strip())
    return out
