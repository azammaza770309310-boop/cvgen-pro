"""Settings API routes — provider metadata + key management.

Allows users to:
- View provider status (configured/not, never the actual key)
- Add API keys via the website UI (NO prefix validation — accept any key)
- Delete keys added via UI (env keys can't be deleted from UI)
- View masked keys (first 4 + last 4 chars only)
- Get links to obtain API keys for each provider
- Test a Gemini API key with a REAL request to Google's API
"""
from __future__ import annotations

import logging

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.ai.manager import ai_manager
from app.core.config import settings
from app.services.key_store import (
    PROVIDER_KEY_LINKS,
    add_key,
    delete_key,
    get_key_sources,
)

logger = logging.getLogger("cvgen.api.settings")

router = APIRouter(prefix="/api/settings", tags=["settings"])


class AddKeyRequest(BaseModel):
    provider: str
    key: str


class TestGeminiRequest(BaseModel):
    key: str


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

    NO prefix validation — accept the key exactly as entered (trimmed only).
    The key will be validated by a real API request when the user tests it.
    """
    if not req.provider or not req.key:
        raise HTTPException(status_code=400, detail="Provider and key are required")

    provider = req.provider.lower()
    key = req.key.strip()  # trim accidental spaces only

    # Validate provider exists
    from app.ai.manager import PROVIDER_META
    if provider not in PROVIDER_META:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")

    added = add_key(provider, key)
    if not added:
        raise HTTPException(status_code=409, detail="Key already exists for this provider")

    return {
        "success": True,
        "provider": provider,
        "message": f"Key added successfully. Provider now has {len(get_key_sources(provider))} key(s).",
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


@router.post("/test-gemini")
async def test_gemini_key(req: TestGeminiRequest):
    """Test a Gemini API key with a REAL request to Google's Gemini API.

    Makes an actual authenticated request and returns the exact result.
    Does NOT validate by prefix — validates by real API response.
    """
    key = req.key.strip()
    if not key:
        return {"success": False, "error": "No key provided", "error_type": "empty_key"}

    # Mask key for logging (never log the full key)
    masked = key[:4] + "..." + key[-4:] if len(key) > 12 else "****"

    # Use the v1beta endpoint with a currently supported model
    # Use gemini-1.5-pro model (as requested)
    model = "gemini-1.5-pro"
    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"

    # Minimal test prompt
    payload = {
        "contents": [{"role": "user", "parts": [{"text": "Reply with exactly: OK"}]}],
        "generationConfig": {
            "temperature": 0,
            "maxOutputTokens": 10,
        },
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(endpoint, json=payload)

        # Log masked key + status (never the full key)
        logger.info("Gemini test: key=%s status=%d", masked, resp.status_code)

        if resp.status_code == 200:
            data = resp.json()
            # Extract the response text
            try:
                parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
                response_text = "".join(p.get("text", "") for p in parts).strip()
            except (IndexError, KeyError):
                response_text = "(no text in response)"

            return {
                "success": True,
                "message": "Gemini API Connected Successfully",
                "endpoint": f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                "model": model,
                "http_status": 200,
                "authenticated": True,
                "response_received": True,
                "response_text": response_text[:100],
                "key_masked": masked,
            }

        # Error responses — return the REAL error from Google
        error_detail = ""
        error_type = "unknown"
        try:
            error_data = resp.json()
            error_detail = error_data.get("error", {}).get("message", str(error_data))[:500]
            error_status = error_data.get("error", {}).get("status", "")
        except Exception:
            error_detail = resp.text[:500]

        # Categorize the error
        if resp.status_code == 400:
            if "API key not valid" in error_detail or "API_KEY_INVALID" in error_detail:
                error_type = "invalid_key"
            elif "model" in error_detail.lower() and "not found" in error_detail.lower():
                error_type = "model_not_found"
            else:
                error_type = "invalid_request"
        elif resp.status_code == 401 or resp.status_code == 403:
            if "permission" in error_detail.lower() or "forbidden" in error_detail.lower():
                error_type = "permission_error"
            else:
                error_type = "auth_error"
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
            "endpoint": f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            "model": model,
            "http_status": resp.status_code,
            "authenticated": resp.status_code != 400 or "API key not valid" not in error_detail,
            "response_received": False,
            "key_masked": masked,
        }

    except httpx.ConnectError as e:
        logger.warning("Gemini test network error: key=%s error=%s", masked, str(e)[:100])
        return {
            "success": False,
            "error": f"Network error: {e}",
            "error_type": "network_error",
            "endpoint": f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            "model": model,
            "http_status": 0,
            "authenticated": False,
            "response_received": False,
            "key_masked": masked,
        }
    except httpx.TimeoutException as e:
        logger.warning("Gemini test timeout: key=%s", masked)
        return {
            "success": False,
            "error": f"Request timed out: {e}",
            "error_type": "network_error",
            "endpoint": f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            "model": model,
            "http_status": 0,
            "authenticated": False,
            "response_received": False,
            "key_masked": masked,
        }
    except Exception as e:
        logger.exception("Gemini test unexpected error: key=%s", masked)
        return {
            "success": False,
            "error": f"Unexpected error: {e}",
            "error_type": "unknown",
            "endpoint": f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            "model": model,
            "http_status": 0,
            "authenticated": False,
            "response_received": False,
            "key_masked": masked,
        }


@router.get("/key-links")
async def get_key_links():
    """Return links to obtain API keys for each provider."""
    return {"links": PROVIDER_KEY_LINKS}
