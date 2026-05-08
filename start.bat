@echo off
title YouTube Livestream Planner
python --version >nul 2>&1
if errorlevel 1 (
    echo Python niet gevonden. Installeer Python via https://www.python.org/downloads/
    pause
    exit /b 1
)
python main.py
