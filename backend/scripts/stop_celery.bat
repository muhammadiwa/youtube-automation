@echo off
REM Script untuk menghentikan semua proses Celery di Windows

echo ========================================
echo Stopping All Celery Processes
echo ========================================
echo.

REM Kill all celery processes
echo Stopping Celery workers and beat...
taskkill /F /IM celery.exe 2>nul
if %errorlevel% equ 0 (
    echo Celery processes stopped.
) else (
    echo No celery.exe processes found.
)

REM Also kill any python processes running celery (fallback)
echo.
echo Checking for Python Celery processes...
for /f "tokens=2" %%a in ('wmic process where "commandline like '%%celery%%'" get processid 2^>nul ^| findstr /r "[0-9]"') do (
    echo Killing process %%a
    taskkill /F /PID %%a 2>nul
)

echo.
echo Done. All Celery processes should be stopped.
echo.
pause
