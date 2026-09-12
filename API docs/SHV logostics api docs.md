# SOR Integration API
SHV Logistics · TMS: Broker/3PL · System of Record

## Overview
The SOR Integration API creates and reads load records in the SHV Logistics system of record. Loads created through this API appear on the account's Loads board immediately.

## Authentication
Every request must carry your account email address as a bearer token — use the same email address you have used to communicate with us throughout your hiring process:
```
Authorization: Bearer [candidate email address]
```

## Create or update loads
```
POST https://shv-logistics-tms.vercel.app/api/sor/loads
Content-Type: application/json
```
Body: `{ "load": { ... } }` for one load, or `{ "loads": [ ... ] }` for up to 50.

Writes are upserts keyed by `load_number`: submitting an existing load number overwrites the stored record (prior versions remain visible in the record's Load History).

`load_number` must correspond to an open tender assigned to the authenticated account. Load numbers with no matching tender are rejected ("No matching tender on file").

## Field reference (all fields required)
| Field | Format |
|---|---|
| `load_number` | Load number. Format "LD-" followed by digits, e.g. "LD-20841" |
| `bol_number` | Bill of lading number |
| `shipper_name` | Shipper name |
| `origin_city` | Origin city |
| `origin_state` | Origin state code |
| `destination_city` | Destination city |
| `destination_state` | Destination state code |
| `ship_date` | Expected ship date. Exactly 8 digits, DDMMYYYY, e.g. "15072026" |
| `delivery_date` | Expected delivery date. Exactly 8 digits, DDMMYYYY |
| `weight` | Total weight in whole pounds. JSON number — no units, commas, or quotes |
| `equipment_type` | Exactly "Reefer 53'" or "Dry Van 53'" |

String fields are limited to 200 characters and must not have leading or trailing whitespace.

## Example request
```bash
curl -X POST https://shv-logistics-tms.vercel.app/api/sor/loads \
  -H "Authorization: Bearer [candidate email address]" \
  -H "Content-Type: application/json" \
  -d '{
    "load": {
      "load_number": "LD-20841",
      "bol_number": "4500219873",
      "shipper_name": "NESTLE USA INC",
      "origin_city": "Anderson",
      "origin_state": "IN",
      "destination_city": "Bentonville",
      "destination_state": "AR",
      "ship_date": "15072026",
      "delivery_date": "17072026",
      "weight": 41860,
      "equipment_type": "Dry Van 53'"
    }
  }'
```

## Example response — accepted (200)
```json
{
  "status": "ok",
  "message": "1 load(s) accepted into the system of record.",
  "accepted": ["LD-20841"],
  "rejected": []
}
```

## Example response — validation failure (422)
```json
{
  "status": "rejected",
  "message": "1 load(s) rejected by the SOR. Fix the errors and push again — pushes are safe to retry (same load_number overwrites).",
  "accepted": [],
  "rejected": [
    {
      "load_number": "LD-20841",
      "errors": [
        "ship_date must be 8 digits in DDMMYYYY format (e.g. 15072026). Got \"07152026\". That looks like MMDDYYYY — the SOR requires DDMMYYYY (day first)."
      ]
    }
  ]
}
```
Validation errors name the failing field and the expected format. Pushes are safe to retry.

## List stored loads
```
GET https://shv-logistics-tms.vercel.app/api/sor/loads
```
Returns the authenticated account's stored loads: `{ "owner": string, "count": number, "loads": [ ... ] }`.

## Rate limits & capacity
POST: 30 requests per minute per source address. GET: 60 per minute. Accounts hold at most 50 stored loads. Exceeding a limit returns `429` with a `Retry-After` header.

## Status codes
| Code | Meaning |
|---|---|
| 200 | All loads accepted |
| 400 | Malformed request body |
| 401 | Missing or malformed Authorization header |
| 422 | One or more loads rejected — per-load errors in the response body |
| 429 | Rate limit or account capacity exceeded — see Retry-After header |