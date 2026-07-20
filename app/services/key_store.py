"""API Key Store — manages multiple keys per provider with persistent storage.

Keys come from TWO sources, merged at runtime:
1. Environment variables (set in Render dashboard) — primary, persistent across redeploys
2. JSON file (data/api_keys.json) — added via the website UI, persists across restarts

The store supports:
- Multiple keys per provider
- Add / delete keys via API
- Automatic key rotation when one hits rate limits (429)
- Key masking in API responses (never expose full key to browser)
"""
from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Dict, List

from app.core.config import settings

# Path to the JSON key file
_KEYS_FILE = Path(__file__).resolve().parent.parent.parent / "data" / "api_keys.json"
_lock = threading.Lock()

# Links to get API keys for each provider
PROVIDER_KEY_LINKS = {
    "gemini": {"url": "https://aistudio.google.com/apikey", "label": "Google AI Studio"},
    "openai": {"url": "https://platform.openai.com/api-keys", "label": "OpenAI Platform"},
    "anthropic": {"url": "https://console.anthropic.com/settings/keys", "label": "Anthropic Console"},
    "openrouter": {"url": "https://openrouter.ai/keys", "label": "OpenRouter Keys"},
    "groq": {"url": "https://console.groq.com/keys", "label": "Groq Console"},
    "deepseek": {"url": "https://platform.deepseek.com/api_keys", "label": "DeepSeek Platform"},
    "mistral": {"url": "https://console.mistral.ai/api-keys", "label": "Mistral Console"},
    "xai": {"url": "https://console.x.ai", "label": "xAI Console"},
}


def _ensure_data_dir():
    """Ensure the data directory exists."""
    _KEYS_FILE.parent.mkdir(parents=True, exist_ok=True)


def _load_file_keys() -> Dict[str, List[str]]:
    """Load keys from the JSON file."""
    if not _KEYS_FILE.exists():
        return {}
    try:
        with open(_KEYS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return {k: list(v) for k, v in data.items() if isinstance(v, list)}
    except (json.JSONDecodeError, IOError):
        pass
    return {}


def _save_file_keys(keys: Dict[str, List[str]]):
    """Save keys to the JSON file."""
    _ensure_data_dir()
    with open(_KEYS_FILE, "w", encoding="utf-8") as f:
        json.dump(keys, f, indent=2, ensure_ascii=False)


def get_all_keys(provider: str = "") -> Dict[str, List[str]]:
    """Get ALL keys for a provider (or all providers) — env + file combined.

    Returns dict: {"gemini": ["key1", "key2"], "openai": [...], ...}
    """
    with _lock:
        # Start with env keys
        result: Dict[str, List[str]] = {}
        all_providers = list(settings.get_provider_keys("") or [])  # won't work, need explicit
        
        # Get env keys for each known provider
        from app.ai.manager import PROVIDER_META
        for pid in PROVIDER_META:
            env_keys = settings.get_provider_keys(pid)
            if env_keys:
                result[pid] = list(env_keys)
        
        # Merge file keys (deduplicated)
        file_keys = _load_file_keys()
        for pid, keys in file_keys.items():
            if pid not in result:
                result[pid] = []
            for k in keys:
                if k and k not in result[pid]:
                    result[pid].append(k)
        
        # Filter to single provider if requested
        if provider:
            return {provider: result.get(provider, [])}
        return result


def get_keys_for_provider(provider: str) -> List[str]:
    """Get all keys for a specific provider (env + file)."""
    return get_all_keys(provider).get(provider, [])


def add_key(provider: str, key: str) -> bool:
    """Add a key for a provider. Returns True if added (not duplicate)."""
    if not key or not key.strip():
        return False
    key = key.strip()
    provider = provider.lower()
    
    with _lock:
        file_keys = _load_file_keys()
        if provider not in file_keys:
            file_keys[provider] = []
        
        # Check if key already exists (in env or file)
        env_keys = settings.get_provider_keys(provider)
        all_existing = set(env_keys + file_keys[provider])
        
        if key in all_existing:
            return False  # duplicate
        
        file_keys[provider].append(key)
        _save_file_keys(file_keys)
        return True


def delete_key(provider: str, key_index: int) -> bool:
    """Delete a key from the file store by index. Returns True if deleted.

    Note: can only delete keys stored in the file, not env vars.
    """
    provider = provider.lower()
    
    with _lock:
        file_keys = _load_file_keys()
        if provider not in file_keys:
            return False
        
        if key_index < 0 or key_index >= len(file_keys[provider]):
            return False
        
        file_keys[provider].pop(key_index)
        if not file_keys[provider]:
            del file_keys[provider]
        _save_file_keys(file_keys)
        return True


def mask_key(key: str) -> str:
    """Mask a key for safe display: show first 4 + last 4 chars."""
    if not key or len(key) < 12:
        return "****"
    return key[:4] + "..." + key[-4:]


def get_key_sources(provider: str) -> List[dict]:
    """Get keys for a provider with source info (env vs file) and masked values.

    Returns: [{"index": 0, "masked": "AIza...abc", "source": "env"},
              {"index": 1, "masked": "sk-p...xyz", "source": "file"}]
    """
    result = []
    env_keys = settings.get_provider_keys(provider)
    file_keys = _load_file_keys().get(provider, [])
    
    # Env keys first (can't be deleted from UI)
    for i, k in enumerate(env_keys):
        result.append({
            "index": i,
            "masked": mask_key(k),
            "source": "env",
            "deletable": False,
        })
    
    # File keys (can be deleted from UI)
    for i, k in enumerate(file_keys):
        result.append({
            "index": len(env_keys) + i,
            "masked": mask_key(k),
            "source": "file",
            "deletable": True,
            "file_index": i,  # actual index in file_keys list
        })
    
    return result
