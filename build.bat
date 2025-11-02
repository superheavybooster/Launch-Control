@echo off
echo ============================================================
echo Building StarbaseSim Launch Control
echo ============================================================
echo.

REM Create a venv for reproducible builds
if not exist ".venv" (
    python -m venv .venv
)

REM Activate venv
call .venv\Scripts\activate

REM Upgrade pip and install pinned requirements
python -m pip install --upgrade pip
pip install -r requirements.txt

echo.
echo Building executable...
echo.

REM Build the executable using the venv's pyinstaller
.venv\Scripts\pyinstaller --noconfirm --onefile --windowed ^
    --name "LaunchControl" ^
    --icon="Rocket.ico" ^
    --add-data "LaunchControl.html;." ^
    --hidden-import "websockets" ^
    --hidden-import "webview" ^
    Main.py

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
