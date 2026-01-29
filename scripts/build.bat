@echo off
REM Scout Build Script for Windows
REM This script builds a standalone executable for Windows

echo.
echo Scout Build Script
echo ====================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed. Please install Python 3.9 or higher.
    exit /b 1
)

echo Python found: 
python --version
echo.

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

if errorlevel 1 (
    echo Error: Failed to install dependencies
    exit /b 1
)

echo Dependencies installed
echo.

REM Install PyInstaller
echo Installing PyInstaller...
pip install pyinstaller

if errorlevel 1 (
    echo Error: Failed to install PyInstaller
    exit /b 1
)

echo PyInstaller installed
echo.

REM Build executable
echo Building Scout executable...

if exist "assets\icon.ico" (
    echo Using custom icon...
    pyinstaller --onefile --windowed --name Scout --icon=assets\icon.ico main.py
) else (
    echo No custom icon found, building without icon...
    pyinstaller --onefile --windowed --name Scout main.py
)

if errorlevel 1 (
    echo Error: Build failed
    exit /b 1
)

echo.
echo Build complete!
echo.
echo Executable location: dist\Scout.exe
echo.
echo To run Scout:
echo   dist\Scout.exe
echo.

pause
