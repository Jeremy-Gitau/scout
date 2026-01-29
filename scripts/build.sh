#!/bin/bash

# Scout Build Script for macOS/Linux
# This script builds a standalone executable for the current platform

echo "🔍 Scout Build Script"
echo "===================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.9 or higher."
    exit 1
fi

echo "✓ Python found: $(python3 --version)"

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed."
    exit 1
fi

echo "✓ pip3 found"
echo ""

# Install dependencies
echo "📦 Installing dependencies..."
pip3 install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo "✓ Dependencies installed"
echo ""

# Install PyInstaller
echo "📦 Installing PyInstaller..."
pip3 install pyinstaller

if [ $? -ne 0 ]; then
    echo "❌ Failed to install PyInstaller"
    exit 1
fi

echo "✓ PyInstaller installed"
echo ""

# Build executable
echo "🔨 Building Scout executable..."

if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    echo "Platform: macOS"
    
    if [ -f "assets/icon.icns" ]; then
        echo "Using custom icon..."
        pyinstaller --onefile --windowed --name Scout --icon=assets/icon.icns main.py
    else
        echo "No custom icon found, building without icon..."
        pyinstaller --onefile --windowed --name Scout main.py
    fi
else
    # Linux
    echo "Platform: Linux"
    pyinstaller --onefile --name Scout main.py
fi

if [ $? -ne 0 ]; then
    echo "❌ Build failed"
    exit 1
fi

echo ""
echo "✅ Build complete!"
echo ""
echo "📁 Executable location: dist/Scout"
echo ""
echo "To run Scout:"
echo "  ./dist/Scout"
echo ""
echo "To install system-wide (optional):"
echo "  sudo cp dist/Scout /usr/local/bin/"
echo ""
