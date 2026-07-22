"""Export schemas."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class DesignControls(BaseModel):
    """Design controls from the preview editor — passed to PDF export so the
    exported PDF matches what the user sees in the preview."""
    fontSize: float = 11.0
    lineHeight: float = 1.5
    sectionSpacing: float = 2.0
    columnDistance: float = 4.0
    margin: float = 15.0


class ExportRequest(BaseModel):
    data: dict
    template_id: str = "official_bilingual_master"
    lang: str = "en"
    filename: Optional[str] = None
    controls: Optional[DesignControls] = None
