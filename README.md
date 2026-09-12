# LoadBridge

Automating the flow of Walmart freight tenders into SHV TMS.

LoadBridge is a small Flask operations dashboard that fetches open Walmart freight tenders, sanitizes them into the SHV load contract, and pushes them to the SHV TMS API. It replaces the manual, tender-by-tender copy work described in the workflow SOP with two actions: **Fetch Loads** and **Sanitize & Push**.

## 1. What it does

1. **Fetch Loads** — calls the Walmart Freight Order Monitor API and displays every open tender in a table, exactly as returned (no mode or weight filtering, per the assessment requirement).
2. **Sanitize & Push** — converts the fetched tenders into the SHV load payload shape and posts them to the SHV TMS API in a single batch, then shows the accepted/rejected result per load.

## 2. Architecture

```text
app.py                 Flask app factory, constants loader, template rendering
routes/
  health.py            GET /health
  walmart.py           GET /api/walmart/loads  (fetches tenders from Walmart)
  shv.py                POST /api/shv/loads     (sanitizes + pushes loads to SHV)
templates/index.html   Server-rendered dashboard shell
static/app.js          Fetch/push button logic, table rendering
static/styles.css      Dashboard styling
constants.json         All UI copy, API URLs, account email, mode mapping
vercel.json            Vercel Python deployment config
requirements.txt       Flask, requests, pytest
```

The browser never receives the account email or API URLs — `app.py` strips the `integration` section of `constants.json` out of the constants passed to the template, so those calls only ever happen server-side in `routes/walmart.py` and `routes/shv.py`.

## 3. Configuration

All static values (URLs, account email, request timeout, UI copy, mode mapping) live in [constants.json](constants.json), not in templates or JavaScript:

```json
{
  "integration": {
    "account_email": "vaishnavirkekuda@gmail.com",
    "walmart_loads_url": "https://wmt-freight-portal.vercel.app/api/sap/loads",
    "shv_loads_url": "https://shv-logistics-tms.vercel.app/api/sor/loads",
    "request_timeout_seconds": 15
  }
}
```

The assessment requires the account email to be hardcoded as the API input, so it is stored in this config file rather than an environment variable.

## 4. Local setup

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Visit `http://127.0.0.1:5000`. Click **Fetch Loads**, review the tender table, then click **Sanitize & Push** to send the batch to SHV.

## 5. API behavior

### `GET /api/walmart/loads`
Calls the Walmart API with `Authorization: Bearer <account_email>` and returns the raw tender envelope. On HTTP or network failure it returns `{"status": "error", "message": ...}` with the upstream status code (or `502` for network/parse failures).

### `POST /api/shv/loads`
Accepts `{"loads": [...]}` or `{"load": {...}}`. For each load:
- trims all string fields;
- converts `shp_dt`/`del_dt` from Walmart's `MMDDYYYY`/`MM/DD/YYYY` to SHV's `DDMMYYYY`;
- strips commas/whitespace/`lbs` from `wgt` and converts it to an integer;
- maps `mode` to an SHV equipment type (`AMBIENT` → `Dry Van 53'`, `REFRIGERATED`/`FREEZER` → `Reefer 53'`, anything else → `Contact Operator`).

The full sanitized batch is POSTed to SHV in one request. SHV performs an upsert by `load_number`, so pushing the same load twice updates it rather than duplicating it. An empty load list is rejected locally with `400` before any network call is made. Every accepted/rejected load in the SHV response is surfaced back to the UI unchanged.

## 6. Validation rules applied during sanitization

| Field | Rule |
|---|---|
| Dates | Must resolve to 8 digits; reordered from `MMDDYYYY` to `DDMMYYYY` |
| Weight | Non-digit characters removed; result must be non-empty and numeric |
| Mode | Unmapped values default to `Contact Operator` instead of being dropped — the app loads every record it receives |

## 7. Testing

```powershell
pytest
```

Run the test suite before making UI changes to confirm date conversion, weight cleanup, mode mapping, and the SHV payload shape are unaffected.

## 8. Deployment (Vercel)

1. Push this repository to GitHub.
2. Import the repository into Vercel; it will detect `vercel.json` and build `app.py` with `@vercel/python`.
3. Vercel auto-deploys on every commit to the connected branch once the project is linked.

