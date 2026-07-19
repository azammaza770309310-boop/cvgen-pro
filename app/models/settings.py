"""Settings models (provider metadata etc.)."""
from __future__ import annotations

from typing import List

from pydantic import BaseModel


class ProviderSetting(BaseModel):
    id: str
    name: str
    configured: bool
    enabled: bool
    has_backup: bool
    website: str = ""
    description: str = ""


class SettingsResponse(BaseModel):
    app_name: str
    app_version: str
    default_provider: str
    backup_provider: str
    providers: List[ProviderSetting]
