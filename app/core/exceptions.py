"""Custom application exceptions."""
from __future__ import annotations


class CVGenError(Exception):
    """Base exception for CVGen Pro."""

    status_code: int = 500
    code: str = "cvgen_error"

    def __init__(self, message: str = "", *, code: str | None = None, status_code: int | None = None):
        super().__init__(message or self.code)
        self.message = message or self.code
        if code:
            self.code = code
        if status_code:
            self.status_code = status_code


class AIProviderError(CVGenError):
    status_code = 502
    code = "ai_provider_error"


class AIProviderNotConfiguredError(CVGenError):
    status_code = 400
    code = "ai_provider_not_configured"


class AIInvalidKeyError(AIProviderError):
    """The API key is invalid, expired, or lacks permission.

    Failover SHOULD still try other providers (they have different keys),
    but the error message must clearly state the key is invalid — NOT
    'quota exceeded' or 'rate limited'.
    """
    code = "ai_invalid_key"


class AIQuotaExceededError(AIProviderError):
    """The API key is valid but the quota/rate limit was hit (HTTP 429).

    The key itself is CORRECT — the user has simply exceeded their allowance.
    Failover to another provider is appropriate. The user-facing message must
    say 'quota exceeded', NOT 'invalid key'.
    """
    code = "ai_quota_exceeded"


class AIAllProvidersFailedError(CVGenError):
    status_code = 502
    code = "ai_all_providers_failed"


class ResumeValidationError(CVGenError):
    status_code = 422
    code = "resume_validation_error"


class TemplateNotFoundError(CVGenError):
    status_code = 404
    code = "template_not_found"


class ExportError(CVGenError):
    status_code = 500
    code = "export_error"
