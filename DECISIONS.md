# Decisions — Ambiguities Resolved

## 1. SAP: which integration format?

**Options considered:** IDoc, OData, BAPI, flat-file CSV from SE16/Z-reports.

**Chose:** Semicolon-delimited **flat-file CSV** (SAP MM material document style).

**Why:** Enterprise sustainability teams often lack real-time SAP API access. Monthly extracts from custom Z-reports or SE16 exports are common. IDoc/OData require IT integration projects outside a 4-day prototype.

**Subset handled:**
- Fuel (diesel, gasoline, heating oil) → Scope 1
- Procurement line items → Scope 3 purchased goods
- DE and EN column aliases (`Werks`/`Plant`, `Budat`/`Posting Date`)
- Semicolon delimiter, comma decimals (`1250,50`)
- Plant code lookup table

**Ignored:** IDoc parsing, OData pagination, BAPI auth, goods receipt reversals, full MM document lifecycle.

**Would ask PM:** Do they have a live SAP API or only monthly CSV drops? Who maintains the Werks→site mapping?

---

## 2. Utility: portal CSV vs PDF vs API

**Chose:** **Portal CSV export** (monthly interval / billing export).

**Why:** Facilities teams routinely download CSV from utility portals (PG&E, Con Edison pattern). PDF OCR is brittle and wrong for a prototype. Utility APIs exist but require per-utility registration.

**Subset handled:**
- Account + meter ID
- Billing period start/end (non-calendar months flagged)
- kWh consumption + tariff/rate schedule name
- Scope 2 purchased electricity

**Ignored:** PDF bill parsing, Green Button XML, interval-level 15-min demand, tariff cost allocation.

**Would ask PM:** Which utilities and do they have Green Button or only portal CSV?

---

## 3. Travel: which platform and mechanism?

**Chose:** **Concur-style expense report CSV** via file upload.

**Why:** Concur Expense Reports export to CSV/Excel for finance; Trip API requires OAuth enterprise setup. CSV matches how analysts receive travel data today.

**Subset handled:**
- Airfare (airport codes, inferred distance when missing)
- Hotel (spend-based quantity)
- Ground / personal mileage
- Scope 3 business travel subcategories

**Ignored:** Live Concur API, Navan webhooks, per-trip GHG factors, class of service, radiative forcing.

**Would ask PM:** Concur or Navan? Do they get trip-level API access or only expense exports?

---

## 4. Ingestion mechanism per source

| Source | Mechanism | Justification |
|--------|-----------|---------------|
| SAP | File upload | Matches monthly extract delivery |
| Utility | File upload | Matches portal download workflow |
| Travel | File upload | Matches expense report export |

API pull would be next step for clients with OAuth — not assumed in prototype.

---

## 5. Multi-tenancy model

Single database, `organization_id` on all rows (shared schema). Simpler than schema-per-tenant for prototype; production might add RLS or separate DB per enterprise client.

---

## 6. Suspicion vs hard failure

- **Hard failure:** missing activity date, unparseable row → counted in `error_count`, no `EmissionActivity` created
- **Suspicion flag:** unit mismatch, unknown plant, inferred distance → row created as `flagged`, analyst decides

This mirrors real analyst workflow: bad dates are blocked; ambiguous units need human judgment.

---

## 7. Audit lock semantics

Only **approved** rows can be **locked**. Locked rows reject PATCH and further status changes. Auditors see frozen normalized data with full audit trail.

---

## 8. Frontend served from Django

Single Render web service: React built to `frontend/dist`, `index.html` copied to Django templates, API at `/api/`. Avoids CORS complexity on free tier.

---

## 9. Authentication

Token auth (DRF) for SPA. Demo user `analyst` / `breathe2026` seeded. Production would use SSO/SAML.

---

## 10. Date parsing

Supports `DD.MM.YYYY` (German SAP), ISO, US formats via `dateutil` fallback. Day-first preferred for EU clients.
