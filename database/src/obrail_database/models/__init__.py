"""Modèles ORM ObRail. Importer ce package enregistre les tables sur `Base.metadata`."""

from obrail_database.models.base import Base
from obrail_database.models.cluster import Cluster
from obrail_database.models.trajet import Trajet
from obrail_database.models.ville import Ville

__all__ = ["Base", "Cluster", "Trajet", "Ville"]
