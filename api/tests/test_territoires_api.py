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
