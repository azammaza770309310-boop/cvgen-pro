"""Export schemas."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class ExportRequest(BaseModel):
    data: dict
    template_id: str = "official_bilingual_master"
    lang: str = "en"
    filename: Optional[str] = None
