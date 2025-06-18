#!/usr/bin/env fish
source venv/bin/activate.fish
set -x PYTHONPATH (pwd)
dataset-tools $argv
