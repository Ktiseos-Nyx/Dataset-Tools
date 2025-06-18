#!/bin/zsh
source venv/bin/activate
export PYTHONPATH="$(pwd)"
dataset-tools "$@"
