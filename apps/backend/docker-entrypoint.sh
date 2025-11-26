#!/bin/sh
set -e

echo "[Entrypoint] Starting StyleLicense Backend..."

# Start Gunicorn
echo "[Entrypoint] Starting Gunicorn..."
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
