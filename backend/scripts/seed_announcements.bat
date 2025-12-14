@echo off
echo Seeding announcements...
cd /d "%~dp0.."
call venv\Scripts\activate
python scripts/seed_announcements.py
echo Done!
pause
