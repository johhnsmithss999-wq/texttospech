@echo off
title VoxCPM2 Telegram Voice Clone Bot
cd /d "%~dp0"

echo ========================================================
echo       VoxCPM2 Telegram Voice Clone TTS Bot
echo ========================================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH!
    pause
    exit /b
)

findstr /C:"TELEGRAM_BOT_TOKEN=" .env | findstr /V "TELEGRAM_BOT_TOKEN=$" >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] TELEGRAM_BOT_TOKEN is empty in .env file!
    echo Please open .env and paste your Telegram Bot Token from @BotFather.
    echo.
)

echo Starting Bot...
python bot.py

pause
