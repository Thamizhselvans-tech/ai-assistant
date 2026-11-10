@echo off
title AI Knowledge Assistant - Shutdown Manager
color 0E

echo ==============================================================================
echo        AI KNOWLEDGE ASSISTANT - STOPPING SERVICES
echo ==============================================================================
echo.

where docker >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Docker command not found on PATH.
    pause
    exit /b 1
)

echo [INFO] Gracefully stopping and removing containers...
docker compose down

if %ERRORLEVEL% equ 0 (
    color 0A
    echo.
    echo [OK] All AI Knowledge Assistant services stopped gracefully.
    echo Data volumes (SQLite database, ChromaDB vector store) remain safely preserved.
) else (
    color 0C
    echo.
    echo [ERROR] Encountered an issue stopping containers.
)

echo.
pause
