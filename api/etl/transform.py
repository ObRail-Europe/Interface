"""Conversion des valeurs CSV (texte) vers des types Python, selon le modèle ORM.

Gère les particularités des sources : booléens au format `1.0`/`True`, entiers au
format `3.0`, dates GTFS `YYYYMMDD`, champs vides → `None`.
"""

from datetime import date, datetime
from typing import Any

from sqlalchemy import Boolean, Date, Float, Integer
from sqlalchemy.types import TypeEngine

# Valeurs textuelles interprétées comme « vrai ».
_TRUE = {"true", "t", "1", "1.0", "yes", "vrai"}


def cast_value(value: Any, coltype: TypeEngine) -> Any:
    """Convertit une valeur CSV vers le type Python correspondant à la colonne."""
    if value is None:
        return None
    v = value.strip() if isinstance(value, str) else value
    if v == "":
        return None
    if isinstance(coltype, Boolean):
        return str(v).strip().lower() in _TRUE
    if isinstance(coltype, Integer):  # BigInteger / SmallInteger en héritent
        return int(float(v))
    if isinstance(coltype, Float):
        return float(v)
    if isinstance(coltype, Date):
        s = str(v).strip()
        if len(s) == 8 and s.isdigit():  # format GTFS YYYYMMDD
            return datetime.strptime(s, "%Y%m%d").date()
        return date.fromisoformat(s)
    return str(v)


def row_to_mapping(row: dict[str, str], model: type) -> dict[str, Any]:
    """Ligne CSV → dict typé, pour les colonnes du modèle présentes dans la source."""
    return {
        col.name: cast_value(row[col.name], col.type)
        for col in model.__table__.columns
        if col.name in row
    }
