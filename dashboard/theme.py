"""Tokens de couleurs data-viz (cohérents avec assets/theme.css)."""

COLOR_JOUR = "#e8a33d"  # trains de jour
COLOR_NUIT = "#3b4cc0"  # trains de nuit

# Onglet « Empreinte carbone » : train (marron moderne) vs avion (bleu ciel doux).
COLOR_TRAIN = "#8c5e3c"
COLOR_AVION = "#7ec0ee"

# Onglet « Fragilité » : palette qualitative daltonisme-safe (Okabe–Ito) pour les clusters.
COLOR_CLUSTERS = (
    "#0072b2",
    "#e69f00",
    "#009e73",
    "#d55e00",
    "#cc79a7",
    "#56b4e9",
    "#f0e442",
    "#999999",
)

# Échelle séquentielle de la fragilité (clair/vert → foncé/rouge).
COLOR_FRAGILITE = {
    "Faible": "#2e8b57",
    "Faible-modérée": "#9acd32",
    "Modérée": "#e8a33d",
    "Modérée-élevée": "#e67e22",
    "Élevée": "#c0392b",
}
