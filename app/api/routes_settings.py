"""Settings API routes — provider metadata + key management.

Allows users to:
- View provider status (configured/not, never the actual key)
- Add API keys via the website UI
- Delete keys added via UI (env keys can't be deleted from UI)
- View masked keys (first 4 + last 4 chars only)
- Get links to obtain API keys for each provider
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.ai.manager import ai_manager
from app.core.config import settings
from app.services.key_store import (
    PROVIDER_KEY_LINKS,
    add_key,
    delete_key,
    get_key_sources,
    get_all_keys,
)

router = APIRouter(prefix="/api/settings", tags=["settings"])


class AddKeyRequest(BaseModel):
    provider: str
    key: str


class DeleteKeyRequest(BaseModel):
    provider: str
    index: int  # index in the file_keys list (not env)


@router.get("/")
async def get_settings():
    """Return safe provider metadata + key management info."""
    providers = []
    for p in ai_manager.list_providers():
        pid = p["id"]
        key_info = get_key_sources(pid)
        link = PROVIDER_KEY_LINKS.get(pid, {})
        providers.append({
            "id": pid,
            "name": p["name"],
            "description": p.get("description", ""),
            "website": p.get("website", ""),
            "configured": p["configured"],
            "enabled": p["enabled"],
            "has_backup": len(key_info) > 1,
            "key_count": len(key_info),
            "keys": key_info,
            "key_link": link.get("url", ""),
            "key_link_label": link.get("label", ""),
        })
    return {
        "app_name": settings.app_name,
        "app_version": settings.app_version,
        "default_provider": settings.default_ai_provider,
        "backup_provider": settings.backup_ai_provider,
        "providers": providers,
    }


@router.get("/providers")
async def get_providers():
    """Alias for backwards compatibility."""
    return {"providers": ai_manager.list_providers()}


@router.post("/keys")
async def add_api_key(req: AddKeyRequest):
    """Add an API key for a provider. Multiple keys per provider supported.
    Validates key format for known providers."""
    if not req.provider or not req.key:
        raise HTTPException(status_code=400, detail="Provider and key are required")
    
    provider = req.provider.lower()
    key = req.key.strip()
    
    # Validate provider exists
    from app.ai.manager import PROVIDER_META
    if provider not in PROVIDER_META:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")
    
    # Key format validation (warn but don't block)
    warnings = []
    if provider == "gemini" and not key.startswith("AIza"):
        warnings.append("تنبيه: مفاتيح Gemini عادة تبدأ بـ 'AIza'. تأكد أنك نسخت المفتاح الصحيح من Google AI Studio.")
    elif provider == "openai" and not key.startswith("sk-"):
        warnings.append("تنبيه: مفاتيح OpenAI عادة تبدأ بـ 'sk-'. تأكد من نسخ المفتاح الصحيح.")
    elif provider == "groq" and not key.startswith("gsk_"):
        warnings.append("تنبيه: مفاتيح Groq عادة تبدأ بـ 'gsk_'. تأكد من نسخ المفتاح الصحيح.")
    elif provider == "anthropic" and not key.startswith("sk-ant-"):
        warnings.append("تنبيه: مفاتيح Anthropic عادة تبدأ بـ 'sk-ant-'. تأكد من نسخ المفتاح الصحيح.")
    
    added = add_key(provider, key)
    if not added:
        raise HTTPException(status_code=409, detail="Key already exists for this provider")
    
    return {
        "success": True,
        "provider": provider,
        "message": f"Key added successfully. Provider now has {len(get_key_sources(provider))} key(s).",
        "warnings": warnings,
    }


@router.delete("/keys/{provider}/{index}")
async def delete_api_key(provider: str, index: int):
    """Delete a file-stored key by index. Env keys cannot be deleted from UI."""
    provider = provider.lower()
    deleted = delete_key(provider, index)
    if not deleted:
        raise HTTPException(status_code=404, detail="Key not found or cannot be deleted (env keys are managed via environment variables)")
    
    return {
        "success": True,
        "provider": provider,
        "message": "Key deleted successfully."
    }


@router.post("/test-key")
async def test_key(provider: str):
    """Return whether a provider is configured."""
    configured = ai_manager.is_configured(provider)
    return {"provider": provider, "configured": configured, "enabled": configured}


@router.get("/key-links")
async def get_key_links():
    """Return links to obtain API keys for each provider."""
    return {"links": PROVIDER_KEY_LINKS}
