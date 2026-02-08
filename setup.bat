@echo off
echo ================================================
echo   Multimodal Earnings Agent - Quick Setup
echo ================================================
echo.

echo [1/5] Creating virtual environment...
python -m venv venv
if %errorlevel% neq 0 (
    echo ERROR: Failed to create virtual environment
    echo Make sure Python is installed and in PATH
    pause
    exit /b 1
)

echo [2/5] Activating virtual environment...
call venv\Scripts\activate.bat

echo [3/5] Installing dependencies (this may take 2-3 minutes)...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo [4/5] Creating .env file...
if not exist .env (
    copy .env.example .env
)

echo [5/5] Creating data directories...
if not exist data\pdfs mkdir data\pdfs
if not exist outputs mkdir outputs

echo.
echo ================================================
echo   Setup Complete! 
echo ================================================
echo.
echo To run the app:
echo   1. Double-click 'run.bat'
echo   OR
echo   2. Run: streamlit run app.py
echo.
pause
