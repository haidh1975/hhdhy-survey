@echo off
chcp 65001 >nul
echo ============================================
echo   Khoi dong ung dung Khao sat Hung Yen
echo ============================================
echo.

:: Kiem tra Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [LOI] Khong tim thay Python. Vui long cai dat Python 3.11+
    pause
    exit /b 1
)

:: Cai dat thu vien neu chua co
if not exist ".venv" (
    echo Tao moi truong ao Python...
    python -m venv .venv
)

:: Kich hoat moi truong ao
call .venv\Scripts\activate.bat

:: Cai dat thu vien
echo Cai dat cac thu vien can thiet...
pip install -r requirements.txt --quiet

:: Tao thu muc data neu chua co
if not exist "data" mkdir data

:: Khoi dong ung dung
echo.
echo [OK] Khoi dong ung dung tai: http://localhost:5000
echo [OK] Nhan Ctrl+C de dung ung dung
echo.
streamlit run app.py --server.port 5000 --server.address localhost

pause
