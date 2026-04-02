"""Quart application factory for the ZHVI dashboard."""

from pathlib import Path
from typing import Optional

from quart import Quart

from .charts import ChartService
from .data import DataStore
from .routes import register_routes
from .settings import Settings, load_settings


BASE_DIR = Path(__file__).resolve().parent.parent


def create_app(settings: Optional[Settings] = None) -> Quart:
    """Create and configure the Quart app.

    A small factory keeps global state out of import time and makes the
    application easier to test or extend (e.g., swapping data sources or
    injecting alternative settings).
    """

    settings = settings or load_settings(base_dir=BASE_DIR)

    app = Quart(
        __name__,
        template_folder=str(BASE_DIR / "templates"),
        static_folder=str(BASE_DIR / "static"),
    )

    store = DataStore(settings)
    charts = ChartService(store, settings)

    register_routes(app, store, charts, settings)

    return app


# Default application instance for Hypercorn / scripts
app = create_app()

