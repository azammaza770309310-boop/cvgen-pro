"""Settings API routes — returns safe provider metadata only."""
from __future__ import annotations

from fastapi import APIRouter

from app.ai.manager import ai_manager
from app.core.config import settings
from app.models.settings import ProviderSetting, SettingsResponse

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("/", response_model=SettingsResponse)
async def get_settings_route():
    providers = [
        ProviderSetting(
            id=p["id"],
            name=p["name"],
            configured=p["configured"],
            enabled=p["enabled"],
            has_backup=p["has_backup"],
            website=p["website"],
            description=p["description"],
        )
        for p in ai_manager.list_providers()
    ]
    return SettingsResponse(
        app_name=settings.app_name,
        app_version=settings.app_version,
        default_provider=settings.default_ai_provider,
        backup_provider=settings.backup_ai_provider,
        providers=providers,
    )


@router.get("/providers")
async def get_providers():
    """Alias for backwards compatibility."""
    return {"providers": ai_manager.list_providers()}


@router.post("/test-key")
async def test_key(provider: str):
    """Return whether a provider is configured. Does NOT test the key itself
    (to avoid leaking keys or making external calls); returns safe metadata.
    """
    configured = ai_manager.is_configured(provider)
    return {"provider": provider, "configured": configured, "enabled": configured}
