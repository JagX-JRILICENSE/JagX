@echo off
REM ============================================================
REM  JagX Premium Windows Build
REM  JRILICENSE
REM ============================================================

echo.
echo  ========================================
echo   Building JagX Premium for Windows
echo  ========================================
echo.

cd /d "%~dp0"

if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
)
call .venv\Scripts\activate.bat

echo Installing dependencies...
pip install --upgrade pip >nul
pip install -r requirements.txt
pip install pyinstaller pillow pystray

REM Generate jaguar icon for exe + tray
echo Generating jaguar icon...
python -c "from ui.tray import create_jaguar_icon; img=create_jaguar_icon(256); img.save('jagx_icon.png'); img.save('jagx_icon.ico', format='ICO', sizes=[(256,256),(128,128),(64,64),(32,32),(16,16)]); print('icon ok')" 2>nul
if not exist "jagx_icon.ico" (
    echo Icon generation skipped - continuing without custom ico
)

if exist "dist" rmdir /s /q dist
if exist "build" rmdir /s /q build

echo.
echo Running PyInstaller...
echo.

if exist "jagx_icon.ico" (
    set ICON_FLAG=--icon jagx_icon.ico
) else (
    set ICON_FLAG=
)

pyinstaller --noconfirm --clean ^
    --name "JagX" ^
    --windowed ^
    %ICON_FLAG% ^
    --add-data "config;config" ^
    --hidden-import "pystray._win32" ^
    --hidden-import "PIL._tkinter_finder" ^
    --hidden-import "edge_tts" ^
    --hidden-import "keyring.backends.Windows" ^
    --collect-all "edge_tts" ^
    --collect-submodules "core" ^
    --collect-submodules "ui" ^
    --collect-submodules "voice" ^
    main.py

echo.
if exist "dist\JagX\JagX.exe" (
    echo  ========================================
echo   BUILD SUCCESSFUL
echo  ========================================
echo.
echo  Run:  dist\JagX\JagX.exe
echo  You should see the orange jaguar in the system tray.
echo  Close the window to keep JagX in the tray.
echo.
) else if exist "dist\JagX.exe" (
    echo  ========================================
echo   BUILD SUCCESSFUL (one-file style)
echo  ========================================
echo  Run: dist\JagX.exe
echo.
) else (
    echo  BUILD FAILED - read errors above.
)

pause
