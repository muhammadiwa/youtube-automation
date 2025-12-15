@echo off
echo ========================================
echo Seeding Compliance Data
echo ========================================
cd /d "%~dp0.."
call venv\Scripts\activate
python scripts/seed_compliance.py
pause
