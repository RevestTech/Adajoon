"""Unit tests for AI search keyword fallback helpers."""
import pytest

from app.services.ai_search_service import (
    _expand_search_terms,
    _score_searchable,
    _tokenize_fallback_query,
)


@pytest.mark.unit
def test_tokenize_fifa_games_keeps_content_words() -> None:
    tokens = _tokenize_fallback_query("fifa games")
    assert tokens == ["fifa", "games"]


@pytest.mark.unit
def test_tokenize_drops_stopwords_keeps_plus() -> None:
    tokens = _tokenize_fallback_query("find me the FIFA+ channel")
    assert "fifa+" in tokens
    assert "find" not in tokens
    assert "me" not in tokens
    assert "the" not in tokens
    assert "channel" not in tokens


@pytest.mark.unit
def test_expand_fifa_adds_sports_terms() -> None:
    terms = _expand_search_terms(["fifa"])
    assert "fifa" in terms
    assert "sports" in terms
    assert "football" in terms
    assert "soccer" in terms


@pytest.mark.unit
def test_score_matches_fifa_plus_channel() -> None:
    score = _score_searchable(
        "FIFA+ sports",
        ["fifa", "games", "sports", "football", "soccer"],
    )
    assert score >= 2
    assert _score_searchable("CNN news", ["fifa", "sports"]) == 0
