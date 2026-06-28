"""Tests d'intégration des endpoints qualité (API + base seed)."""

from fastapi.testclient import TestClient


def test_completude_endpoint_trajets(client: TestClient) -> None:
    data = client.get("/api/v1/qualite/completude?table=trajets").json()
    assert data["table"] == "trajets"
    assert data["nb_lignes"] == 15  # 15 trajets du seed
    by_col = {c["nom"]: c for c in data["colonnes"]}
    assert by_col["id"]["taux_complet"] == 1.0  # clé primaire complète
    # 11 arrivées résolues / 15 -> 4 NULLs.
    assert by_col["arrival_citycode"]["nb_nuls"] == 4


def test_completude_endpoint_rejects_unknown_table(client: TestClient) -> None:
    assert client.get("/api/v1/qualite/completude?table=operateurs").status_code == 422


def test_anomalies_endpoint(client: TestClient) -> None:
    anomalies = {a["type"]: a for a in client.get("/api/v1/qualite/anomalies").json()["anomalies"]}
    assert anomalies["arrivee_non_resolue"]["nb"] == 4
    assert anomalies["cluster_non_rattache"]["nb"] == 1  # « Nulle Part »
    assert anomalies["ville_sans_coordonnees"]["severite"] == "error"


def test_volumetrie_endpoint(client: TestClient) -> None:
    sources = client.get("/api/v1/qualite/volumetrie").json()["sources"]
    assert sum(s["nb"] for s in sources) == 15  # total trajets du seed
    assert sources[0]["cle"] == "SNCF"  # source la plus fréquente (11 trajets)
    assert sources[0]["nb"] == 11
