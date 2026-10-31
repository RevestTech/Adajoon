"""Admin-facing wrapper around the shared Vault client for the Secrets tab.

Write-only from the UI's perspective - a secret's value is never read back
once set, only whether it's configured (in the vault, via an env var
fallback, or not at all). Scoped to a fixed whitelist of keys this app
actually uses (see MANAGED_SECRETS) rather than exposing vault.list()/
vault.history(), which are admin-vault-token-only operations our app's
scoped role isn't issued for anyway.
"""

import logging
import os

from app.config import get_vault
from app.vault_client import VaultSealed

logger = logging.getLogger(__name__)

VAULT_PREFIX = "adajoon:"

# key: the bare vault key (prefixed with VAULT_PREFIX) and the env var this
# app falls back to (via _get_secret) when no vault is configured.
MANAGED_SECRETS = [
    {
        "key": "tmdb_api_key",
        "label": "TMDb API Key",
        "description": "Free key from themoviedb.org/settings/api - powers "
        "poster/metadata lookup when adding a movie.",
        "sensitive": False,
    },
    {
        "key": "anthropic_api_key",
        "label": "Anthropic API Key",
        "description": "Powers AI-assisted search.",
        "sensitive": True,
    },
    {
        "key": "google_client_id",
        "label": "Google OAuth Client ID",
        "description": "Google sign-in.",
        "sensitive": False,
    },
    {
        "key": "apple_client_id",
        "label": "Apple OAuth Client ID",
        "description": "Sign in with Apple.",
        "sensitive": False,
    },
    {
        "key": "stripe_secret_key",
        "label": "Stripe Secret Key",
        "description": "Server-side Stripe API calls (checkout, portal).",
        "sensitive": True,
    },
    {
        "key": "stripe_webhook_secret",
        "label": "Stripe Webhook Secret",
        "description": "Verifies incoming Stripe webhook signatures.",
        "sensitive": True,
    },
    {
        "key": "stripe_publishable_key",
        "label": "Stripe Publishable Key",
        "description": "Sent to the browser for Stripe.js - not secret, "
        "but kept here so it's set alongside the rest.",
        "sensitive": False,
    },
    {
        "key": "sync_api_key",
        "label": "Sync API Key",
        "description": "Authenticates calls to the catalog sync endpoints.",
        "sensitive": True,
    },
]

_MANAGED_KEYS = {s["key"] for s in MANAGED_SECRETS}


class SecretNotManaged(Exception):
    """Raised when a key isn't in MANAGED_SECRETS - never write/delete an
    arbitrary vault key from this UI."""


def _check_managed(key: str) -> None:
    if key not in _MANAGED_KEYS:
        raise SecretNotManaged(key)


def get_secret_status() -> list[dict]:
    """Per managed key: whether it's set, and where (vault vs. env var
    fallback), without ever returning the value itself."""
    vault = get_vault()
    statuses = []
    for secret in MANAGED_SECRETS:
        key = secret["key"]
        source = "unconfigured"
        if vault:
            try:
                source = (
                    "vault" if vault.has(f"{VAULT_PREFIX}{key}") else "unconfigured"
                )
            except VaultSealed:
                source = "sealed"
            except Exception as e:
                logger.warning(
                    "vault.has(%s) failed: %s: %s", key, type(e).__name__, e
                )
                source = "error"
        if source == "unconfigured" and os.getenv(key.upper()):
            source = "env"
        statuses.append({**secret, "source": source})
    return statuses


def set_secret(key: str, value: str) -> None:
    _check_managed(key)
    vault = get_vault()
    if not vault:
        raise RuntimeError("Vault is not configured in this environment")
    vault.set(f"{VAULT_PREFIX}{key}", value)


def delete_secret(key: str) -> None:
    _check_managed(key)
    vault = get_vault()
    if not vault:
        raise RuntimeError("Vault is not configured in this environment")
    vault.delete(f"{VAULT_PREFIX}{key}")
