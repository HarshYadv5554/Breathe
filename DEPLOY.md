# Deployment to Render (required for submission)

## Prerequisites

1. Push this repo to GitHub (private is fine).
2. Share the repo with `saurav@breatheesg.com`, `rahul@breatheesg.com`, `shivang@breatheesg.com`.
3. Log in to [Render](https://render.com) (workspace connected in Cursor MCP).

## Option A — Blueprint (recommended)

1. Render Dashboard → **New** → **Blueprint**
2. Connect your GitHub repo
3. Render reads `render.yaml` and creates:
   - PostgreSQL database `breathe-db`
   - Web service `breathe-esg`
4. After deploy, set environment variable on the web service:
   - `CORS_ALLOWED_ORIGINS` = `https://<your-service>.onrender.com` (same origin if SPA is served by Django — optional)
5. Copy the public URL (e.g. `https://breathe-esg.onrender.com`) into your submission email.

## Option B — Manual web service

- **Runtime:** Python 3.12
- **Build command:** `bash build.sh`
- **Start command:** `cd backend && gunicorn breathe_api.wsgi:application --bind 0.0.0.0:$PORT`
- **Env:** `DATABASE_URL` from Render Postgres, `DEBUG=false`, `DJANGO_SECRET_KEY` (generate)

## Demo credentials (after `seed_demo` in build)

| Field | Value |
|-------|-------|
| Username | `analyst` |
| Password | `breathe2026` |

## Verify deployment

1. Open `/` — login page loads
2. Sign in → Dashboard shows ingestion stats
3. Upload `sample_data/sap_mm_export.csv` under SAP source
4. Review Queue → flagged rows visible → Approve → Lock for audit
