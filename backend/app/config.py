from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://retv:retv_secret@db:5432/retv"
    sync_database_url: str = "postgresql://retv:retv_secret@db:5432/retv"
    iptv_api_base: str = "https://iptv-org.github.io/api"
    refresh_interval_hours: int = 6
    port: int = 8000

    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_timeout: int = 30

    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiry_days: int = 30
    google_client_id: str = ""
    google_client_secret: str = ""
    apple_client_id: str = ""
    webauthn_rp_id: str = "adajoon.com"
    webauthn_rp_name: str = "Adajoon"
    webauthn_origin: str = "https://adajoon.com"

    cors_origins: str = "https://adajoon.com,https://www.adajoon.com"

    class Config:
        env_file = ".env"

    def get_async_url(self) -> str:
        url = self.database_url
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url

    @property
    def cors_origins_list(self) -> list[str]:
        if self.cors_origins == "*":
            return ["*"]
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
