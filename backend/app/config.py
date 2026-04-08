"""
Application configuration.

Secrets are loaded from HashiCorp Vault when VAULT_ADDR is set.
Falls back to environment variables if Vault is unavailable.
"""
import os
from pydantic_settings import BaseSettings

from app.services.vault_service import get_secret, init_vault, is_vault_active


# Initialize Vault early — before Settings is instantiated.
# If VAULT_ADDR is not set, this is a no-op and get_secret() falls back to env vars.
init_vault()


class Settings(BaseSettings):
    # Environment (not a secret — always from env)
    env: str = os.getenv("ENV", "development")

    # ── Secrets (from Vault → env var fallback) ──

    # Database
    database_url: str = get_secret("DATABASE_URL", "postgresql+asyncpg://retv_user:retv_secret@localhost:5432/retv")

    # Database pool settings (not secrets)
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_timeout: int = 30

    def get_async_url(self) -> str:
        """Convert postgres:// URL to postgresql+asyncpg://"""
        url = self.database_url
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif not url.startswith("postgresql+asyncpg://"):
            url = "postgresql+asyncpg://" + url.split("://", 1)[1] if "://" in url else url
        return url

    # JWT
    jwt_secret: str = get_secret("JWT_SECRET", "")
    jwt_algorithm: str = "HS256"
    jwt_expiry_days: int = 30

    # OAuth
    google_client_id: str = get_secret("GOOGLE_CLIENT_ID", "")
    apple_client_id: str = get_secret("APPLE_CLIENT_ID", "")

    # WebAuthn (Passkeys)
    webauthn_rp_id: str = get_secret("WEBAUTHN_RP_ID", "localhost")
    webauthn_rp_name: str = os.getenv("WEBAUTHN_RP_NAME", "Adajoon")
    webauthn_origin: str = get_secret("WEBAUTHN_ORIGIN", "http://localhost:5173")

    # API Keys
    sync_api_key: str = get_secret("SYNC_API_KEY", "")

    # External APIs (public URLs, not secrets)
    iptv_api_base: str = "https://iptv-org.github.io/api"
    iptv_github_url: str = "https://raw.githubusercontent.com/iptv-org/iptv/master/streams.json"
    radio_browser_api: str = "https://de1.api.radio-browser.info"

    # Redis
    redis_url: str = get_secret("REDIS_URL", "redis://localhost:6379")

    # AI Search
    anthropic_api_key: str = get_secret("ANTHROPIC_API_KEY", "")
    ai_search_enabled: bool = os.getenv("AI_SEARCH_ENABLED", "true").lower() == "true"
    ai_model: str = os.getenv("AI_MODEL", "claude-sonnet-4-20250514")

    # Stripe
    stripe_secret_key: str = get_secret("STRIPE_SECRET_KEY", "")
    stripe_webhook_secret: str = get_secret("STRIPE_WEBHOOK_SECRET", "")
    stripe_publishable_key: str = get_secret("STRIPE_PUBLISHABLE_KEY", "")

    # Vault status (computed, not a setting)
    vault_active: bool = is_vault_active()

    @property
    def cors_origins(self) -> list[str]:
        """Parse CORS origins from Vault/env or use defaults."""
        cors_env = get_secret("CORS_ORIGINS", "")
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
            errors.append("JWT_SECRET must be set (in Vault or as env var)")
        elif len(self.jwt_secret) < 32:
            errors.append("JWT_SECRET must be at least 32 characters long")
        elif self.jwt_secret == "change-me-in-production":
            errors.append("JWT_SECRET must not be the default value 'change-me-in-production'")

        if self.env == "production":
            if "localhost" in self.database_url:
                errors.append("DATABASE_URL must not contain 'localhost' in production")

            if "localhost" in self.redis_url:
                errors.append("REDIS_URL must not contain 'localhost' in production")

            if self.stripe_secret_key and not self.stripe_webhook_secret:
                errors.append("STRIPE_WEBHOOK_SECRET must be set when using Stripe in production")

        if errors:
            error_msg = "Configuration validation failed:\n  - " + "\n  - ".join(errors)
            raise ValueError(error_msg)

    class Config:
        env_file = ".env"


settings = Settings()
settings.validate_config()
