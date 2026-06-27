"""Tests d'intégration des endpoints territoires (API + base seed)."""

from fastapi.testclient import TestClient

_CARTE = "/api/v1/villes/carte"


def test_carte_endpoint_default_dimension(client: TestClient) -> None:
    data = client.get(_CARTE).json()
    assert len(data) == 12  # 12 communes géolocalisées du seed
    paris = next(v for v in data if v["citycode"] == "75056")
    assert paris["geo"]["lat"] == 48.8566
    assert paris["valeur"] == 331694  # dimension par défaut : nb_trajets_total
    assert paris["has_gare"] is True


def test_carte_endpoint_filters_by_dept(client: TestClient) -> None:
    data = client.get(f"{_CARTE}?code_dept=75").json()
    assert {v["city_name"] for v in data} == {"Paris"}


def test_carte_endpoint_dimension_has_gare(client: TestClient) -> None:
    data = client.get(f"{_CARTE}?dimension=has_gare").json()
    assert all(v["valeur"] == 1.0 for v in data)  # toutes les communes du seed ont une gare


def test_carte_endpoint_rejects_unknown_dimension(client: TestClient) -> None:
    assert client.get(f"{_CARTE}?dimension=revenu_median_uc").status_code == 422


_COUVERTURE = "/api/v1/stats/couverture"


def test_couverture_endpoint_by_dept(client: TestClient) -> None:
    data = client.get(f"{_COUVERTURE}?by=code_dept").json()
    assert data["by"] == "code_dept"
    mailles = {m["cle"]: m for m in data["mailles"]}
    # Dépt 95 : Ermont + Pontoise (2 communes) ; toutes deux avec gare dans le seed.
    assert mailles["95"]["nb_communes"] == 2
    assert mailles["95"]["taux_avec_gare"] == 1.0
    assert mailles["75"]["nb_trajets_total"] == 331694
    # Trié par desserte décroissante.
    totaux = [m["nb_trajets_total"] for m in data["mailles"]]
    assert totaux == sorted(totaux, reverse=True)


def test_couverture_endpoint_by_region(client: TestClient) -> None:
    data = client.get(f"{_COUVERTURE}?by=code_region").json()
    assert data["by"] == "code_region"
    # Région 11 (Île-de-France) : Paris, Bretigny, Ablon, Ermont, Pontoise = 5 communes.
    idf = next(m for m in data["mailles"] if m["cle"] == "11")
    assert idf["nb_communes"] == 5


def test_couverture_endpoint_rejects_unknown_maille(client: TestClient) -> None:
    assert client.get(f"{_COUVERTURE}?by=code_commune").status_code == 422


_AMPLITUDE = "/api/v1/stats/amplitude"


def test_amplitude_endpoint(client: TestClient) -> None:
    data = client.get(_AMPLITUDE).json()
    assert data["bin_h"] == 1.0
    # 12 communes du seed ont une amplitude renseignée.
    assert sum(b["nb_communes"] for b in data["bins"]) == 12
    # 5 communes desservies après minuit / 12.
    assert abs(data["part_apres_minuit"] - 5 / 12) < 1e-6
    mins = [b["min_h"] for b in data["bins"]]
    assert mins == sorted(mins)  # bins ordonnés


def test_amplitude_endpoint_rejects_out_of_range_bin(client: TestClient) -> None:
    assert client.get(f"{_AMPLITUDE}?bin_h=0").status_code == 422
