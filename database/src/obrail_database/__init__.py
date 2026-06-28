"""Couche base de données ObRail Europe.

Module autonome regroupant la **gestion de PostgreSQL** : modèles ORM, migrations
Alembic, vues matérialisées et ETL d'ingestion des CSV. Consommé par l'API (modèles)
et déployable seul (image Docker provisionnant le schéma).
"""
