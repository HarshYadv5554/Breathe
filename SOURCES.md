# Sources — Research, Sample Data, Production Gaps

## 1. SAP — Fuel & Procurement

### What we researched

- SAP MM material documents and movement types (201/261 for goods issue/consumption)
- Common sustainability team workflow: **SE16 / custom Z-report → CSV export**
- European deployments often use **semicolon separators** and **German headers** (`Budat`, `Werks`, `Menge`, `Meins`)
- Plant codes (`Werks`) require client-specific mapping to physical sites

### What we learned

- Full IDoc/OData integration is IT-heavy; CSV extracts are the pragmatic first-mile
- Units vary (`L`, `GAL`, `KG`, `EA`) and amounts use locale-specific decimals
- Not every row is fuel — procurement dominates line count; keyword + movement type classification is fragile

### Sample data (`sample_data/sap_mm_export.csv`)

| Row | Purpose |
|-----|---------|
| Diesel/gasoline/heating oil | Scope 1 fuel with DE and US units |
| Office supplies / IT equipment | Scope 3 procurement |
| Plant `9999` | Unknown plant → `unknown_plant` flag |
| `EA` unit on IT row | Unrecognized unit → `unit_mismatch` flag |

### What breaks in production

- Custom Z-report column names we didn't alias
- Multi-line invoices collapsed incorrectly
- Currency conversion for global rollups
- Reversals/credit memos double-counting
- Real Werks table has hundreds of codes

---

## 2. Utility — Electricity

### What we researched

- Utility customer portals (PG&E, Con Edison patterns): monthly **CSV download** with account, meter, billing period, kWh
- Billing periods often **mid-month to mid-month**, not calendar months
- Rate schedules / tariffs affect cost but activity data is kWh

### What we learned

- Facilities teams rarely have API access initially
- PDF bills are common but terrible for automated ingestion without OCR
- Multiple meters per site need aggregation rules we don't implement

### Sample data (`sample_data/utility_portal_export.csv`)

| Row | Purpose |
|-----|---------|
| Chicago mid-month periods | `billing_period_gap` flag |
| Frankfurt calendar month | Clean period |
| Singapore commercial tariff | Different rate schedule label |

### What breaks in production

- Demand charges vs energy (kW vs kWh) — we only handle energy
- Solar/net metering exports
- Estimated vs actual reads
- Multi-utility formats (dozens of CSV schemas)

---

## 3. Corporate Travel — Concur-style

### What we researched

- SAP Concur Expense Reports: CSV exports with expense type, merchant, amounts
- Trip API exists but requires partner OAuth; exports are more common for ESG teams
- Flights often have **airport codes without distance**; hotels are spend-based

### What we learned

- Scope 3 business travel needs subcategory (air/hotel/ground) for different emission factors
- Distance inference from airport pairs is approximate — must be flagged
- Personal car mileage often in miles

### Sample data (`sample_data/concur_travel_export.csv`)

| Row | Purpose |
|-----|---------|
| JFK→LHR without distance | Inferred km + `missing_distance` flag |
| Hotel only | Spend-based normalization |
| Personal mileage 120 mi | Miles → km conversion |
| SFO→ORD with km | Direct distance, no flag |

### What breaks in production

- Multi-leg trips split across rows
- Refunds/chargebacks
- Private vs business trip classification
- International rail and ride-hail categories
- Real airport distance needs great-circle DB (we use a tiny static table)
