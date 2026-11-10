@echo off
title AI Knowledge Assistant - Restart Manager
color 0B

echo ==============================================================================
echo        AI KNOWLEDGE ASSISTANT - RESTARTING SERVICES
echo ==============================================================================
echo.

where docker >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Docker command not found on PATH.
    pause
    exit /b 1
)

echo [INFO] Stopping containers...
docker compose down

echo.
echo [INFO] Restarting containers in detached mode...
docker compose up -d

if %ERRORLEVEL% equ 0 (
    color 0A
    echo.
    echo [OK] All services restarted successfully!
    echo - Web Application: http://localhost:8501
    echo - Backend API:     http://localhost:8000/docs
) else (
    color 0C
    echo.
    echo [ERROR] Failed to restart services.
)

echo.
pause
