#!/usr/bin/env fish

# Shell detection
set DETECTED_SHELL (basename $SHELL)
echo "Detected shell: $DETECTED_SHELL"

# Create virtual environment
python3 -m venv venv; or begin
    echo "Failed to create virtual environment"
    exit 1
end

# Write activation scripts
printf '%s\n' '#!/usr/bin/env fish' \
    'source venv/bin/activate.fish' \
    'set -x PYTHONPATH (pwd)' \
    'dataset-tools $argv' > activate.fish

printf '%s\n' '#!/bin/bash' \
    'source venv/bin/activate' \
    'export PYTHONPATH="$(pwd)"' \
    'dataset-tools "$@"' > activate.bash

printf '%s\n' '#!/bin/zsh' \
    'source venv/bin/activate' \
    'export PYTHONPATH="$(pwd)"' \
    'dataset-tools "$@"' > activate.zsh

# Make scripts executable
chmod +x activate.fish activate.bash activate.zsh

# Install dependencies
source venv/bin/activate.fish
pip install --upgrade pip
pip install .

echo "Installation complete!"
echo "You can run Dataset-Tools using:"
echo "  ./activate.fish - For Fish shell"
echo "  ./activate.bash - For Bash shell"
echo "  ./activate.zsh  - For Zsh shell"