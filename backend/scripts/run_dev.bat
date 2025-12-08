@echo off
REM Script untuk menjalankan development server

echo ========================================
echo Starting YouTube Automation Backend
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

echo Starting FastAPI server on http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo.

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
