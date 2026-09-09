@echo off
REM ============================================================
REM  JagX - Full Build + Installer Creator
REM ============================================================

echo.
echo  ========================================
echo   JagX Full Build + Installer
echo  ========================================
echo.

cd /d "%~dp0"

REM Step 1: Build the application
echo [1/2] Building JagX application...
call build_windows.bat

if not exist "dist\JagX\JagX.exe" (
    echo.
echo  ERROR: Application build failed. Cannot create installer.
pause
    exit /b 1
)

echo.
echo [2/2] Creating installer with Inno Setup...
echo.

REM Try to find Inno Setup Compiler
set ISCC=""

if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" (
    set ISCC="%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
)
if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" (
    set ISCC="%ProgramFiles%\Inno Setup 6\ISCC.exe"
)
if exist "%LocalAppData%\Programs\Inno Setup 6\ISCC.exe" (
    set ISCC="%LocalAppData%\Programs\Inno Setup 6\ISCC.exe"
)

if %ISCC%=="" (
    echo.
echo  Inno Setup is not installed.
echo.
echo  Please do the following:
echo  1. Download Inno Setup from: https://jrsoftware.org/isinfo.php
echo  2. Install it
echo  3. Run this script again   OR
echo     Open installer\JagX.iss in Inno Setup and click Build
echo.
pause
    exit /b 1
)

echo Found Inno Setup: %ISCC%
echo Compiling installer...

%ISCC% "installer\JagX.iss"

if exist "dist_installer\JagX_Setup.exe" (
    echo.
echo  ========================================
echo   SUCCESS!
echo  ========================================
echo.
echo  Installer created:
echo    dist_installer\JagX_Setup.exe
echo.
echo  You can now distribute this single file.
echo  Double-click it to install JagX on any Windows PC.
echo.
) else (
    echo.
echo  Installer compilation failed. Check the output above.
echo.
)

pause
