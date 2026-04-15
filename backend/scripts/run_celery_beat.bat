@echo off
REM Script untuk menjalankan Celery Beat scheduler

echo ========================================
echo Starting Celery Beat Scheduler
echo ========================================
echo.

REM Check if venv exists
if not exist venv (
    echo ERROR: Virtual environment tidak ditemukan.
    echo Jalankan setup_venv.bat terlebih dahulu.
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

echo Starting Celery Beat...
echo.

celery -A app.core.celery_app beat --loglevel=info
