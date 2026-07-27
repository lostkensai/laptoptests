@echo off
rem ============================================================================
rem  Build EXE.bat  -  Builds "Laptop Battery Test.exe" on a Windows computer
rem
rem  Run this on Windows (double-click it). It will:
rem    1. Find Python (3.10 - 3.12 recommended)
rem    2. Create a separate build environment (.venv-build)
rem    3. Install Playwright + PyInstaller
rem    4. Download Chromium INTO the Playwright package so it gets bundled
rem    5. Compile everything into:  dist\Laptop Battery Test\
rem
rem  The finished product is the WHOLE "dist\Laptop Battery Test" folder
rem  (zip it and send it). The exe inside it does not need Python installed.
rem
rem  See BUILD-EXE-PLAN.md for the full explanation and troubleshooting.
rem ============================================================================

setlocal
title Build Laptop Battery Test EXE
cd /d "%~dp0"

echo.
echo  ==========================================================
echo    BUILDING "Laptop Battery Test.exe"
echo    This needs internet and can take 5-15 minutes.
echo  ==========================================================
echo.

rem ---- Step 1: find Python -------------------------------------------------
set "PY="
py -3 -c "exit()" >nul 2>&1
if not errorlevel 1 set "PY=py -3"
if not defined PY (
    python -c "exit()" >nul 2>&1
    if not errorlevel 1 set "PY=python"
)
if not defined PY (
    echo  ERROR: Python was not found on this computer.
    echo  Install it from https://www.python.org/downloads/windows/
    echo  ^(tick "Add python.exe to PATH" during install^), then run
    echo  this file again.
    echo.
    pause
    exit /b 1
)
echo  [1/4] Using Python: %PY%

rem ---- Step 2: fresh build environment ------------------------------------
echo  [2/4] Creating the build environment (.venv-build)...
if not exist ".venv-build\Scripts\python.exe" (
    %PY% -m venv .venv-build
    if errorlevel 1 goto :BuildFailed
)
set "VPY=%CD%\.venv-build\Scripts\python.exe"

"%VPY%" -m pip install --upgrade pip --quiet --disable-pip-version-check
"%VPY%" -m pip install playwright pyinstaller --disable-pip-version-check
if errorlevel 1 goto :BuildFailed

rem ---- Step 3: put Chromium inside the package so it gets bundled ----------
echo  [3/4] Downloading Chromium into the package (~150 MB)...
set "PLAYWRIGHT_BROWSERS_PATH=0"
"%VPY%" -m playwright install chromium
if errorlevel 1 goto :BuildFailed

rem ---- Step 4: compile ------------------------------------------------------
echo  [4/4] Compiling the exe (this is the slow part)...
"%VPY%" -m PyInstaller --noconfirm --clean --onedir ^
    --name "Laptop Battery Test" ^
    --collect-all playwright ^
    browse.py
if errorlevel 1 goto :BuildFailed

echo.
echo  ==========================================================
echo    SUCCESS!
echo.
echo    Your build is in:   dist\Laptop Battery Test\
echo.
echo    To give it to someone: right-click that folder,
echo    "Compress to ZIP file", and send them the zip.
echo    They unzip it and double-click
echo    "Laptop Battery Test.exe" - nothing to install.
echo  ==========================================================
echo.
pause
exit /b 0

:BuildFailed
echo.
echo  ----------------------------------------------------------
echo   The build failed. Common fixes:
echo     - Check the internet connection and run this again.
echo     - Delete the ".venv-build", "build" and "dist" folders
echo       and run this file again for a clean build.
echo     - If antivirus interrupted the build, add this folder
echo       to its exclusions and retry.
echo   The error details are printed above this message.
echo  ----------------------------------------------------------
echo.
pause
exit /b 1
