"""Base déclarative commune à tous les modèles ORM."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Classe de base ORM : porte les métadonnées partagées (création des tables)."""
