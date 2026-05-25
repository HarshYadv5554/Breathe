# Sample upload files — Data Ingestion

Use these CSV files on the **Ingest Data** page. Pick the matching **Data source** dropdown option, then **Choose File** → **Upload & normalize**.

## Which file for which dropdown?

| Data source (in app) | Upload this file | Format |
|----------------------|------------------|--------|
| **SAP MM — Fuel & Procurement** | `sap_mm_export.csv` | CSV, **semicolon** (`;`) delimiter |
| **Utility Portal — Electricity** | `utility_portal_export.csv` | CSV, **comma** (`,`) delimiter |
| **Concur — Business Travel** | `concur_travel_export.csv` | CSV, **comma** (`,`) delimiter |

Optional: `sap_mm_export_german_headers.csv` — same data with German SAP column names (tests DE/EN alias mapping).

---

## 1. SAP MM — Fuel & Procurement

**Real-world shape:** Export from SAP (SE16 / custom Z-report): material documents for fuel and purchased goods.

**Required columns (English or German aliases):**

| Column | German alias | Example |
|--------|--------------|---------|
| Material Document | Belegnummer | 4900123456 |
| Posting Date | Buchungsdatum | 15.03.2025 |
| Plant | Werks | 1000 |
| Description | Kurztext | Diesel fuel - fleet vehicles |
| Quantity | Menge | 1250,50 |
| Unit | Meins | L, GAL, KG |
| Vendor | Name1 | Shell Deutschland GmbH |
| Movement Type | Bewegungsart | 201 |

**Notes:**
- Use **semicolons** between columns (European SAP export default).
- Decimals can use comma: `1250,50`
- Plant codes `1000`, `2000`, `3000` map to sites (seeded in demo). Plant `9999` will be **flagged** (unknown plant).

---

## 2. Utility Portal — Electricity

**Real-world shape:** Monthly CSV download from a utility customer portal (account, meter, billing period, kWh).

**Required columns:**

| Column | Example |
|--------|---------|
| Account Number | ACC-77821 |
| Meter Number | MTR-00142 |
| Service Address | 100 Industrial Pkwy, Chicago IL |
| Period Start | 2025-01-17 |
| Period End | 2025-02-16 |
| Consumption | 145230 |
| Unit | kWh |
| Rate Schedule | GS-1 General Service |

**Notes:**
- Comma-separated CSV.
- Billing periods that don’t align to calendar months (e.g. Jan 17 – Feb 16) are **flagged** for analyst review.

---

## 3. Concur — Business Travel

**Real-world shape:** Expense report export from Concur (or similar): flights, hotels, ground transport.

**Required columns:**

| Column | Example |
|--------|---------|
| Report ID | RPT-2025-00142 |
| Employee Name | Jane Smith |
| Transaction Date | 2025-03-05 |
| Expense Type | Airfare, Hotel, Ground Transport |
| Merchant | United Airlines |
| Amount | 1245.00 |
| Currency | USD |
| Origin Airport Code | JFK |
| Destination Airport Code | LHR |
| Distance | (optional) |
| Distance Unit | mi or km |

**Notes:**
- Comma-separated CSV.
- Flights **without distance** use airport-pair lookup and are **flagged** (`missing_distance`).
- Hotels use **spend** (amount + currency) as the normalized quantity.

---

## After upload

Go to **Review Queue** to see normalized rows, suspicion flags, approve/reject, and lock approved rows for audit.
