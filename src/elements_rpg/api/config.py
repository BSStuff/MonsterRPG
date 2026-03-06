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
        ELEMENTS_DATABASE_URL=postgresql+asyncpg://postgres:[password]@[host]:5432/postgres
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
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8080", "http://localhost:5500"]

    # Database
    database_url: str = ""

    # Supabase
    supabase_url: str = ""
    supabase_key: str = ""  # anon key (public, client-side safe)
    supabase_service_key: str = ""  # service_role key (secret, backend only)
    supabase_jwt_secret: str = ""

    # Server
    port: int = 8000

    def validate_required_for_production(self) -> list[str]:
        """Return list of missing required settings.

        Returns:
            List of environment variable names that are empty but required.
        """
        missing: list[str] = []
        if not self.supabase_jwt_secret:
            missing.append("ELEMENTS_SUPABASE_JWT_SECRET")
        if not self.database_url:
            missing.append("ELEMENTS_DATABASE_URL")
        if not self.supabase_url:
            missing.append("ELEMENTS_SUPABASE_URL")
        return missing


@lru_cache
def get_settings() -> Settings:
    """Return cached Settings instance. Call once at startup; cached thereafter."""
    return Settings()
