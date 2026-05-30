@echo off
chcp 65001 >nul
echo ==========================================
echo    Ying Er Ku Sheng Yi Tu Li Jie Qi - Qi Dong Jiao Ben
echo ==========================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.8+
    pause
    exit /b 1
)

echo [OK] Python installed

REM Check virtual environment
if not exist "venv" (
    echo [INFO] Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
)

echo [OK] Virtual environment ready

REM Activate virtual environment
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo [INFO] Installing dependencies...
pip install -q -r requirements.txt
if errorlevel 1 (
    echo [WARNING] Some dependencies failed to install, but continuing...
)

echo [OK] Dependencies installed

REM Check .env file
if not exist ".env" (
    echo [WARNING] .env file not found
    echo [INFO] Creating .env template from .env.example
    copy .env.example .env
    echo [INFO] Please edit .env and add your DeepSeek API Key, then restart
    notepad .env
    pause
    exit /b 1
)

echo [OK] Config file exists

REM Start application
echo.
echo [LAUNCH] Starting Ying Er Ku Sheng Yi Tu Li Jie Qi...
echo [INFO] The app will open in your browser
streamlit run app.py

pause
