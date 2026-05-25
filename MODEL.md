# Data Model — Breathe ESG Prototype

## Design goal

Model the **ingestion → normalization → analyst review → audit lock** pipeline with explicit multi-tenancy, scope classification, source provenance, unit normalization, and an append-only audit trail. Carbon calculation is intentionally out of scope; we produce **review-ready activity rows** with normalized quantities.

## Entity relationship (conceptual)

```
Organization
  ├── OrganizationMembership → User
  ├── PlantLookup (SAP Werks → site name)
  ├── DataSource (registry of SAP / utility / travel systems)
  └── IngestionBatch (one upload)
        ├── RawRecord (immutable source row JSON)
        └── EmissionActivity (normalized, reviewable)
              └── ActivityAuditLog (append-only)
```

## Multi-tenancy

| Model | Isolation |
|-------|-----------|
| `Organization` | Root tenant; `slug` for URLs/API |
| `OrganizationMembership` | Links Django `User` to org with role (`analyst`, `admin`) |
| All operational models | FK to `organization_id`; API scoped via `/api/orgs/{org_id}/...` |

Every API endpoint (except login) checks `OrganizationMembership` via `IsOrgMember`. Cross-tenant reads are impossible without membership.

## Scope 1 / 2 / 3 categorization

`EmissionActivity` carries:

- **`scope`**: `1`, `2`, or `3` (GHG Protocol scopes)
- **`category`**: enum aligned to GHG subcategories we ingest:
  - Scope 1: `stationary_combustion`, `mobile_combustion`
  - Scope 2: `purchased_electricity`
  - Scope 3: `purchased_goods`, `business_travel`
- **`subcategory`**: freeform refinement (`fuel`, `air`, `hotel`, `grid_electricity`, tariff code, etc.)

Classification happens in **source parsers** (business rules per format), not in the DB — the model stores the outcome so analysts can override via edit + audit log.

## Source-of-truth tracking

| Field / model | Purpose |
|---------------|---------|
| `DataSource` | Which system (SAP MM, utility portal, Concur) is registered for the tenant |
| `IngestionBatch` | When/who uploaded; filename; pipeline counts |
| `RawRecord.raw_payload` | Exact source row as JSON (provenance) |
| `EmissionActivity.data_source` | FK — which source produced this row |
| `source_reference` | Document/report/meter ID from source |
| `source_row_hash` | SHA-256 of normalized keys — dedup hint |
| `batch` + `raw_record` | Link normalized row back to upload and raw line |

## Unit normalization

| Field | Meaning |
|-------|---------|
| `quantity_raw` / `unit_raw` | As reported in source file |
| `quantity_normalized` / `unit_normalized` | Converted to canonical units (`liters`, `kg`, `kwh`, `km`, `*_spend`) |

Conversion table lives in `ingest/parsers/common.py` (liters, kg, kWh, miles→km, gallons→liters). Unrecognized units set `unit_mismatch` suspicion flag rather than silently guessing.

## Review workflow

`review_status` state machine:

```
pending → approved → locked
   ↓         ↓
flagged   rejected
```

- **Flagged**: auto-set when `suspicion_flags` non-empty after ingestion
- **Approved**: analyst sign-off
- **Locked**: immutable for auditors (no further edits)
- **`is_edited`**: true if analyst PATCHed quantity/description

## Audit trail

`ActivityAuditLog` is **append-only**:

- Actions: `created`, `edited`, `approved`, `rejected`, `flagged`, `locked`
- `field_changes`: JSON diff `{field: {old, new}}`
- `user` + `created_at` on every analyst action

We do not overwrite history; corrections are new log entries.

## Why not a single "Emissions" table?

Separating `RawRecord` from `EmissionActivity` lets us:

1. Show analysts exactly what SAP/Concur sent vs what we normalized
2. Re-run normalization without losing source evidence
3. Count parse errors separately from business-rule flags

## Indexes

- `(organization, review_status)` — review queue queries
- `(organization, scope)` — scope-filtered dashboards
- `source_row_hash` — duplicate detection (future)
