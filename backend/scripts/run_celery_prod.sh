#!/bin/bash
# Production script untuk menjalankan Celery Worker
# Gunakan dengan supervisor atau systemd

set -e

# Configuration
APP_DIR="${APP_DIR:-/app}"
VENV_DIR="${VENV_DIR:-$APP_DIR/venv}"
LOG_LEVEL="${LOG_LEVEL:-info}"
CONCURRENCY="${CONCURRENCY:-4}"
POOL="${POOL:-prefork}"

# Activate virtual environment if exists
if [ -d "$VENV_DIR" ]; then
    source "$VENV_DIR/bin/activate"
fi

cd "$APP_DIR"

echo "=========================================="
echo "Starting Celery Worker (Production)"
echo "=========================================="
echo "App Dir: $APP_DIR"
echo "Log Level: $LOG_LEVEL"
echo "Concurrency: $CONCURRENCY"
echo "Pool: $POOL"
echo "=========================================="

exec celery -A app.core.celery_app worker \
    --loglevel=$LOG_LEVEL \
    --pool=$POOL \
    --concurrency=$CONCURRENCY \
    --hostname=worker@%h
