"""Configuration du module base de données (autonome, chargée depuis l'environnement)."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Paramètres de connexion. Surchargeables par variables d'environnement."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Valeur par défaut = dev local.
    database_url: str = "postgresql+psycopg://obrail:obrail@localhost:5432/obrail"

    # Niveau de log des outils CLI (ETL, init_db).
    log_level: str = "INFO"


settings = Settings()
