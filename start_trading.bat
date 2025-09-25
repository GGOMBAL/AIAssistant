@echo off
echo ========================================
echo    Auto Trade System Launcher
echo ========================================
echo.

REM 가상환경 활성화 (있는 경우)
REM call venv\Scripts\activate

echo Starting Auto Trade System...
echo.

REM Python 실행
python main_auto_trade.py

echo.
echo System stopped. Press any key to exit...
pause >nul