"""Point d'entrée du dashboard ObRail (Dash).

`create_app()` assemble la fabrique (client API injecté, onglets, callbacks).
`server` est exposé pour gunicorn (`gunicorn main:server`).
"""

from dash import Dash, dcc, html

from api.client import HttpOverviewClient
from config import settings
from pages import overview


def create_app() -> Dash:
    app = Dash(__name__, title="ObRail — Dashboard")
    client = HttpOverviewClient(settings.api_url)

    app.layout = html.Div(
        className="app",
        children=[
            html.H1("ObRail — Observatoire ferroviaire"),
            dcc.Tabs(
                id="tabs",
                value="overview",
                children=[
                    dcc.Tab(label="Vue d'ensemble", value="overview", children=overview.layout()),
                ],
            ),
        ],
    )
    overview.register_callbacks(app, client)
    return app


app = create_app()
server = app.server  # exposé pour gunicorn

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8050, debug=True)
