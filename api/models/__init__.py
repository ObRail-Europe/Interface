"""Modèles ORM ObRail. Importer ce package enregistre les tables sur `Base.metadata`."""

from models.base import Base
from models.ville import Ville

__all__ = ["Base", "Ville"]
