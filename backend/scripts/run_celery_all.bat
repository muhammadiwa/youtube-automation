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

REM Kill any existing celery processes first
echo Cleaning up existing Celery processes...
taskkill /F /IM celery.exe 2>nul

echo.
echo Starting Celery Beat in background...
start "Celery Beat" /MIN cmd /c "call venv\Scripts\activate.bat && celery -A app.core.celery_app beat --loglevel=info"

echo Starting Celery Worker...
echo.
echo ========================================
echo NOTE: 
echo - Beat is running in minimized window
echo - To stop ALL Celery: run scripts\stop_celery.bat
echo - Or press Ctrl+C here then run stop_celery.bat
echo ========================================
echo.

celery -A app.core.celery_app worker --loglevel=info --pool=threads --concurrency=4

REM When worker exits, also stop beat
echo.
echo Worker stopped. Cleaning up Beat process...
taskkill /F /FI "WINDOWTITLE eq Celery Beat*" 2>nul
echo Done.
