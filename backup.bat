@echo off
setlocal enabledelayedexpansion
title AI Knowledge Assistant - Backup Utility
color 0B

echo ==============================================================================
echo        AI KNOWLEDGE ASSISTANT - DATABASE & VECTOR STORE BACKUP
echo ==============================================================================
echo.

where docker >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Docker command not found on PATH.
    pause
    exit /b 1
)

:: Get current timestamp for unique backup folder name (YYYY-MM-DD_HH-MM-SS)
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value 2^>nul') do set dt=%%I
if defined dt (
    set TIMESTAMP=!dt:~0,4!-!dt:~4,2!-!dt:~6,2!_!dt:~8,2!-!dt:~10,2!-!dt:~12,2!
) else (
    set TIMESTAMP=%date:~-4%-%date:~4,2%-%date:~7,2%_%time:~0,2%-%time:~3,2%-%time:~6,2%
    set TIMESTAMP=!TIMESTAMP: =0!
)

set BACKUP_DIR=backups\backup_!TIMESTAMP!

echo [INFO] Creating backup destination directory: %BACKUP_DIR%
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"

echo.
echo [1/3] Backing up SQLite relational database volume (rag_sqlite_data)...
docker run --rm -v rag_sqlite_data:/source:ro -v "%cd%\%BACKUP_DIR%":/dest alpine sh -c "cp -rf /source/* /dest/ 2>/dev/null || true"

echo [2/3] Backing up ChromaDB vector store volume (rag_chroma_data)...
docker run --rm -v rag_chroma_data:/source:ro -v "%cd%\%BACKUP_DIR%":/dest alpine sh -c "mkdir -p /dest/chroma_data && cp -rf /source/* /dest/chroma_data/ 2>/dev/null || true"

echo [3/3] Backing up local configuration (.env)...
if exist .env (
    copy .env "%BACKUP_DIR%\.env.bak" >nul
    echo [OK] Configuration saved.
)

color 0A
echo.
echo ==============================================================================
echo [SUCCESS] Backup completed successfully!
echo Destination: %BACKUP_DIR%
echo ==============================================================================
echo.
pause
