@echo off
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Lege virtuelle Umgebung an ...
    python -m venv .venv || goto :error
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt || goto :error
)

start "" ".venv\Scripts\pythonw.exe" -m easy_cutter %*
exit /b 0

:error
echo Einrichtung fehlgeschlagen.
pause
exit /b 1
