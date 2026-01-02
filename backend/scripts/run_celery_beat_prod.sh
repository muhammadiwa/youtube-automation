#!/bin/bash
# Production script untuk menjalankan Celery Beat Scheduler
# PENTING: Hanya jalankan 1 instance!

set -e

# Configuration
APP_DIR="${APP_DIR:-/app}"
VENV_DIR="${VENV_DIR:-$APP_DIR/venv}"
LOG_LEVEL="${LOG_LEVEL:-info}"
SCHEDULE_FILE="${SCHEDULE_FILE:-/tmp/celerybeat-schedule}"

# Activate virtual environment if exists
if [ -d "$VENV_DIR" ]; then
    source "$VENV_DIR/bin/activate"
fi

cd "$APP_DIR"

echo "=========================================="
echo "Starting Celery Beat (Production)"
echo "=========================================="
echo "App Dir: $APP_DIR"
echo "Log Level: $LOG_LEVEL"
echo "Schedule File: $SCHEDULE_FILE"
echo "=========================================="
echo "WARNING: Only run ONE instance of beat!"
echo "=========================================="

exec celery -A app.core.celery_app beat \
    --loglevel=$LOG_LEVEL \
    --schedule=$SCHEDULE_FILE
