#!/bin/bash
echo "Starting Dataset-Tools..."

# Check if the local venv exists
if [ -f "venv/bin/activate" ]; then
    # If it exists, use it
    source venv/bin/activate
else
    # If not, assume the tool is installed globally
    echo ""
    echo "INFO: 'venv' not found. Trying to run globally."
    echo "If this fails, please run the install.sh script first."
    echo ""
fi

# Launch the tool
dataset-tools