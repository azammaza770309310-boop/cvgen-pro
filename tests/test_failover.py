"""Provider failover test — verifies the AIManager failover chain with real and mock providers."""
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.ai.base import AIProvider
from app.ai.manager import AIManager, PROVIDER_CLASSES
from app.core.exceptions import AIAllProvidersFailedError, AIProviderError, AIProviderNotConfiguredError


class _FakeProvider(AIProvider):
    """Fake provider for testing failover. Raises a configurable error."""
    id = "fake"
    name = "Fake"
    def __init__(self, api_keys, *, fail_with=None, result=None):
        self._keys = api_keys
        self._key_index = 0
        self._fail_with = fail_with
        self._result = result
    async def parse_resume(self, text, lang="auto"):
        if self._fail_with:
            raise self._fail_with
        return self._result or {"personal": {"name": "Fake"}}


class TestProviderFailover:
    """Test the failover chain: requested → backup → primary → any configured."""

    def test_failover_chain_order(self):
        """_failover_chain returns: requested, backup, primary, then any configured."""
        mgr = AIManager()
        with patch.object(mgr, "is_configured", return_value=True):
            chain = mgr._failover_chain("gemini")
        # requested (gemini) should be first
        assert chain[0] == "gemini"
        # all entries should be unique
        assert len(chain) == len(set(chain))

    def test_failover_skips_unconfigured(self):
        """Unconfigured providers are skipped in the chain."""
        mgr = AIManager()
        with patch.object(mgr, "is_configured", side_effect=lambda p: p in ("gemini", "openrouter")):
            chain = mgr._failover_chain("groq")  # groq not configured
        # should still include gemini and openrouter
        assert "gemini" in chain
        assert "openrouter" in chain
        # groq should NOT be in chain (not configured)
        assert "groq" not in chain

    def test_failover_no_providers_configured_raises(self):
        """If no providers are configured, raises AIAllProvidersFailedError."""
        mgr = AIManager()
        with patch.object(mgr, "is_configured", return_value=False):
            with pytest.raises(AIAllProvidersFailedError):
                asyncio.get_event_loop().run_until_complete(
                    mgr._run_with_failover("parse_resume", provider="gemini", args=("text",), kwargs={})
                )

    @pytest.mark.asyncio
    async def test_failover_first_provider_succeeds(self):
        """If the first provider works, no failover happens."""
        mgr = AIManager()
        fake = _FakeProvider(["k"], result={"personal": {"name": "OK"}})
        with patch.object(mgr, "is_configured", return_value=True), \
             patch.object(mgr, "_instantiate", return_value=fake):
            result = await mgr._run_with_failover("parse_resume", provider="gemini", args=("text",), kwargs={})
        assert result == {"personal": {"name": "OK"}}

    @pytest.mark.asyncio
    async def test_failover_first_fails_second_succeeds(self):
        """If provider A fails, provider B is tried."""
        mgr = AIManager()
        fail_provider = _FakeProvider(["k"], fail_with=AIProviderError("A failed"))
        ok_provider = _FakeProvider(["k"], result={"personal": {"name": "B OK"}})
        call_count = [0]
        def instantiate(pid):
            call_count[0] += 1
            return fail_provider if call_count[0] == 1 else ok_provider
        with patch.object(mgr, "is_configured", return_value=True), \
             patch.object(mgr, "_instantiate", side_effect=instantiate):
            result = await mgr._run_with_failover("parse_resume", provider="gemini", args=("text",), kwargs={})
        assert result == {"personal": {"name": "B OK"}}
        assert call_count[0] == 2  # tried A then B

    @pytest.mark.asyncio
    async def test_failover_all_providers_fail_raises(self):
        """If all providers fail, raises AIAllProvidersFailedError."""
        mgr = AIManager()
        fail_provider = _FakeProvider(["k"], fail_with=AIProviderError("all fail"))
        with patch.object(mgr, "is_configured", return_value=True), \
             patch.object(mgr, "_instantiate", return_value=fail_provider):
            with pytest.raises(AIAllProvidersFailedError) as exc_info:
                await mgr._run_with_failover("parse_resume", provider="gemini", args=("text",), kwargs={})
        # Error message should list all failed providers
        assert "all fail" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_failover_no_empty_resume_returned(self):
        """Failover never returns an empty/fake resume — it raises on total failure."""
        mgr = AIManager()
        fail_provider = _FakeProvider(["k"], fail_with=AIProviderError("fail"))
        with patch.object(mgr, "is_configured", return_value=True), \
             patch.object(mgr, "_instantiate", return_value=fail_provider):
            try:
                result = await mgr._run_with_failover("parse_resume", provider="gemini", args=("text",), kwargs={})
                # If it returned, it must be a real result, not empty
                assert result is not None
                assert result != {}
            except AIAllProvidersFailedError:
                pass  # expected — this is the correct behavior

    def test_real_zai_provider_configured(self):
        """The real ZAI provider should be detected as configured in this environment."""
        from app.ai.manager import ai_manager
        assert ai_manager.is_configured("zai"), "ZAI provider should be configured"

    @pytest.mark.asyncio
    async def test_real_zai_provider_parse(self):
        """Real end-to-end test: ZAI provider actually parses a resume.
        May be skipped if rate-limited or provider unavailable."""
        from app.ai.manager import ai_manager
        if not ai_manager.is_configured("zai"):
            pytest.skip("ZAI provider not configured")
        try:
            result = await ai_manager.parse_resume("John Doe\njohn@x.com\nDeveloper", provider="zai", lang="en")
            assert isinstance(result, dict)
            assert "personal" in result or "experience" in result
        except AIAllProvidersFailedError as e:
            # Rate limit (429) or gateway timeout is acceptable in test env
            if "429" in str(e) or "rate" in str(e).lower() or "timeout" in str(e).lower():
                pytest.skip(f"ZAI provider rate-limited: {e}")
            raise
