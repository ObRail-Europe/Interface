"""Exceptions métier de l'API.

Elles portent un `status_code` HTTP et un `code` machine stable, ce qui permet un
suivi précis (logs + réponses normalisées `ApiError`) et un mapping HTTP propre.
"""


class ObRailError(Exception):
    """Erreur métier : statut HTTP + code stable + message destiné au client."""

    status_code = 500
    code = "obrail_error"

    def __init__(
        self, detail: str, *, status_code: int | None = None, code: str | None = None
    ) -> None:
        super().__init__(detail)
        self.detail = detail
        if status_code is not None:
            self.status_code = status_code
        if code is not None:
            self.code = code


class ModelUnavailableError(ObRailError):
    """Le modèle de fragilité (artefacts .joblib) n'est pas disponible."""

    status_code = 503
    code = "model_unavailable"
