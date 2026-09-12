"""SHV integration route for sanitizing and pushing Walmart loads."""

import logging
import re

import requests
from flask import Blueprint, current_app, jsonify, request

shv_blueprint = Blueprint("shv", __name__, url_prefix="/api/shv")


def convert_date(value: str) -> str:
    """Convert a Walmart MMDDYYYY date to the SHV DDMMYYYY format."""
    digits = re.sub(r"[^0-9]", "", str(value))
    if len(digits) != 8:
        raise ValueError("Date must contain eight digits")
    return f"{digits[2:4]}{digits[0:2]}{digits[4:8]}"


def clean_weight(value: str) -> int:
    """Convert a displayed Walmart weight into a whole-pound number."""
    digits = re.sub(r"[^0-9]", "", str(value))
    if not digits:
        raise ValueError("Weight must contain a numeric value")
    return int(digits)


def sanitize_load(load: dict, constants: dict) -> dict:
    """Map one Walmart record to the SHV load payload."""
    mode = str(load.get("mode", "")).strip().upper()
    equipment = constants["mode_mapping"].get(mode, constants["mode_mapping"]["unmapped"])
    return {
        "load_number": str(load["load_no"]).strip(),
        "bol_number": str(load["frt_ord_no"]).strip(),
        "shipper_name": str(load["shipper_nm"]).strip(),
        "origin_city": str(load["orig_city"]).strip(),
        "origin_state": str(load["orig_st"]).strip(),
        "destination_city": str(load["dest_city"]).strip(),
        "destination_state": str(load["dest_st"]).strip(),
        "ship_date": convert_date(load["shp_dt"]),
        "delivery_date": convert_date(load["del_dt"]),
        "weight": clean_weight(load["wgt"]),
        "equipment_type": equipment,
    }


def build_push_results(sanitized_loads: list, response_body: dict) -> list:
    """Pair each sanitized payload with its accepted/rejected SHV outcome for display."""
    accepted = set(response_body.get("accepted", []))
    rejected = {item["load_number"]: item.get("errors", []) for item in response_body.get("rejected", [])}

    results = []
    for load in sanitized_loads:
        load_number = load["load_number"]
        if load_number in accepted:
            results.append({"load_number": load_number, "status": "pushed", "payload": load})
        elif load_number in rejected:
            results.append({
                "load_number": load_number,
                "status": "rejected",
                "payload": load,
                "errors": rejected[load_number],
            })
        else:
            results.append({"load_number": load_number, "status": "unknown", "payload": load})
    return results


@shv_blueprint.post("/loads")
def push_loads():
    """Sanitize all submitted Walmart loads and push the valid ones to SHV."""
    logging.info("Sanitizing and pushing Walmart loads to SHV")
    body = request.get_json(silent=True) or {}
    loads = body.get("loads", [])
    if "load" in body:
        loads = [body["load"]]
    if not loads:
        return jsonify({"status": "error", "message": "At least one load is required"}), 400

    constants = current_app.config["APP_CONSTANTS"]
    sanitized_loads = []
    local_rejections = []
    # Isolate failures per load so one malformed record cannot block the rest of the batch.
    for load in loads:
        if not isinstance(load, dict):
            logging.error("Skipping malformed load entry: expected an object")
            local_rejections.append({
                "load_number": "UNKNOWN",
                "status": "rejected",
                "payload": load,
                "errors": ["Load must be an object with the expected fields"],
            })
            continue

        load_number = str(load.get("load_no", "UNKNOWN")).strip()
        try:
            sanitized_loads.append(sanitize_load(load, constants))
        except (KeyError, TypeError, ValueError) as error:
            logging.error("Skipping load %s: sanitization failed", load_number)
            local_rejections.append({
                "load_number": load_number,
                "status": "rejected",
                "payload": load,
                "errors": [str(error)],
            })

    if not sanitized_loads:
        return jsonify({
            "status": "error",
            "message": "No loads could be sanitized",
            "results": local_rejections,
        }), 400

    integration = constants["integration"]
    try:
        response = requests.post(
            integration["shv_loads_url"],
            headers={
                "Authorization": f"Bearer {integration['account_email']}",
                "Content-Type": "application/json",
            },
            json={"loads": sanitized_loads},
            timeout=integration["request_timeout_seconds"],
        )
        response_body = response.json()
        response_body["results"] = local_rejections + build_push_results(sanitized_loads, response_body)
        logging.info("SHV load push completed with status %s", response.status_code)
        return jsonify(response_body), response.status_code
    except (requests.RequestException, ValueError):
        logging.error("SHV API request failed or returned invalid JSON")
        return jsonify({"status": "error", "message": "Unable to push loads to SHV"}), 502