@echo off
cd /d "%~dp0"
if "%~1"=="" (
    start "" pythonw "%~dp0app.py"
) else (
    start "" pythonw "%~dp0app.py" "%~1"
)
