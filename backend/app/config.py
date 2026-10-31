"""
Application configuration.

Secrets are loaded from railway-vault (centralized encrypted storage).
Database and Redis URLs come from Railway service references.
"""

import os

from pydantic_settings import BaseSettings


def _get_vault_client():
    """Build the AppRole-based vault client (lazy loaded) from
    VAULT_ADDR/VAULT_ROLE_ID/VAULT_SECRET_ID - the one-time enrollment
    output from RevestTech/revest-vault's examples/enroll.py, scoped to
    the `adajoon:*` key prefix. Never a static long-lived token."""
    vault_addr = os.getenv("VAULT_ADDR")
    role_id = os.getenv("VAULT_ROLE_ID")
    secret_id = os.getenv("VAULT_SECRET_ID")

    if not vault_addr or not role_id or not secret_id:
        # Not enrolled with the vault (e.g. local dev) - env var fallback.
        return None

    from app.vault_client import VaultClient

    return VaultClient(addr=vault_addr, role_id=role_id, secret_id=secret_id)


# Initialize vault client once
_vault = _get_vault_client()


def get_vault():
    """The shared vault client, or None if VAULT_ADDR/VAULT_ROLE_ID/
    VAULT_SECRET_ID aren't set (e.g. local dev, not yet enrolled). Used by
    the admin Secrets UI to write/clear keys - reads already go through
    `_get_secret` at startup."""
    return _vault


# Placeholder secret used only when no vault/env value is configured -
# never valid in production, checked explicitly in validate_config().
DEV_JWT_SECRET_DEFAULT = "dev-jwt-secret-change-in-production-min-32-chars"


def _get_secret(key: str, default: str = "") -> str:
    """Get secret from vault, fallback to env var, then default. Never logs
    the secret value itself - only the key name and failure reason."""
    if _vault:
        try:
            return _vault.get(f"adajoon:{key}")
        except KeyError:
            print(f"Vault has no value for {key}, trying env var fallback")
        except Exception as e:
            print(
                f"Warning: vault lookup failed for {key} ({type(e).__name__}: {e}), trying env var fallback"
            )

    # Fallback to environment variable (for development, or if the vault
    # doesn't have this key yet)
    env_key = key.upper()
    return os.getenv(env_key, default)


class Settings(BaseSettings):
    # Environment
    env: str = os.getenv("ENV", "development")

    # Database & Redis (from Railway service references - NOT in vault)
    database_url: str = ""
    redis_url: str = "redis://localhost:6379"

    # Database pool settings
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_timeout: int = 30

    def get_async_url(self) -> str:
        """Convert postgres:// URL to postgresql+asyncpg://"""
        url = self.database_url
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif not url.startswith("postgresql+asyncpg://"):
            url = (
                "postgresql+asyncpg://" + url.split("://", 1)[1]
                if "://" in url
                else url
            )
        return url

    # JWT (from vault)
    jwt_secret: str = _get_secret("jwt_secret", DEV_JWT_SECRET_DEFAULT)
    jwt_algorithm: str = "HS256"
    jwt_expiry_days: int = 30

    # OAuth (from vault)
    google_client_id: str = _get_secret("google_client_id")
    apple_client_id: str = _get_secret("apple_client_id")

    # WebAuthn (from vault)
    webauthn_rp_id: str = _get_secret("webauthn_rp_id", "localhost")
    webauthn_rp_name: str = os.getenv("WEBAUTHN_RP_NAME", "Adajoon")
    webauthn_origin: str = _get_secret("webauthn_origin", "http://localhost:5173")

    @property
    def webauthn_origins(self) -> list[str]:
        """Parse one or more allowed WebAuthn origins (comma-separated env)."""
        raw = (self.webauthn_origin or "").strip()
        if not raw:
            return ["http://localhost:5173"]
        return [o.strip() for o in raw.split(",") if o.strip()]

    # API Keys (from vault)
    sync_api_key: str = _get_secret("sync_api_key")

    # External APIs (public URLs, not secrets)
    iptv_api_base: str = "https://iptv-org.github.io/api"
    iptv_github_url: str = (
        "https://raw.githubusercontent.com/iptv-org/iptv/master/streams.json"
    )
    radio_browser_api: str = "https://de1.api.radio-browser.info"

    # AI Search (from vault)
    anthropic_api_key: str = _get_secret("anthropic_api_key")
    ai_search_enabled: bool = os.getenv("AI_SEARCH_ENABLED", "true").lower() == "true"
    ai_model: str = os.getenv("AI_MODEL", "claude-sonnet-4-20250514")

    # Stripe (from vault)
    stripe_secret_key: str = _get_secret("stripe_secret_key")
    stripe_webhook_secret: str = _get_secret("stripe_webhook_secret")
    stripe_publishable_key: str = _get_secret("stripe_publishable_key")

    # TMDb (The Movie Database) - free API, used only for admin-side poster
    # art/metadata lookup when adding a syndicated movie. Get a free key at
    # https://www.themoviedb.org/settings/api
    tmdb_api_key: str = _get_secret("tmdb_api_key")

    @property
    def cors_origins(self) -> list[str]:
        """Parse CORS origins from env var or use defaults."""
        cors_env = os.getenv("CORS_ORIGINS", "")
        if cors_env:
            return [origin.strip() for origin in cors_env.split(",") if origin.strip()]

        return [
            "http://localhost:5173",
            "http://localhost:3000",
            "https://adajoon.com",
            "https://www.adajoon.com",
        ]

    def validate_config(self) -> None:
        """Validate critical configuration on startup."""
        errors = []

        if not self.jwt_secret:
            errors.append("JWT_SECRET must be set as environment variable")
        elif len(self.jwt_secret) < 32:
            errors.append("JWT_SECRET must be at least 32 characters long")
        elif self.jwt_secret == "change-me-in-production":
            errors.append(
                "JWT_SECRET must not be the default value 'change-me-in-production'"
            )
        elif self.jwt_secret == DEV_JWT_SECRET_DEFAULT and self.env not in (
            "development",
            "dev",
        ):
            errors.append(
                "JWT_SECRET must not be the built-in development default outside development"
            )

        if self.env == "production":
            if "localhost" in self.database_url:
                errors.append("DATABASE_URL must not contain 'localhost' in production")

            if "localhost" in self.redis_url:
                errors.append("REDIS_URL must not contain 'localhost' in production")

            if self.stripe_secret_key and not self.stripe_webhook_secret:
                errors.append(
                    "STRIPE_WEBHOOK_SECRET must be set when using Stripe in production"
                )

        if errors:
            error_msg = "Configuration validation failed:\n  - " + "\n  - ".join(errors)
            raise ValueError(error_msg)

    class Config:
        env_file = ".env"


settings = Settings()
settings.validate_config()
