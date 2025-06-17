#!/bin/bash
echo "=============================================================="
echo " Welcome to the Dataset-Tools Installer for macOS & Linux!"
echo "=============================================================="
echo ""
echo "This script will set up a dedicated 'venv' folder for this"
echo "application. This is the recommended way to install to"
echo "avoid conflicts with other Python software."
echo ""
read -p "Do you want to proceed with the standard installation? (Y/n): " choice
case "$choice" in 
  n|N ) 
    echo ""
    echo "Installation cancelled."
    echo "For advanced installation, please see the README.md file."
    exit 0
    ;;
  * ) 
    ;;
esac

echo ""
echo "[1/3] Creating Python virtual environment in 'venv'..."
python3 -m venv venv
if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: Could not create the virtual environment."
    echo "Please make sure Python 3.10+ is installed."
    exit 1
fi

echo ""
echo "[2/3] Installing Dataset-Tools and its dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install .
if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: Installation failed. Please check your internet connection."
    exit 1
fi

echo ""
echo "[3/3] Success!"
echo "=============================================================="
echo ""
echo "You can now run the application at any time by"
echo "running the './run.sh' script from your terminal."
echo ""