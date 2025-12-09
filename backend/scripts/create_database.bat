@echo off
echo ========================================
echo Creating PostgreSQL Database
echo ========================================

REM Load environment variables
for /f "tokens=1,2 delims==" %%a in ('type .env ^| findstr /v "^#"') do set %%a=%%b

echo.
echo Database Configuration:
echo - Host: %DATABASE_HOST%
echo - Port: %DATABASE_PORT%
echo - Database: %DATABASE_NAME%
echo - User: %DATABASE_USER%
echo.

echo Creating database if it doesn't exist...
psql -h %DATABASE_HOST% -p %DATABASE_PORT% -U %DATABASE_USER% -d postgres -c "CREATE DATABASE %DATABASE_NAME%;"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo Database created successfully!
    echo ========================================
) else (
    echo.
    echo Note: Database may already exist or there was an error.
    echo If the database already exists, this is normal.
    echo ========================================
)

echo.
echo You can now run migrations with: .\scripts\run_migrations.bat
pause
