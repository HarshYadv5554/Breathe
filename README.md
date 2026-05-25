# Breathe ESG — Data Ingestion & Analyst Review Prototype

Django REST + React app for ingesting SAP, utility, and corporate travel data; normalizing to GHG-scoped activity rows; and analyst review before audit lock.

## Live deployment

| Item | Status |
|------|--------|
| Render Postgres `breathe-db` | Created — [dashboard](https://dashboard.render.com/d/dpg-d8a2ra67r5hc73e1cggg-a) |
| Render Web Service | **Pending** — push code to GitHub first (see below) |
| Live URL | _Will be `https://breathe-esg.onrender.com` (or similar) after deploy_ |

### Finish deploy (2 steps)

**1. GitHub** — In a terminal, complete login if prompted, then push:

```powershell
gh auth login -h github.com -p https -w
cd c:\Users\91729\Desktop\Breathe
.\scripts\finish-deploy.ps1
```

Or create https://github.com/new named `Breathe-ESG`, then:

```powershell
git remote set-url origin https://github.com/HarshYadv5554/Breathe-ESG.git
git push -u origin main
```

**2. Render** — [New Blueprint](https://dashboard.render.com/blueprints) → connect `Breathe-ESG` → uses `render.yaml` (web + DB).

**Demo credentials:** `analyst` / `breathe2026`

## Local development

```bash
# Backend
cd backend
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

Frontend: http://localhost:5173 (proxies `/api` to Django)

## Production build

```bash
bash build.sh
cd backend && gunicorn breathe_api.wsgi:application
```

## Sample data

Upload files from `/sample_data`:

- `sap_mm_export.csv` — SAP MM fuel & procurement
- `utility_portal_export.csv` — utility portal electricity
- `concur_travel_export.csv` — Concur-style travel expenses

## Documentation (assignment deliverables)

- [MODEL.md](./MODEL.md) — data model rationale
- [DECISIONS.md](./DECISIONS.md) — ambiguities resolved
- [TRADEOFFS.md](./TRADEOFFS.md) — what we didn't build
- [SOURCES.md](./SOURCES.md) — source research & sample data

## API overview

- `POST /api/auth/login/`
- `GET /api/orgs/{id}/dashboard/`
- `POST /api/orgs/{id}/sources/{source_id}/upload/` (multipart file)
- `GET /api/orgs/{id}/activities/?status=flagged`
- `POST /api/orgs/{id}/activities/{id}/approve|reject|lock/`

## Tech stack

- Django 5 + DRF + Token auth
- React 18 + Vite + TypeScript
- SQLite (local) / PostgreSQL (Render)
