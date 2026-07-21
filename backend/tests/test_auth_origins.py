"""Config helpers for auth origins / cookies."""

from app.config import Settings


def test_webauthn_origins_parses_comma_list() -> None:
    s = Settings()
    s.webauthn_origin = "https://www.adajoon.com,https://adajoon-production.up.railway.app"
    assert s.webauthn_origins == [
        "https://www.adajoon.com",
        "https://adajoon-production.up.railway.app",
    ]


def test_webauthn_origins_single() -> None:
    s = Settings()
    s.webauthn_origin = "http://localhost:5173"
    assert s.webauthn_origins == ["http://localhost:5173"]
