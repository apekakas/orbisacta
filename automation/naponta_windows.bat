@echo off
cd /d "%~dp0.."
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" orbisacta.py run >> "data\scheduler.log" 2>&1
) else (
  py orbisacta.py run >> "data\scheduler.log" 2>&1
)
