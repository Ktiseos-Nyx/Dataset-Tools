@echo off
echo ==============================================================
echo  Welcome to the Dataset-Tools Installer for Windows!
echo ==============================================================
echo.
echo This script will set up a dedicated 'venv' folder for this
echo application. This is the recommended way to install to
echo avoid conflicts with other Python software.
echo.
set /p "choice=Do you want to proceed with the standard installation? (Y/n): "
if /i not "%choice%"=="Y" if /i not "%choice%"=="" (
    echo.
    echo Installation cancelled.
    echo For advanced installation, please see the README.md file.
    pause
    exit /b
)

echo.
echo [1/3] Creating Python virtual environment in 'venv'...
python -m venv venv
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Could not create the virtual environment.
    echo Please make sure Python 3.10+ is installed and the
    echo "Add Python to PATH" option was checked during installation.
    pause
    exit /b
)

echo.
echo [2/3] Installing Dataset-Tools and its dependencies...
call venv\Scripts\activate.bat
pip install --upgrade pip
pip install .
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Installation failed. Please check your internet connection.
    pause
    exit /b
)

echo.
echo [3/3] Success!
echo ==============================================================
echo.
echo You can now run the application at any time by
echo double-clicking the 'run.bat' file in this folder.
echo.
pause