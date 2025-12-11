@echo off
echo ========================================
echo Running All Seeders
echo ========================================
cd /d "%~dp0.."
call venv\Scripts\activate
python scripts/seed_all.py
pause
