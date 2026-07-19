"""JSON extraction helper for AI responses."""
from __future__ import annotations

import json
import re
from typing import Any, Optional


def extract_json(text: str) -> Optional[Any]:
    """Extract a JSON object/array from an AI response.

    Handles: pure JSON, ```json fenced blocks, and JSON embedded in prose.
    """
    if not text:
        return None
    text = text.strip()
    # 1) fenced block
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text, re.IGNORECASE)
    if fence:
        text = fence.group(1).strip()
    # 2) direct parse
    try:
        return json.loads(text)
    except Exception:
        pass
    # 3) find first { ... } or [ ... ]
    for opener, closer in (("{", "}"), ("[", "]")):
        start = text.find(opener)
        end = text.rfind(closer)
        if start != -1 and end != -1 and end > start:
            chunk = text[start : end + 1]
            try:
                return json.loads(chunk)
            except Exception:
                continue
    return None
