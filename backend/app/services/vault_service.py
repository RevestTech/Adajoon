"""
HashiCorp Vault integration for secrets management.

All application secrets are stored in Vault instead of environment variables.
The only env vars needed are the Vault connection parameters themselves:

  VAULT_ADDR       — Vault server URL (e.g. https://vault.example.com:8200)
  VAULT_TOKEN      — Direct token auth (dev/simple setups)
  VAULT_ROLE_ID    — AppRole role_id (production)
  VAULT_SECRET_ID  — AppRole secret_id (production)
  VAULT_MOUNT      — KV secrets engine mount point (default: "secret")
  VAULT_PATH       — Path under the mount for Adajoon secrets (default: "adajoon")
  VAULT_NAMESPACE  — HCP Vault namespace (optional, for HCP Vault)

Secrets are fetched once at startup and cached in memory.
"""

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

# Cached secrets dict — populated on startup
_secrets: dict[str, Any] = {}
_vault_initialized = False


def _get_vault_client():
    """Create and authenticate an hvac Vault client."""
    import hvac

    addr = os.getenv("VAULT_ADDR", "")
    if not addr:
        return None

    namespace = os.getenv("VAULT_NAMESPACE", "")
    client = hvac.Client(
        url=addr,
        namespace=namespace or None,
    )

    # Auth method 1: Direct token (simpler, for dev/staging)
    token = os.getenv("VAULT_TOKEN", "")
    if token:
        client.token = token
        if client.is_authenticated():
            logger.info("Vault authenticated via token")
            return client
        logger.warning("Vault token auth failed")
        return None

    # Auth method 2: AppRole (recommended for production)
    role_id = os.getenv("VAULT_ROLE_ID", "")
    secret_id = os.getenv("VAULT_SECRET_ID", "")
    if role_id and secret_id:
        try:
            resp = client.auth.approle.login(role_id=role_id, secret_id=secret_id)
            client.token = resp["auth"]["client_token"]
            logger.info("Vault authenticated via AppRole")
            return client
        except Exception as e:
            logger.error("Vault AppRole auth failed: %s", e)
            return None

    logger.warning("No Vault credentials provided (VAULT_TOKEN or VAULT_ROLE_ID+VAULT_SECRET_ID)")
    return None


def init_vault() -> bool:
    """
    Connect to Vault and load all secrets into memory.
    Returns True if Vault secrets were loaded, False if falling back to env vars.
    """
    global _secrets, _vault_initialized

    addr = os.getenv("VAULT_ADDR", "")
    if not addr:
        logger.info("VAULT_ADDR not set — using environment variables for secrets")
        _vault_initialized = False
        return False

    try:
        client = _get_vault_client()
        if not client:
            logger.warning("Vault client unavailable — falling back to environment variables")
            _vault_initialized = False
            return False

        mount = os.getenv("VAULT_MOUNT", "secret")
        path = os.getenv("VAULT_PATH", "adajoon")

        # Read all secrets from KV v2
        try:
            response = client.secrets.kv.v2.read_secret_version(
                path=path,
                mount_point=mount,
                raise_on_deleted_version=True,
            )
            _secrets = response["data"]["data"]
            _vault_initialized = True
            logger.info(
                "Loaded %d secrets from Vault (mount=%s, path=%s)",
                len(_secrets), mount, path,
            )
            return True
        except Exception as e:
            logger.error("Failed to read secrets from Vault path '%s/%s': %s", mount, path, e)
            _vault_initialized = False
            return False

    except ImportError:
        logger.error("hvac package not installed — cannot connect to Vault. Run: pip install hvac")
        _vault_initialized = False
        return False
    except Exception as e:
        logger.error("Vault initialization error: %s", e)
        _vault_initialized = False
        return False


def get_secret(key: str, default: str = "") -> str:
    """
    Get a secret value. Checks Vault cache first, falls back to env var.

    Args:
        key: Secret key name. In Vault, use the exact key name.
             For env var fallback, the key is used as-is (e.g. "DATABASE_URL").
        default: Default value if not found anywhere.
    """
    if _vault_initialized and key in _secrets:
        return str(_secrets[key])
    # Fallback to environment variable
    return os.getenv(key, default)


def is_vault_active() -> bool:
    """Check if Vault is the active secrets source."""
    return _vault_initialized


def get_all_secret_keys() -> list[str]:
    """Return list of loaded secret key names (for health checks)."""
    if _vault_initialized:
        return list(_secrets.keys())
    return []


def refresh_secrets() -> bool:
    """Re-fetch secrets from Vault (e.g. after rotation)."""
    if not _vault_initialized:
        return False
    return init_vault()


# ── Secret key constants ──
# Use these as the `key` argument to get_secret() so typos are caught early.
# These match the key names stored in Vault AND the env var fallback names.

SECRET_DATABASE_URL = "DATABASE_URL"
SECRET_REDIS_URL = "REDIS_URL"
SECRET_JWT_SECRET = "JWT_SECRET"
SECRET_GOOGLE_CLIENT_ID = "GOOGLE_CLIENT_ID"
SECRET_APPLE_CLIENT_ID = "APPLE_CLIENT_ID"
SECRET_SYNC_API_KEY = "SYNC_API_KEY"
SECRET_ANTHROPIC_API_KEY = "ANTHROPIC_API_KEY"
SECRET_STRIPE_SECRET_KEY = "STRIPE_SECRET_KEY"
SECRET_STRIPE_WEBHOOK_SECRET = "STRIPE_WEBHOOK_SECRET"
SECRET_STRIPE_PUBLISHABLE_KEY = "STRIPE_PUBLISHABLE_KEY"
SECRET_CORS_ORIGINS = "CORS_ORIGINS"
SECRET_WEBAUTHN_RP_ID = "WEBAUTHN_RP_ID"
SECRET_WEBAUTHN_ORIGIN = "WEBAUTHN_ORIGIN"
