"""Application configuration using Pydantic Settings."""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """Central application settings.

    All AI API keys are read from the environment and NEVER exposed to the
    frontend.  Only safe metadata (provider id + configured flag) is returned
    via the settings API.
    """

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Application ---
    app_name: str = "CVGen Pro"
    app_version: str = "2.0.0"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 3000

    # --- Database (SQLite, optional, ready for future use) ---
    database_url: str = f"sqlite:///{BASE_DIR / 'data' / 'cvgen.db'}"

    # --- Cloud AI provider API keys (server-side only) ---
    gemini_api_key: str = ""
    gemini_backup_keys: str = ""  # comma separated
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    openrouter_api_key: str = ""
    groq_api_key: str = ""
    deepseek_api_key: str = ""
    mistral_api_key: str = ""
    xai_api_key: str = ""

    # --- Default provider ---
    default_ai_provider: str = "gemini"
    backup_ai_provider: str = "openrouter"

    # --- AI request settings ---
    ai_request_timeout: int = 60
    ai_max_retries: int = 2

    # --- PDF / preview ---
    pdf_page_size: str = "A4"
    pdf_margin_top: str = "14mm"
    pdf_margin_bottom: str = "14mm"
    pdf_margin_left: str = "14mm"
    pdf_margin_right: str = "14mm"

    # --- Paths ---
    @property
    def base_dir(self) -> Path:
        return BASE_DIR

    @property
    def templates_dir(self) -> Path:
        return BASE_DIR / "app" / "templates"

    @property
    def static_dir(self) -> Path:
        return BASE_DIR / "app" / "static"

    @property
    def fonts_dir(self) -> Path:
        return BASE_DIR / "app" / "static" / "fonts"

    # --- Helpers ---
    def get_provider_keys(self, provider: str) -> List[str]:
        """Return list of valid (non-empty) API keys for a provider, including backups."""
        key_map = {
            "gemini": ("gemini_api_key", "gemini_backup_keys"),
            "google": ("gemini_api_key", "gemini_backup_keys"),
            "openai": ("openai_api_key", ""),
            "anthropic": ("anthropic_api_key", ""),
            "claude": ("anthropic_api_key", ""),
            "openrouter": ("openrouter_api_key", ""),
            "groq": ("groq_api_key", ""),
            "deepseek": ("deepseek_api_key", ""),
            "mistral": ("mistral_api_key", ""),
            "xai": ("xai_api_key", ""),
        }
        primary_attr, backup_attr = key_map.get(provider.lower(), ("", ""))
        keys: List[str] = []
        if primary_attr:
            val = getattr(self, primary_attr, "")
            if val:
                # Support comma-separated backup keys
                for k in str(val).split(","):
                    k = k.strip()
                    if k:
                        keys.append(k)
        return keys


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
