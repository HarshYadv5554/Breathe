# Decisions — How We Resolved Ambiguities

## 1. SAP Integration Format

**Options considered:**
IDoc, OData APIs, BAPI, and flat-file CSV exports.

**What we chose:**
We used semicolon-separated CSV files similar to SAP MM export reports.

**Why:**
In most companies, sustainability teams usually don’t get direct SAP API access in the beginning. Monthly CSV exports from SAP reports are much more common and practical for onboarding. Setting up IDoc or OData integrations would need IT support and extra approvals, which is outside the scope of a short prototype.

**What we handled:**

* Fuel records (diesel, petrol, heating oil) → Scope 1
* Procurement records → Scope 3 purchased goods
* German and English column names (`Werks` / `Plant`, `Budat` / `Posting Date`)
* Semicolon-separated files with comma decimals (`1250,50`)
* Plant code mapping table

**What we ignored:**
IDoc parsing, OData pagination, BAPI authentication, reversals, and the complete SAP MM workflow.

**What we would ask the PM:**
Does the client have live SAP API access, or do they only share monthly CSV exports? Also, who manages the plant-to-site mapping?

---

## 2. Utility Data Source

**What we chose:**
Portal CSV exports from utility providers.

**Why:**
Most facilities teams already download electricity and utility data as CSV files from portals. PDF OCR is unreliable for a prototype, and utility APIs usually require separate registration for each provider.

**What we handled:**

* Account and meter IDs
* Billing start and end dates
* kWh consumption and tariff details
* Scope 2 purchased electricity

**What we ignored:**
PDF bill OCR, Green Button XML, 15-minute interval data, and tariff cost allocation.

**What we would ask the PM:**
Which utility providers are being used? Do they support Green Button APIs, or only CSV exports?

---

## 3. Travel Data Source

**What we chose:**
Concur-style expense report CSV uploads.

**Why:**
Finance and operations teams commonly export travel data into CSV or Excel. Direct API integrations need OAuth setup and enterprise permissions, which are difficult for a prototype.

**What we handled:**

* Flight data with airport codes
* Hotel expenses
* Ground travel and mileage
* Scope 3 business travel categories

**What we ignored:**
Live Concur APIs, Navan webhooks, travel class emissions, and advanced aviation calculations like radiative forcing.

**What we would ask the PM:**
Does the company use Concur or Navan? Do they provide API access or only exported reports?

---

## 4. Ingestion Method

| Source  | Method      | Reason                           |
| ------- | ----------- | -------------------------------- |
| SAP     | File upload | Matches monthly SAP exports      |
| Utility | File upload | Matches utility portal downloads |
| Travel  | File upload | Matches finance expense exports  |

API-based ingestion can be added later for enterprise clients with proper OAuth access.

---

## 5. Multi-Tenancy Design

We used a single shared database with `organization_id` added to each row.

**Why:**
This is much simpler and faster for a prototype compared to creating separate databases or schemas for every customer. In production, this can later move to Row-Level Security (RLS) or dedicated databases per client.

---

## 6. Suspicion vs Hard Failure

We separated invalid data into two levels:

* **Hard failure:** Missing dates or completely invalid rows. These are rejected and counted in `error_count`.
* **Suspicion flag:** Unknown units, unknown plant codes, inferred distances, etc. These rows are still created but marked for analyst review.

**Why:**
This reflects how real sustainability analysts work. Completely broken data should stop ingestion, but uncertain data should still be reviewable by humans.

---

## 7. Audit Locking

Only approved records can be locked.

Once locked:

* No further edits are allowed
* Status changes are blocked
* Auditors can see the final approved version with a full audit trail

This ensures reporting consistency during audits.

---

## 8. Frontend + Backend Deployment

We served the React frontend directly from Django.

**Why:**
This allows everything to run as a single service on Render, avoids CORS issues, and keeps deployment simple for a prototype.

Frontend build files are stored inside:

* `frontend/dist`
* Django templates
* API served at `/api/`

---

## 9. Authentication

We used DRF token authentication for the frontend application.

**Demo credentials:**

* Username: `analyst`
* Password: `breathe2026`

**Production plan:**
In a real enterprise setup, this would be replaced with SSO or SAML authentication.

---

## 10. Date Parsing

We added support for multiple date formats:

* German SAP format (`DD.MM.YYYY`)
* ISO format
* US date formats

We used `dateutil` fallback parsing, with day-first preference enabled for European clients.
