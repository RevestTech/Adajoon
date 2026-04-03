"""Application configuration."""
import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://retv_user:retv_secret@localhost:5432/retv"
    )
    
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
            url = "postgresql+asyncpg://" + url.split("://", 1)[1] if "://" in url else url
        return url
    
    # JWT
    jwt_secret: str = os.getenv("JWT_SECRET", "change-me-in-production")
    jwt_algorithm: str = "HS256"
    jwt_expiry_days: int = 30
    
    # OAuth
    google_client_id: str = os.getenv("GOOGLE_CLIENT_ID", "")
    apple_client_id: str = os.getenv("APPLE_CLIENT_ID", "")
    
    # WebAuthn (Passkeys)
    webauthn_rp_id: str = os.getenv("WEBAUTHN_RP_ID", "localhost")
    webauthn_rp_name: str = os.getenv("WEBAUTHN_RP_NAME", "Adajoon")
    webauthn_origin: str = os.getenv("WEBAUTHN_ORIGIN", "http://localhost:5173")
    
    # API Keys
    sync_api_key: str = os.getenv("SYNC_API_KEY", "")
    
    # External APIs
    iptv_api_base: str = "https://iptv-org.github.io/api"
    iptv_github_url: str = "https://raw.githubusercontent.com/iptv-org/iptv/master/streams.json"
    radio_browser_api: str = "https://de1.api.radio-browser.info"
    
    # Redis
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Stripe
    stripe_secret_key: str = os.getenv("STRIPE_SECRET_KEY", "")
    stripe_webhook_secret: str = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    stripe_publishable_key: str = os.getenv("STRIPE_PUBLISHABLE_KEY", "")
    
    # CORS
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "https://adajoon.com",
        "https://www.adajoon.com",
    ]
    
    class Config:
        env_file = ".env"


settings = Settings()
