@echo off
echo Seeding default plans...
cd /d "%~dp0\.."
call venv\Scripts\activate
python scripts/seed_plans.py
echo Done!
pause
