"""Tests smoke du dashboard Dash"""

from main import app, server


def test_layout_is_not_empty() -> None:
    assert app.layout is not None
    assert app.layout.children  # le Div racine contient des éléments


def test_flask_server_is_exposed_for_gunicorn() -> None:
    assert server is app.server
