@echo off
title YouTube Planner - Bouwen naar .exe
echo.
echo Controleren of Python beschikbaar is...
python --version >nul 2>&1
if errorlevel 1 (
    echo FOUT: Python is niet gevonden.
    echo Installeer Python via https://www.python.org/downloads/
    echo Zorg dat u "Add Python to PATH" aanvinkt tijdens installatie.
    echo.
    pause
    exit /b 1
)
echo Python gevonden. Bouwen starten...
echo.
python build.py
