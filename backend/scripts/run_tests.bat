@echo off
REM Script untuk menjalankan tests

echo ========================================
echo Running Tests
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

echo Running pytest with coverage...
echo.

pytest app/ -v --cov=app --cov-report=term-missing %*
