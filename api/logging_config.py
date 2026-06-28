"""Politique de logs de l'API : journalisation structurée (JSON) sur stdout.

Le format JSON est directement exploitable par Loki/Grafana (parsing des champs
`level`, `logger`, `method`, `path`, `status`, `duration_ms`…). La sortie stdout est
collectée par Promtail depuis les logs du conteneur - aucune écriture de fichier.
"""

import json
import logging
import sys
from datetime import UTC, datetime

# Attributs « extra » conservés dans la sortie JSON (contexte requête).
_EXTRA_FIELDS = ("method", "path", "status", "duration_ms", "code")


class JsonFormatter(logging.Formatter):
    """Formate chaque enregistrement en une ligne JSON (logfmt-friendly)."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        for field in _EXTRA_FIELDS:
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging(level: str = "INFO") -> None:
    """Configure le logger racine (handler stdout + format JSON), idempotent."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level.upper())

    # Uvicorn : on évite le double-log des accès (notre middleware s'en charge).
    logging.getLogger("uvicorn.access").disabled = True
    for name in ("uvicorn", "uvicorn.error"):
        uv_logger = logging.getLogger(name)
        uv_logger.handlers.clear()
        uv_logger.propagate = True
