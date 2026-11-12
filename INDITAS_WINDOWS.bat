@echo off
chcp 65001 >nul
cd /d "%~dp0"
where py >nul 2>&1
if errorlevel 1 (
 echo Python Launcher not found. Install Python 3.11+ from python.org.
 pause
 exit /b 1
)
if not exist ".venv\Scripts\python.exe" py -m venv .venv
call ".venv\Scripts\activate.bat"
python -m pip install -r requirements.txt
if errorlevel 1 (
 echo Dependency installation failed.
 pause
 exit /b 1
)
python orbisacta.py run
start "" "http://127.0.0.1:8000"
python orbisacta.py serve
pause
