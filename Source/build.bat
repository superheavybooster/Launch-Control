@echo off
echo ============================================================
echo Building StarbaseSim Launch Control
echo ============================================================
echo.

REM Check if pyinstaller is installed
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo PyInstaller not found. Installing...
    pip install pyinstaller
)

REM Check if pywebview is installed
python -c "import webview" 2>nul
if errorlevel 1 (
    echo PyWebView not found. Installing...
    pip install pywebview
)

REM Check if websockets is installed
python -c "import websockets" 2>nul
if errorlevel 1 (
    echo websockets not found. Installing...
    pip install websockets
)

echo.
echo Building executable...
echo.

REM Build the executable
pyinstaller --noconfirm --onefile --windowed ^
    --name "LaunchControl" ^
    --icon="Rocket.ico" ^
    --add-data "LaunchControl.html;." ^
    --hidden-import "websockets" ^
    --hidden-import "webview" ^
    --hidden-import "asyncio" ^
    main.py

echo.
echo ============================================================
echo Build complete!
echo ============================================================
echo.
echo Your executable is in the 'dist' folder:
echo   dist\LaunchControl.exe
echo.
echo You can now:
echo   1. Copy LaunchControl.exe anywhere you want
echo   2. Run it directly (no Python needed!)
echo   3. Make sure StarbaseSim game is running first
echo.
echo Note: The .exe is about 15-30MB and includes everything!
echo ============================================================
pause
