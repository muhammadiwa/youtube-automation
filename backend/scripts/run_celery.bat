@echo off
REM Script untuk menjalankan Celery worker

echo ========================================
echo Starting Celery Worker
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

echo Starting Celery worker...
echo.

celery -A app.core.celery_app worker --loglevel=info --pool=solo
