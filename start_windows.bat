@echo off
setlocal
cd /d "%~dp0"

if not "%~1"=="" set "UNICAREER_PORT=%~1"

py -3 --version >nul 2>nul
if not errorlevel 1 (
  set "PY=py -3"
  goto run
)

python --version >nul 2>nul
if not errorlevel 1 (
  set "PY=python"
  goto run
)

echo.
echo Python 3 was not found.
echo Install Python 3 from https://www.python.org/downloads/windows/
echo During installation, enable "Add python.exe to PATH".
echo.
pause
exit /b 1

:run
if "%UNICAREER_PORT%"=="" set "UNICAREER_PORT=8000"
echo.
echo UniCareer is starting...
echo Open http://localhost:%UNICAREER_PORT% in your browser.
echo Press Ctrl+C or close this window to stop.
echo.
%PY% server.py
echo.
echo Server stopped.
pause
