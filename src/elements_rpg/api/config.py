"""API configuration via pydantic-settings — loads from environment variables and .env file."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables with ELEMENTS_ prefix.

    Example .env file:
        ELEMENTS_DEBUG=true
        ELEMENTS_CORS_ORIGINS=["http://localhost:3000","https://my-app.vercel.app"]
        ELEMENTS_SUPABASE_URL=https://xxx.supabase.co
        ELEMENTS_SUPABASE_KEY=eyJ...
        ELEMENTS_PORT=8000
    """

    model_config = SettingsConfigDict(
        env_prefix="ELEMENTS_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = "ElementsRPG"
    app_version: str = "0.2.0"
    debug: bool = False

    # CORS
    cors_origins: list[str] = ["http://localhost:*"]

    # Supabase
    supabase_url: str = ""
    supabase_key: str = ""  # anon key (public, client-side safe)
    supabase_service_key: str = ""  # service_role key (secret, backend only)
    supabase_jwt_secret: str = ""

    # Server
    port: int = 8000


@lru_cache
def get_settings() -> Settings:
    """Return cached Settings instance. Call once at startup; cached thereafter."""
    return Settings()
