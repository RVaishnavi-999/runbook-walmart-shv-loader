"""Flask application entry point for the Walmart to SHV load automation app."""

import json
import logging
from pathlib import Path

from flask import Flask, render_template

from routes.health import health_blueprint
from routes.shv import shv_blueprint
from routes.walmart import walmart_blueprint

BASE_DIR = Path(__file__).resolve().parent


def load_constants() -> dict:
    """Load application values from the shared JSON configuration."""
    logging.info("Loading application constants")
    constants_path = BASE_DIR / "constants.json"
    with constants_path.open(encoding="utf-8") as constants_file:
        constants = json.load(constants_file)
    logging.info("Application constants loaded")
    return constants


def create_app() -> Flask:
    """Create and configure the Flask application."""
    logging.info("Creating Flask application")
    application = Flask(__name__)
    # Preserve dict insertion order in JSON responses (Flask sorts keys alphabetically by default).
    application.json.sort_keys = False  # type: ignore[attr-defined]
    application.config["APP_CONSTANTS"] = load_constants()

    @application.get("/")
    def index():
        """Render the initial operations page."""
        logging.info("Rendering operations page")
        constants = application.config["APP_CONSTANTS"]
        # Never send account email or API URLs to the browser.
        public_constants = {key: value for key, value in constants.items() if key != "integration"}
        return render_template("index.html", constants=public_constants)

    application.register_blueprint(health_blueprint)
    application.register_blueprint(shv_blueprint)
    application.register_blueprint(walmart_blueprint)

    logging.info("Flask application created")
    return application


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
