"""Tests des composants de l'onglet Qualité (fonctions pures, sans API)."""

from components.charts import anomalies_bars, completude_bars, volumetrie_bars

_COMPLETUDE = {
    "table": "trajets",
    "nb_lignes": 15,
    "colonnes": [
        {"nom": "arrival_citycode", "taux_complet": 0.73, "nb_nuls": 4},
        {"nom": "id", "taux_complet": 1.0, "nb_nuls": 0},
    ],
}


def test_completude_bars_worst_on_top_in_percent() -> None:
    fig = completude_bars(_COMPLETUDE)
    bar = fig.data[0]
    assert bar.orientation == "h"
    # Données triées NULLs décroissants ; on inverse → la plus lacunaire en haut (dernière).
    assert bar.y[-1] == "arrival_citycode"
    assert list(bar.x) == [100.0, 73.0]  # taux en %


_ANOMALIES = {
    "anomalies": [
        {
            "type": "arrivee_non_resolue",
            "libelle": "Arrivées non résolues",
            "nb": 4,
            "severite": "warn",
        },
        {
            "type": "ville_sans_coord",
            "libelle": "Villes sans coordonnées",
            "nb": 0,
            "severite": "error",
        },
    ]
}


def test_anomalies_bars_colored_by_severity() -> None:
    fig = anomalies_bars(_ANOMALIES)
    bar = fig.data[0]
    # warn = ambre, error = rouge ; ordre inversé pour l'affichage horizontal.
    assert list(bar.marker.color) == ["#c0392b", "#e8a33d"]


_VOLUMETRIE = {"sources": [{"cle": "SNCF", "nb": 11}, {"cle": "DB", "nb": 1}]}


def test_volumetrie_bars_largest_on_top() -> None:
    fig = volumetrie_bars(_VOLUMETRIE)
    bar = fig.data[0]
    assert bar.y[-1] == "SNCF"  # plus gros volume en haut
    assert list(bar.x) == [1, 11]


def test_volumetrie_bars_respects_limit() -> None:
    many = {"sources": [{"cle": f"S{i}", "nb": 100 - i} for i in range(30)]}
    assert len(volumetrie_bars(many, limit=5).data[0].y) == 5
