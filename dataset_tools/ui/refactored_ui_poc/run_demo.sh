#!/bin/bash
# Quick launcher for the refactored UI POC demo
# This handles the virtual environment automatically

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Navigate to project root (5 levels up from this script)
PROJECT_ROOT="$SCRIPT_DIR/../../../../.."

cd "$PROJECT_ROOT"

echo "Running Refactored UI POC Demo..."
echo "Using Python from: .venv/bin/python"
echo ""

# Use the project's virtual environment Python
.venv/bin/python dataset_tools/ui/refactored_ui_poc/demo.py
