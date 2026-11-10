@echo off
setlocal enabledelayedexpansion
title AI Knowledge Assistant - Startup Manager
color 0A

echo ==============================================================================
echo        AI KNOWLEDGE ASSISTANT - DOCKER STARTUP
echo ==============================================================================
echo.

:: 1. Check if Docker command exists
where docker >nul 2>&1
if %ERRORLEVEL% neq 0 (
    color 0C
    echo [ERROR] Docker command not found on PATH!
    echo.
    echo Please install Docker Desktop for Windows:
    echo https://www.docker.com/products/docker-desktop/
    echo.
    echo After installing, restart Docker Desktop and run this script again.
    echo.
    pause
    exit /b 1
)

:: 2. Check if Docker Engine daemon is actively running
docker info >nul 2>&1
if %ERRORLEVEL% neq 0 (
    color 0E
    echo [WARNING] Docker is installed but Docker Desktop / Docker Engine is not running.
    echo.
    echo Attempting to start Docker Desktop...
    start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe" >nul 2>&1
    echo Waiting for Docker daemon to become responsive (up to 45 seconds)...
    
    set /a attempts=0
    :WAIT_DOCKER
    timeout /t 3 /nobreak >nul
    docker info >nul 2>&1
    if %ERRORLEVEL% equ 0 goto DOCKER_READY
    set /a attempts+=1
    if !attempts! lss 15 goto WAIT_DOCKER

    color 0C
    echo [ERROR] Docker daemon did not respond. Please launch Docker Desktop manually
    echo and wait for the engine status icon to turn green.
    echo.
    pause
    exit /b 1
)

:DOCKER_READY
color 0A
echo [OK] Docker Engine is running.
echo.

:: 3. Check for .env file; initialize from .env.example if missing
if not exist .env (
    if exist .env.example (
        echo [INFO] No .env file detected. Creating default .env from .env.example...
        copy .env.example .env >nul
        echo [OK] .env initialized successfully.
    ) else (
        echo [WARNING] Neither .env nor .env.example found. Default container settings will apply.
    )
)

:: 4. Start Docker Compose services in detached background mode
echo [INFO] Launching AI Knowledge Assistant containers...
docker compose up -d

if %ERRORLEVEL% neq 0 (
    color 0C
    echo.
    echo [ERROR] Failed to start Docker Compose services!
    echo Check logs using: docker compose logs
    echo.
    pause
    exit /b 1
)

echo.
echo ==============================================================================
echo [SUCCESS] AI Knowledge Assistant is running!
echo.
echo - Web Application:   http://localhost:8501
echo - Backend API Docs:  http://localhost:8000/docs
echo - System Health:     http://localhost:8000/health
echo ==============================================================================
echo.
echo Waiting 5 seconds for application initialization before opening browser...
timeout /t 5 /nobreak >nul

:: 5. Open Streamlit frontend in default web browser
start http://localhost:8501

echo.
echo Useful management commands:
echo - Stop services:     stop.bat
echo - Restart services:  restart.bat
echo - Backup database:   backup.bat
echo - View live logs:    docker compose logs -f
echo.
pause
