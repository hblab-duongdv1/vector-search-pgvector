"""Core: application settings."""
from src.core.config import Settings


def test_cors_origins_wildcard() -> None:
    settings = Settings(database_url="postgresql://u:p@localhost/db", cors_origins="*")
    assert settings.cors_origins_list == ["*"]


def test_cors_origins_comma_separated() -> None:
    settings = Settings(
        database_url="postgresql://u:p@localhost/db",
        cors_origins="http://a.com, http://b.com",
    )
    assert settings.cors_origins_list == ["http://a.com", "http://b.com"]


def test_is_production() -> None:
    dev = Settings(database_url="postgresql://u:p@localhost/db", app_env="development")
    prod = Settings(database_url="postgresql://u:p@localhost/db", app_env="production")
    assert dev.is_production is False
    assert prod.is_production is True
