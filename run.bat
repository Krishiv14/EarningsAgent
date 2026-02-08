@echo off
echo ================================================
echo   Starting Multimodal Earnings Agent...
echo ================================================
echo.

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Run Streamlit
echo Starting Streamlit server...
echo Browser should open automatically at http://localhost:8501
echo.
echo Press Ctrl+C to stop the server
echo.

streamlit run app.py

pause
