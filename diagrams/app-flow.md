# Application Flow

This document shows how the user operates the app and how each button communicates with the external APIs.

## Main User Flow

```mermaid
flowchart TD
	Start[Open LoadBridge] --> Fetch[Click Fetch Loads]
	Fetch --> WalmartRoute[GET /api/walmart/loads]
	WalmartRoute --> WalmartAPI[Walmart API]
	WalmartAPI --> Raw[Display all 11 raw tender fields per row]
	Raw --> Push[Click Sanitize & Push]
	Push --> Sanitize[Sanitize each load independently]
	Sanitize --> SHVRoute[POST /api/shv/loads]
	SHVRoute --> SHVAPI[SHV TMS API]
	SHVAPI --> Result[Render a pushed/rejected result card per load]
```

## Fetch Loads

```mermaid
sequenceDiagram
	participant User
	participant Flask as app.py
	participant WalmartRoute as routes/walmart.py
	participant Walmart as Walmart API

	User->>Flask: Click Fetch Loads
	Flask->>WalmartRoute: GET /api/walmart/loads
	WalmartRoute->>Walmart: GET /api/sap/loads
	Walmart-->>WalmartRoute: Tender JSON
	WalmartRoute-->>Flask: Tender JSON
	Flask-->>User: Display all tenders
```

## Sanitize and Push

The push step will apply the documented transformations, one load at a time:

- Convert Walmart dates to the SHV date format.
- Remove commas and the `lbs` label from weight.
- Map known Walmart modes to SHV equipment types (unmapped modes become `Contact Operator`).
- If a single load fails sanitization (bad date, unparsable weight, malformed record), it is recorded as a local rejection and excluded from the SHV request — it does not block the other loads in the batch.
- Send the remaining sanitized loads to the SHV API in one request.
- Combine the local rejections with the SHV accepted/rejected outcome into one `results` list, one entry per original load.
- Render a result card per load: a `Pushed` or `Rejected` badge, the load number, the exact JSON payload sent to SHV, and any validation errors.

```mermaid
sequenceDiagram
	participant User
	participant Flask as app.py
	participant SHVRoute as routes/shv.py
	participant SHV as SHV TMS API

	User->>Flask: Click Sanitize & Push
	Flask->>SHVRoute: POST /api/shv/loads
	SHVRoute->>SHVRoute: Sanitize each load and isolate failures as local rejections
	SHVRoute->>SHV: POST /api/sor/loads (sanitizable loads only)
	SHV-->>SHVRoute: Accepted or rejected load numbers
	SHVRoute->>SHVRoute: build_push_results() merges local rejections + SHV outcome
	SHVRoute-->>Flask: Push result JSON with a results array
	Flask-->>User: Render a pushed/rejected card per load
```
