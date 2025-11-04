@echo off
cd /d "%~dp0"

:: Check if venv folder exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv

    :: Activate venv
    echo Activate virtual environment...
    call venv\Scripts\activate.bat
    echo Installing dependencies...
    call pip install -r ./Dot_Matrix_Panel/requirements.txt
) else (
    :: Activate venv
    echo Activate virtual environment...
    call venv\Scripts\activate.bat
)

call python launcher.py

:: Start new cmd
cmd