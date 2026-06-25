"""Initialise le schéma PostgreSQL : crée les tables ORM.

Usage (base lancée via docker compose) :  uv run python init_db.py
"""

from database import init_db

if __name__ == "__main__":
    init_db()
    print("Schéma initialisé : tables ORM créées.")
