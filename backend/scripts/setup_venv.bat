@echo off
REM Script untuk setup virtual environment dan install dependencies

echo ========================================
echo YouTube Automation Backend Setup
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python tidak ditemukan. Silakan install Python 3.11+
    exit /b 1
)

REM Create virtual environment
echo [1/4] Membuat virtual environment...
if exist venv (
    echo Virtual environment sudah ada, skip...
) else (
    python -m venv venv
    echo Virtual environment berhasil dibuat!
)

REM Activate virtual environment
echo [2/4] Mengaktifkan virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo [3/4] Upgrade pip...
python -m pip install --upgrade pip

REM Install dependencies
echo [4/4] Install dependencies...
pip install -r requirements.txt

echo.
echo ========================================
echo Setup selesai!
echo ========================================
echo.
echo Untuk mengaktifkan venv, jalankan:
echo   venv\Scripts\activate
echo.
echo Untuk menjalankan server:
echo   uvicorn app.main:app --reload
echo.
echo Untuk menjalankan Celery worker:
echo   celery -A app.core.celery_app worker --loglevel=info
echo.
echo Untuk menjalankan tests:
echo   pytest app/
echo.
