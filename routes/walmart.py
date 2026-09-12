"""Walmart integration route for retrieving open freight tenders."""

import logging

import requests
from flask import Blueprint, current_app, jsonify

walmart_blueprint = Blueprint("walmart", __name__, url_prefix="/api/walmart")


@walmart_blueprint.get("/loads")
def loads():
    """Return all open Walmart freight tenders as JSON."""
    integration = current_app.config["APP_CONSTANTS"]["integration"]
    logging.info("Fetching Walmart freight tenders")

    try:
        response = requests.get(
            integration["walmart_loads_url"],
            headers={"Authorization": f"Bearer {integration['account_email']}"},
            timeout=integration["request_timeout_seconds"],
        )
        response.raise_for_status()
        logging.info("Fetched Walmart freight tenders")
        return jsonify(response.json())
    except requests.HTTPError as error:
        status_code = error.response.status_code if error.response else 502
        logging.error("Walmart API returned HTTP status %s", status_code)
        return jsonify({"status": "error", "message": "Walmart API request failed"}), status_code
    except (requests.RequestException, ValueError):
        logging.error("Walmart API request failed or returned invalid JSON")
        return jsonify({"status": "error", "message": "Unable to fetch Walmart loads"}), 502