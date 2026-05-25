#!/usr/bin/env bash
set -euo pipefail

echo "==> Installing Python dependencies"
pip install -r backend/requirements.txt

echo "==> Building React frontend"
cd frontend
if command -v npm >/dev/null 2>&1; then
  npm ci
  npm run build
else
  echo "npm not found — using committed frontend/dist if present"
  test -f dist/index.html || (echo "No dist/ and no npm; build failed" && exit 1)
fi
cd ..

echo "==> Copying frontend build into Django templates"
mkdir -p backend/templates
cp frontend/dist/index.html backend/templates/index.html

echo "==> Collecting static files & running migrations"
cd backend
python manage.py collectstatic --noinput
python manage.py migrate --noinput
python manage.py seed_demo

echo "==> Build complete"
