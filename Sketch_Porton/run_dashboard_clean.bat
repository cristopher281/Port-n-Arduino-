@echo off
REM run_dashboard_clean.bat - Activa venv, instala deps e inicia dashboard.py
cd /d "%~dp0"

REM Activar virtualenv si existe
if exist "venv\Scripts\activate.bat" (
    echo Activando entorno virtual venv...
    call "venv\Scripts\activate.bat"
) else (
    echo No se detecto entorno virtual local (venv). Se usara Python del sistema.
@echo off

