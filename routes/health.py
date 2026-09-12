"""Health-check routes for the Walmart to SHV load automation app."""

import logging

from flask import Blueprint, jsonify

health_blueprint = Blueprint("health", __name__)


@health_blueprint.get("/health")
def health():
    """Return a JSON health response for local and deployment checks."""
    logging.info("Health check requested")
    return jsonify({"status": "ok"})