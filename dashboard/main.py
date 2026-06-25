"""Point d'entrée du dashboard ObRail.

MVP : application Dash minimale (« Hello World »).
L'objet `server` est exposé pour être servi par gunicorn en production.
"""

import os

from dash import Dash, html

API_URL = os.environ.get("API_URL", "http://localhost:8000")

app = Dash(__name__, title="ObRail - Dashboard")
server = app.server  # exposé pour gunicorn (gunicorn main:server)

app.layout = html.Div(
    [
        html.H1("ObRail - Dashboard"),
        html.P("Hello World."),
        html.Small(f"API cible : {API_URL}"),
    ]
)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8050, debug=True)
