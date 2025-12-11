@echo off
cd /d "%~dp0.."
call venv\Scripts\activate
python scripts/seed_moderation_rules.py
pause
