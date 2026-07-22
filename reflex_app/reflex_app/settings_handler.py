"""Settings handler — native Reflex integration for API key management.

Imports app.services.key_store directly (FastAPI-independent). The Reflex
state calls these functions to list/add/delete/test API keys.

Single Source of Truth: key management logic lives in app/services/key_store.py
and is shared by both backends.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("cvgen.reflex.settings")


def get_settings() -> dict:
    """Return safe provider metadata + key management info (no raw keys)."""
    from app.ai.manager import ai_manager
    from app.services.key_store import get_key_sources, PROVIDER_KEY_LINKS
    from app.core.config import settings

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


def list_providers() -> list[dict]:
    """Return the list of AI providers (safe metadata)."""
    from app.ai.manager import ai_manager
    return ai_manager.list_providers()


def add_api_key(provider: str, key: str) -> dict:
    """Add an API key for a provider. Returns {success, provider, message}."""
    from app.services.key_store import add_key, get_key_sources
    from app.ai.manager import PROVIDER_META

    if not provider or not key:
        return {"success": False, "error": "Provider and key are required"}
    provider = provider.lower()
    key = key.strip()
    if provider not in PROVIDER_META:
        return {"success": False, "error": f"Unknown provider: {provider}"}
    added = add_key(provider, key)
    if not added:
        return {"success": False, "error": "Key already exists for this provider"}
    return {
        "success": True,
        "provider": provider,
        "message": f"Key added successfully. Provider now has {len(get_key_sources(provider))} key(s).",
    }


def delete_api_key(provider: str, index: int) -> dict:
    """Delete a file-stored key by index. Env keys cannot be deleted."""
    from app.services.key_store import delete_key
    provider = provider.lower()
    deleted = delete_key(provider, index)
    if not deleted:
        return {"success": False, "error": "Key not found or cannot be deleted (env keys are managed via environment variables)"}
    return {"success": True, "provider": provider, "message": "Key deleted successfully."}


async def test_gemini_key(key: str) -> dict:
    """Test a Gemini API key with a REAL request to Google's API.

    Returns a dict with success/error/error_type/details. Does NOT validate
    by prefix — validates by real API response.
    """
    import httpx
    key = (key or "").strip()
    if not key:
        return {"success": False, "error": "No key provided", "error_type": "empty_key"}

    masked = key[:4] + "..." + key[-4:] if len(key) > 12 else "****"
    model = "gemini-1.5-flash"
    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    payload = {
        "contents": [{"role": "user", "parts": [{"text": "Reply with exactly: OK"}]}],
        "generationConfig": {"temperature": 0, "maxOutputTokens": 10},
    }
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(endpoint, json=payload)
        logger.info("Gemini test: key=%s status=%d", masked, resp.status_code)
        if resp.status_code == 200:
            data = resp.json()
            try:
                parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
                response_text = "".join(p.get("text", "") for p in parts).strip()
            except (IndexError, KeyError):
                response_text = "(no text in response)"
            return {
                "success": True,
                "message": "Gemini API Connected Successfully",
                "model": model,
                "http_status": 200,
                "authenticated": True,
                "response_text": response_text[:100],
                "key_masked": masked,
            }
        # Error
        error_detail = ""
        error_type = "unknown"
        try:
            error_data = resp.json()
            error_detail = error_data.get("error", {}).get("message", str(error_data))[:500]
        except Exception:
            error_detail = resp.text[:500]
        if resp.status_code == 400:
            if "API key not valid" in error_detail or "API_KEY_INVALID" in error_detail:
                error_type = "invalid_key"
            elif "model" in error_detail.lower() and "not found" in error_detail.lower():
                error_type = "model_not_found"
            else:
                error_type = "invalid_request"
        elif resp.status_code in (401, 403):
            error_type = "permission_error" if "permission" in error_detail.lower() else "auth_error"
        elif resp.status_code == 404:
            error_type = "model_not_found"
        elif resp.status_code == 429:
            error_type = "quota_exceeded"
        elif resp.status_code in (500, 502, 503):
            error_type = "server_error"
        return {
            "success": False,
            "error": error_detail,
            "error_type": error_type,
            "model": model,
            "http_status": resp.status_code,
            "authenticated": resp.status_code != 400 or "API key not valid" not in error_detail,
            "key_masked": masked,
        }
    except httpx.ConnectError as e:
        return {"success": False, "error": f"Network error: {e}", "error_type": "network_error", "key_masked": masked}
    except httpx.TimeoutException:
        return {"success": False, "error": "Request timed out", "error_type": "network_error", "key_masked": masked}
    except Exception as e:
        return {"success": False, "error": f"Unexpected error: {e}", "error_type": "unknown", "key_masked": masked}


def test_provider_configured(provider: str) -> dict:
    """Return whether a provider is configured (has at least one key)."""
    from app.ai.manager import ai_manager
    configured = ai_manager.is_configured(provider)
    return {"provider": provider, "configured": configured, "enabled": configured}


def get_key_links() -> dict:
    """Return links to obtain API keys for each provider."""
    from app.services.key_store import PROVIDER_KEY_LINKS
    return {"links": PROVIDER_KEY_LINKS}
