"""Configuration centralisée de l'API, chargée depuis l'environnement (.env)."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Paramètres applicatifs. Surchargeables par variables d'environnement."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Valeur par défaut = dev local.
    database_url: str = "postgresql+psycopg://obrail:obrail@localhost:5432/obrail"

    api_title: str = "ObRail API"
    api_version: str = "0.0.0"


settings = Settings()
