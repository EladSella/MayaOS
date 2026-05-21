@echo off
REM MayaOS Health Dashboard - Local Server Launcher

set PORT=8000
set DASHBOARD_URL=http://localhost:%PORT%/

echo Starting MayaOS Local UI Server...
REM Start the python server in the background
start /B python "%~dp0network\ui_server.py"

REM Start the Auto Git Sync in the background
start /B python "%~dp0network\auto_git.py"

REM Wait a moment for server to start
timeout /t 2 /nobreak > nul

REM Try common Chrome install locations
if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" (
    start "" "%ProgramFiles%\Google\Chrome\Application\chrome.exe" --app=%DASHBOARD_URL%
) else if exist "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" (
    start "" "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" --app=%DASHBOARD_URL%
) else if exist "%LocalAppData%\Google\Chrome\Application\chrome.exe" (
    start "" "%LocalAppData%\Google\Chrome\Application\chrome.exe" --app=%DASHBOARD_URL%
) else (
    start chrome --app=%DASHBOARD_URL%
)
