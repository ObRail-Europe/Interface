"""Tests d'intégration des endpoints fragilité (API + base seed)."""

from fastapi.testclient import TestClient


def test_clusters_carte_endpoint(client: TestClient) -> None:
    data = client.get("/api/v1/clusters/carte").json()
    assert len(data) == 8  # 8 communes du seed clusters (toutes géolocalisées)
    paris = next(c for c in data if c["city_name"] == "Paris")
    assert paris["cluster"] == 0
    assert paris["niveau_fragilite"] is not None
    assert paris["geo"]["lat"] == 48.8566


def test_clusters_carte_filters_has_gare(client: TestClient) -> None:
    sans_gare = client.get("/api/v1/clusters/carte?has_gare=false").json()
    assert {c["city_name"] for c in sans_gare} == {"Nulle Part"}


def test_clusters_endpoint_effectifs(client: TestClient) -> None:
    data = client.get("/api/v1/clusters").json()
    by_cluster = {c["cluster"]: c for c in data}
    assert set(by_cluster) == {0, 1, 2}
    assert by_cluster[0]["effectif"] == 6  # 6 communes en cluster 0
    assert by_cluster[0]["niveau_fragilite"] == "Faible"  # niveau le plus fréquent
    assert data[0]["cluster"] == 0  # trié par effectif décroissant


def test_clusters_profils_endpoint(client: TestClient) -> None:
    data = client.get("/api/v1/clusters/profils").json()
    assert {p["cluster"] for p in data} == {0, 1, 2}
    cluster0 = next(p for p in data if p["cluster"] == 0)
    feature_names = {f["nom"] for f in cluster0["features"]}
    assert "revenu_median_uc" in feature_names
    # Chamonix (cluster 2) a le revenu moyen le plus élevé -> normalisé à 1.
    cluster2 = next(p for p in data if p["cluster"] == 2)
    revenu2 = next(f for f in cluster2["features"] if f["nom"] == "revenu_median_uc")
    assert revenu2["moyenne_normalisee"] == 1.0


def test_fragilite_repartition_by_region(client: TestClient) -> None:
    data = client.get("/api/v1/stats/fragilite?by=code_region").json()
    assert data["by"] == "code_region"
    by_cle = {m["cle"]: m for m in data["mailles"]}
    # Région 84 : Lyon (Faible) + Chamonix (Faible-modérée) = 2 communes.
    assert sum(n["nb"] for n in by_cle["84"]["repartition"]) == 2
    # Région 11 : Paris en « Élevée ».
    assert any(n["niveau"] == "Élevée" for n in by_cle["11"]["repartition"])


def test_fragilite_repartition_rejects_unknown_maille(client: TestClient) -> None:
    assert client.get("/api/v1/stats/fragilite?by=code_commune").status_code == 422
