from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://retv:retv_secret@db:5432/retv"
    sync_database_url: str = "postgresql://retv:retv_secret@db:5432/retv"
    iptv_api_base: str = "https://iptv-org.github.io/api"
    refresh_interval_hours: int = 6
    port: int = 8000

    class Config:
        env_file = ".env"

    def get_async_url(self) -> str:
        url = self.database_url
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url


settings = Settings()
