#!/bin/bash

# Scout Launcher Script
# This script launches Scout using the correct Python environment

echo "🔍 Launching Scout Desktop App..."
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change to the Scout root directory (parent of scripts/)
cd "$SCRIPT_DIR/.."

# Check if virtual environment exists
if [ -d ".venv" ]; then
    echo "✅ Using virtual environment: .venv"
    PYTHON_CMD=".venv/bin/python"
elif [ -d "venv" ]; then
    echo "✅ Using virtual environment: venv"
    PYTHON_CMD="venv/bin/python"
else
    echo "⚠️  No virtual environment found, using system Python"
    PYTHON_CMD="python3"
fi

# Launch Scout
echo "🚀 Starting Scout..."
echo ""

"$PYTHON_CMD" main.py

# Check exit status
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Scout closed successfully"
else
    echo ""
    echo "❌ Scout exited with an error"
    echo "Check the output above for details"
fi
