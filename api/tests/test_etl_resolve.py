"""Test d'intégration de la résolution des jointures inter-sources (etl/resolve.py)."""

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from etl.resolve import resolve_clusters, resolve_trajets
from models import Cluster, Trajet, Ville


def test_resolution_inter_sources(session: Session) -> None:
    # Isolation : jeu de villes maîtrisé (le TRUNCATE et les inserts sont rollback en fin de test).
    session.execute(text("TRUNCATE villes, clusters, trajets CASCADE"))
    session.add_all(
        [
            Ville(citycode="75056", city_name="Paris", has_gare=True,
                  population_insee=2_103_778, lat_insee=48.8566, lon_insee=2.3522),
            Ville(citycode="69123", city_name="Lyon", has_gare=True,
                  population_insee=500_000, lat_insee=45.75, lon_insee=4.85),
            Ville(citycode="11001", city_name="Sainte-Marie", has_gare=False,
                  population_insee=500, lat_insee=43.0, lon_insee=2.0),
            Ville(citycode="97418", city_name="Sainte-Marie", has_gare=True,
                  population_insee=9000, lat_insee=-20.9, lon_insee=55.5),
        ]
    )  # fmt: skip
    session.add_all(
        [
            Cluster(row_id=1, city_name="Paris", cluster=0, lat_insee=48.8566, lon_insee=2.3522),
            Cluster(row_id=2, city_name="Nulle Part", cluster=1, lat_insee=10.0, lon_insee=10.0),
        ]
    )
    session.add_all(
        [
            Trajet(departure_city="Lyon", departure_country="FR",
                   arrival_city="Paris", arrival_country="FR"),
            Trajet(departure_city="lyon", departure_country="FR"),            # casse/accents
            Trajet(departure_city="Paris 09 Opera", departure_country="FR"),  # alias préfixe
            Trajet(departure_city="Sainte-Marie", departure_country="FR"),    # homonyme
            Trajet(departure_city="Sankt Gallen", departure_country="FR"),    # hors référentiel
        ]
    )  # fmt: skip
    session.flush()

    assert resolve_clusters(session) == 1  # seul le cluster aux coords de Paris matche
    resolve_trajets(session)
    session.expire_all()

    assert session.get(Cluster, 1).citycode == "75056"  # rattachement par coordonnées
    assert session.get(Cluster, 2).citycode is None  # aucune coordonnée correspondante

    by_city = {t.departure_city: t for t in session.execute(select(Trajet)).scalars()}
    assert by_city["Lyon"].departure_citycode == "69123"  # correspondance exacte
    assert by_city["Lyon"].arrival_citycode == "75056"  # arrivée résolue aussi
    assert by_city["lyon"].departure_citycode == "69123"  # insensible casse/accents
    assert by_city["Paris 09 Opera"].departure_citycode == "75056"  # alias préfixe
    assert by_city["Sainte-Marie"].departure_citycode == "97418"  # homonyme : has_gare l'emporte
    assert by_city["Sankt Gallen"].departure_citycode is None  # hors référentiel villes
