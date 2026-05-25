# Breathe ESG

Prototype for ingesting enterprise emissions data from SAP, utility portals, and corporate travel exports — normalizing it to GHG-scoped activity rows and supporting analyst review before audit lock.

**Live app:** https://breathe-esg-2e35.onrender.com  
**Repository:** https://github.com/HarshYadv5554/Breathe

| | |
|---|---|
| Username | `analyst` |
| Password | `breathe2026` |

---

## Overview

Breathe ESG addresses the onboarding problem: every client’s data lives in a different system, shape, and quality level. This app:

1. **Ingests** CSV exports from three source types (SAP MM, utility portal, Concur-style travel)
2. **Normalizes** rows to Scope 1/2/3 with unit conversion and suspicion flags
3. **Surfaces** a review dashboard where analysts approve, reject, or lock rows for audit

Carbon calculation (tCO₂e) is intentionally out of scope — the focus is ingestion, normalization, and review workflow.

---

## Features

- Multi-tenant data model (`Organization` boundary)
- Source-specific parsers with realistic column aliases (EN/DE SAP headers)
- Raw record preservation + normalized `EmissionActivity` rows
- Review states: pending → flagged → approved → locked
- Append-only audit trail for analyst actions

---

## Project structure

```
Breathe/
├── backend/          # Django 5 + DRF API
│   ├── core/         # Models, review API, auth
│   └── ingest/       # CSV parsers + ingestion pipeline
├── frontend/         # React + Vite analyst UI
├── sample_data/      # Test CSV files for each source
├── MODEL.md          # Data model documentation
└── DECISIONS.md      # Design decisions
```

---

## Local development

**Backend**

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

**Frontend** (separate terminal)

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 — the dev server proxies `/api` to Django on port 8000.

---

## Sample data

Upload CSVs from `sample_data/` on the **Ingest Data** page. See [sample_data/README.md](./sample_data/README.md) for which file matches each data source.

| Source | File |
|--------|------|
| SAP MM — Fuel & Procurement | `sap_mm_export.csv` |
| Utility Portal — Electricity | `utility_portal_export.csv` |
| Concur — Business Travel | `concur_travel_export.csv` |

---

## Documentation

| Document | Description |
|----------|-------------|
| [MODEL.md](./MODEL.md) | Data model, multi-tenancy, audit trail |

---

## Tech stack

- **Backend:** Django 5, Django REST Framework, Token authentication
- **Frontend:** React 18, TypeScript, Vite
- **Database:** SQLite (local), PostgreSQL (production via Render)

---

## Deployment

Deployed on [Render](https://render.com) using `render.yaml`. Production build:

```bash
./build.sh
cd backend && gunicorn breathe_api.wsgi:application --bind 0.0.0.0:$PORT
```
