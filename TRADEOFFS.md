# Tradeoffs — Three Things We Deliberately Did Not Build

## 1. GHG emission factor calculation and tCO₂e output

**What we skipped:** Applying DEFRA/EPA/IPCC factors to normalized quantities to produce CO₂e totals.

**Why:** The assignment states the hard part is ingestion and normalization across heterogeneous sources — not carbon math. Building factor lookup, GWP versions, and market-based Scope 2 would duplicate work that isn't graded (35% is data model, 20% is realistic ingestion).

**What we did instead:** Store `quantity_normalized` + `unit_normalized` + `scope`/`category` so a downstream calc engine can consume approved rows.

---

## 2. Live API integrations (SAP OData, Concur OAuth, utility Green Button)

**What we skipped:** Real-time pulls from SAP S/4HANA OData, Concur Trip API, or utility interval APIs.

**Why:** Each requires enterprise credentials, OAuth apps, and client-specific IT approval — unavailable in a take-home. File upload matches how data actually arrives in month 1 of onboarding.

**What we'd build next:** Source-specific connectors behind the same `IngestionBatch` → `RawRecord` → `EmissionActivity` pipeline.

---

## 3. PDF utility bill OCR and duplicate detection engine

**What we skipped:** OCR pipeline for scanned bills; automated deduplication across batches.

**Why:** PDF OCR is high-effort, low-reliability without training data. Duplicate detection needs production history and fuzzy matching rules we can't validate in a prototype.

**What we did instead:** `source_row_hash` field and `duplicate_suspected` flag placeholder; portal CSV chosen to avoid OCR entirely.
