"""Unit tests for AI on-now detection."""
import pytest

from app.services.ai_search_service import _tokenize_fallback_query, _wants_epg_on_now


@pytest.mark.unit
def test_wants_epg_on_now_for_live_soccer():
    tokens = _tokenize_fallback_query("live soccer right now")
    assert _wants_epg_on_now(tokens, "live soccer right now") is True


@pytest.mark.unit
def test_wants_epg_on_now_false_for_plain_fifa():
    tokens = _tokenize_fallback_query("fifa games")
    assert _wants_epg_on_now(tokens, "fifa games") is False
