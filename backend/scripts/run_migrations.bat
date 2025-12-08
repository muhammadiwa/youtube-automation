@echo off
REM Script untuk menjalankan database migrations

echo ========================================
echo Running Database Migrations
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

if "%1"=="" (
    echo Running all pending migrations...
    alembic upgrade head
) else if "%1"=="create" (
    echo Creating new migration: %2
    alembic revision --autogenerate -m "%2"
) else if "%1"=="downgrade" (
    echo Downgrading migration...
    alembic downgrade -1
) else (
    echo Usage:
    echo   run_migrations.bat           - Run all pending migrations
    echo   run_migrations.bat create "message" - Create new migration
    echo   run_migrations.bat downgrade - Downgrade one migration
)
