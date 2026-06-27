"""Point d'entrée du dashboard ObRail (Dash).

`create_app()` assemble la fabrique (clients API injectés, onglets, callbacks).
`server` est exposé pour gunicorn (`gunicorn main:server`).
"""

from dash import Dash, dcc, html

from api.carbon_client import HttpCarbonClient
from api.explorer_client import HttpExplorerClient
from api.overview_client import HttpOverviewClient
from config import settings
from pages import carbon, explorer, overview


def create_app() -> Dash:
    # suppress_callback_exceptions : les composants d'un onglet ne sont dans le DOM
    # que lorsqu'il est ouvert (callbacks par onglet déclenchés à l'ouverture).
    app = Dash(__name__, title="ObRail — Dashboard", suppress_callback_exceptions=True)

    overview_client = HttpOverviewClient(settings.api_url)
    explorer_client = HttpExplorerClient(settings.api_url)
    carbon_client = HttpCarbonClient(settings.api_url)

    app.layout = html.Div(
        className="app",
        children=[
            html.H1("ObRail — Observatoire ferroviaire"),
            dcc.Tabs(
                id="tabs",
                value="overview",
                children=[
                    dcc.Tab(label="Vue d'ensemble", value="overview", children=overview.layout()),
                    dcc.Tab(
                        label="Explorateur de trajets",
                        value="explorer",
                        children=explorer.layout(),
                    ),
                    dcc.Tab(
                        label="Empreinte carbone",
                        value="carbon",
                        children=carbon.layout(),
                    ),
                ],
            ),
        ],
    )
    overview.register_callbacks(app, overview_client)
    explorer.register_callbacks(app, explorer_client)
    carbon.register_callbacks(app, carbon_client)
    return app


app = create_app()
server = app.server  # exposé pour gunicorn

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8050, debug=True)
