@echo off
REM ============================================================
REM  JagX - Windows App Build Script
REM  Creates a standalone executable folder you can run or ship
REM ============================================================

echo.
echo  ========================================
echo   Building JagX for Windows...
echo  ========================================
echo.

REM 1. Make sure we are in the project root
cd /d "%~dp0"

REM 2. Create / activate virtual environment (recommended)
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
)
call .venv\Scripts\activate.bat

REM 3. Install / upgrade build tools + project deps
echo Installing dependencies...
pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

REM 4. Clean previous builds
if exist "dist" rmdir /s /q dist
if exist "build" rmdir /s /q build

REM 5. Build with PyInstaller
echo.
echo Running PyInstaller... This can take a few minutes.
echo.

pyinstaller --noconfirm --clean ^
    --name "JagX" ^
    --windowed ^
    --icon "NONE" ^
    --add-data "config;config" ^
    --add-data "core;core" ^
    --add-data "voice;voice" ^
    --add-data "ui;ui" ^
    --hidden-import "pystray._win32" ^
    --hidden-import "PIL._tkinter_finder" ^
    --hidden-import "edge_tts" ^
    --hidden-import "faster_whisper" ^
    --collect-all "edge_tts" ^
    --collect-all "faster_whisper" ^
    main.py

echo.
if exist "dist\JagX\JagX.exe" (
    echo  ========================================
echo   BUILD SUCCESSFUL!
echo  ========================================
echo.
echo  Your app is ready in:  dist\JagX\
echo.
echo  To run it:  double-click  dist\JagX\JagX.exe
echo.
echo  You can copy the whole "JagX" folder anywhere
echo  or create a shortcut to JagX.exe.
echo.
) else (
    echo  BUILD FAILED - check the errors above.
)

pause
