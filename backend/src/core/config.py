"""Application configuration using pydantic-settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = "StockValuator"
    debug: bool = False
    cors_origins: str = "http://localhost:3000"  # Comma separated list

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/stockvaluator"

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    cache_ttl_seconds: int = 300  # 5 minutes for stock prices

    # JWT
    secret_key: str = "development-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24 hours

    # Google OAuth (shared for login and Gmail API)
    google_client_id: str = ""
    google_client_secret: str = ""

    # Celery (uses existing Redis URL as broker)
    celery_broker_url: str = ""  # Defaults to redis_url if empty

    # Gmail API OAuth 2.0 (uses GOOGLE_CLIENT_ID/SECRET above)
    gmail_redirect_uri: str = "http://localhost:8000/email/oauth/callback"
    gmail_refresh_token: str = ""  # Stored after initial authorization
    gmail_user_email: str = ""  # Email to send from
    
    # SMTP fallback (used if Gmail API not configured)
    mail_server: str = ""
    mail_port: int = 587
    mail_username: str = ""
    mail_password: str = ""
    mail_from: str = ""
    mail_from_name: str = "StockValuator"
    mail_starttls: bool = True
    mail_ssl_tls: bool = False

    @property
    def celery_broker(self) -> str:
        """Get Celery broker URL, defaulting to Redis URL."""
        return self.celery_broker_url or self.redis_url


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
