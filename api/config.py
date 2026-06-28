"""Configuration centralisée de l'API, chargée depuis l'environnement (.env)."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_DEFAULT_MODEL_DIR = str(Path(__file__).resolve().parents[1] / "data")


class Settings(BaseSettings):
    """Paramètres applicatifs. Surchargeables par variables d'environnement."""

    # protected_namespaces= : autorise un champ `model_dir` (sinon collision Pydantic).
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", protected_namespaces=())

    # Valeur par défaut = dev local.
    database_url: str = "postgresql+psycopg://obrail:obrail@localhost:5432/obrail"

    api_title: str = "ObRail API"
    api_version: str = "0.0.0"

    # Niveau de log (DEBUG, INFO, WARNING, ERROR) — politique de logs (supervision V9).
    log_level: str = "INFO"

    model_dir: str = _DEFAULT_MODEL_DIR


settings = Settings()
