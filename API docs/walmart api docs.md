# Freight Tender API — Carrier Integration Guide
Retail Link® Transportation · Build FTM-PRD 4.7.12

## Overview
The Freight Tender API provides read-only access to the open freight tenders assigned to your carrier account. Records mirror the tender data shown in the Freight Order Monitor.

## Authentication
Every request must carry your account e-mail address as a bearer token — use the same e-mail address you have used to communicate with us throughout your hiring process:
```
Authorization: Bearer [candidate email address]
```
Requests without a valid address receive `401`.

## Get open tenders
```
GET https://wmt-freight-portal.vercel.app/api/sap/loads
```
Returns a JSON envelope: `{ "source": string, "count": number, "loads": [ ... ] }`.

## Tender record fields
| Field | Type | Description |
|---|---|---|
| `load_no` | string | Load number, "LD-" prefix |
| `tender_id` | string | Tender identifier |
| `frt_ord_no` | string | Freight order number (SAP) |
| `carrier_scac` | string | Carrier SCAC code |
| `shipper_nm` | string | Shipper / vendor name |
| `vendor_nbr` | string | Vendor number |
| `orig_city` | string | Origin city |
| `orig_st` | string | Origin state |
| `dc_nbr` | string | Destination DC number |
| `dest_city` | string | Destination city |
| `dest_st` | string | Destination state |
| `dept_nbr` | string | Department number |
| `shp_dt` | string | Requested ship date, MMDDYYYY |
| `del_dt` | string | Requested delivery date, MMDDYYYY |
| `pallet_cnt` | string | Pallet count |
| `case_cnt` | string | Case count |
| `wgt` | string | null | Gross weight as displayed, e.g. "41,860 lbs" |
| `dist_mi` | string | Route distance, miles |
| `hazmat_flg` | string | Hazmat flag, Y/N |
| `mode` | string | Transport mode / temperature classification code |

## Example request
```bash
curl https://wmt-freight-portal.vercel.app/api/sap/loads \
  -H "Authorization: Bearer [candidate email address]"
```

## Example response
```json
{
  "source": "WMT Freight Tender Portal",
  "count": 3,
  "loads": [
    {
      "load_no": "LD-20841",
      "tender_id": "T-88231904",
      "frt_ord_no": "4500219873",
      "carrier_scac": "SHVL",
      "shipper_nm": "NESTLE USA INC",
      "vendor_nbr": "068704212",
      "orig_city": "Anderson",
      "orig_st": "IN",
      "dc_nbr": "6094",
      "dest_city": "Bentonville",
      "dest_st": "AR",
      "dept_nbr": "92",
      "shp_dt": "07152026",
      "del_dt": "07172026",
      "pallet_cnt": "26",
      "case_cnt": "1,842",
      "wgt": "41,860 lbs",
      "dist_mi": "612",
      "hazmat_flg": "N",
      "mode": "AMBIENT"
    }
  ]
}
```

## Rate limits
60 requests per minute per source address. Exceeding the limit returns `429` with a `Retry-After` header.

## Status codes
| Code | Meaning |
|---|---|
| 200 | OK — open tenders returned |
| 401 | Missing or malformed Authorization header |
| 429 | Rate limit exceeded — retry after the number of seconds in the Retry-After header |