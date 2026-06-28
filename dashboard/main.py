"""Point d'entrée du dashboard ObRail (Dash).

`create_app()` assemble la fabrique (clients API injectés, onglets, callbacks).
`server` est exposé pour gunicorn (`gunicorn main:server`).
"""

from dash import Dash, dcc, html

from api.carbon_client import HttpCarbonClient
from api.cluster_client import HttpClusterClient
from api.explorer_client import HttpExplorerClient
from api.overview_client import HttpOverviewClient
from api.qualite_client import HttpQualiteClient
from api.supervision_client import HttpSupervisionClient
from api.territoire_client import HttpTerritoireClient
from config import settings
from logging_config import configure_logging
from pages import carbon, explorer, fragilite, overview, qualite, supervision, territoires


def create_app() -> Dash:
    # suppress_callback_exceptions : les composants d'un onglet ne sont dans le DOM
    # que lorsqu'il est ouvert (callbacks par onglet déclenchés à l'ouverture).
    configure_logging(settings.log_level)
    app = Dash(__name__, title="ObRail — Dashboard", suppress_callback_exceptions=True)

    overview_client = HttpOverviewClient(settings.api_url)
    explorer_client = HttpExplorerClient(settings.api_url)
    carbon_client = HttpCarbonClient(settings.api_url)
    territoire_client = HttpTerritoireClient(settings.api_url)
    cluster_client = HttpClusterClient(settings.api_url)
    qualite_client = HttpQualiteClient(settings.api_url)
    supervision_client = HttpSupervisionClient(settings.api_url)

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
                    dcc.Tab(
                        label="Territoires & couverture",
                        value="territoires",
                        children=territoires.layout(),
                    ),
                    dcc.Tab(
                        label="Fragilité territoriale",
                        value="fragilite",
                        children=fragilite.layout(),
                    ),
                    dcc.Tab(
                        label="Qualité des données",
                        value="qualite",
                        children=qualite.layout(),
                    ),
                    dcc.Tab(
                        label="Supervision",
                        value="supervision",
                        children=supervision.layout(),
                    ),
                ],
            ),
        ],
    )
    overview.register_callbacks(app, overview_client)
    explorer.register_callbacks(app, explorer_client)
    carbon.register_callbacks(app, carbon_client)
    territoires.register_callbacks(app, territoire_client)
    fragilite.register_callbacks(app, cluster_client)
    qualite.register_callbacks(app, qualite_client)
    supervision.register_callbacks(app, supervision_client)
    return app


app = create_app()
server = app.server  # exposé pour gunicorn

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8050, debug=True)
