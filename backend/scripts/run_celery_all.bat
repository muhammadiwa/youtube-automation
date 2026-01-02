@echo off
REM Script untuk menjalankan Celery Worker + Beat di Windows
REM Menjalankan keduanya dalam window yang sama (parallel)

echo ========================================
echo Starting Celery Worker + Beat (Windows)
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

echo Starting Celery Beat in background...
start "Celery Beat" cmd /c "call venv\Scripts\activate.bat && celery -A app.core.celery_app beat --loglevel=info"

echo Starting Celery Worker...
echo.
echo NOTE: Beat is running in separate window.
echo Close both windows to stop all services.
echo.

celery -A app.core.celery_app worker --loglevel=info --pool=threads --concurrency=4
