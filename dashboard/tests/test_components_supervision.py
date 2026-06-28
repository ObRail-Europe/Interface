"""Tests des composants de l'onglet Supervision (fonctions pures, sans API)."""

from components.supervision import health_badges


def test_health_badges_one_card_per_service_with_status() -> None:
    band = health_badges(
        {
            "services": [
                {"nom": "api", "statut": "up", "latence_ms": 0.0},
                {"nom": "database", "statut": "down", "latence_ms": 12.3},
            ]
        }
    )
    assert len(band.children) == 2
    text = str(band)
    assert "UP" in text and "DOWN" in text
    assert "database" in text


def test_health_badges_empty_does_not_crash() -> None:
    assert health_badges({"services": []}).children == []
    assert health_badges({}).children == []
