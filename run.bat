@echo off
echo Starting Dataset-Tools...

rem Check if the local venv exists
if exist "venv\Scripts\activate.bat" (
    rem If it exists, use it
    call venv\Scripts\activate.bat
) else (
    rem If not, assume the tool is installed globally
    echo.
    echo INFO: 'venv' not found. Trying to run globally.
    echo If this fails, please run the install.bat script first.
    echo.
)

rem Launch the tool
dataset-tools

pause