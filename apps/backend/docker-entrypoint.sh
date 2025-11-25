#!/bin/sh
set -e

echo "[Entrypoint] Starting StyleLicense Backend..."

# Setup OAuth (cleanup duplicates and create SocialApp)
echo "[Entrypoint] Setting up OAuth..."
python manage.py cleanup_oauth || echo "[Entrypoint] Warning: OAuth setup failed, continuing..."

# Start Gunicorn
echo "[Entrypoint] Starting Gunicorn..."
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
