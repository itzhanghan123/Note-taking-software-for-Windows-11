@echo off
setlocal
cd /d "%~dp0"
title DeskMemo14 Calendar Toolbar Polish Build
where py >nul 2>nul
if not errorlevel 1 (
  set "PY=py -3"
  goto pyok
)
where python >nul 2>nul
if not errorlevel 1 (
  set "PY=python"
  goto pyok
)
echo Python 3.11+ was not found. Install from https://www.python.org/downloads/windows/
pause
exit /b 1
:pyok
%PY% -m pip install --upgrade PySide6 pyinstaller
if errorlevel 1 (
  echo Dependency installation failed. Check internet.
  pause
  exit /b 1
)
%PY% -m PyInstaller --noconfirm --clean --onefile --windowed --name DeskMemo14_CalendarToolbar_Polish app.py
if errorlevel 1 (
  echo Build failed. Read the error above.
  pause
  exit /b 1
)
echo Build complete: dist\DeskMemo14_CalendarToolbar_Polish.exe
start "" explorer "%~dp0dist"
pause
