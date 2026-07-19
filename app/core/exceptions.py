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
