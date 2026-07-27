@echo off
rem ============================================================================
rem  Setup.bat  -  One-time setup for the Laptop Battery Test
rem
rem  What this file does when you double-click it:
rem    1. Checks whether Python is installed (installs it automatically if not)
rem    2. Creates a private "virtual environment" folder (.venv) inside this
rem       project folder, so nothing else on the computer is touched
rem    3. Installs the software packages the test needs
rem    4. Downloads the browser used by the test
rem    5. Puts a "Laptop Battery Test" shortcut on the Desktop
rem
rem  It is safe to run this file more than once.
rem ============================================================================

setlocal
title Laptop Battery Test - First-time Setup

rem Always work from the folder this file lives in, even if Windows started us
rem somewhere else (e.g. when run from a shortcut or a network drive).
cd /d "%~dp0"

echo.
echo  ==========================================================
echo    LAPTOP BATTERY TEST  -  FIRST-TIME SETUP
echo  ==========================================================
echo.
echo  This will take a few minutes and needs an internet
echo  connection. Please leave this window open until you
echo  see "ALL DONE".
echo.

rem ----------------------------------------------------------------------------
rem  Quick internet check (just a warning, not a hard stop, because some
rem  networks block "ping" even when the internet works fine).
rem ----------------------------------------------------------------------------
ping -n 1 8.8.8.8 >nul 2>&1
if errorlevel 1 (
    echo  NOTE: We could not confirm an internet connection.
    echo  If the steps below fail, please connect to the internet
    echo  and double-click Setup.bat again.
    echo.
)

rem ============================================================================
rem  STEP 1 of 4: Find Python (or install it)
rem ============================================================================
echo  [Step 1 of 4] Checking whether Python is installed...

set "PYTHON_CMD="
call :FindPython
if defined PYTHON_CMD goto :HavePython

echo      Python is not installed yet. Installing it now
echo      (this is automatic - you may see a Windows
echo      "allow changes?" box - please click Yes)...
echo.

rem winget is Windows' built-in app installer (Windows 10/11).
where winget >nul 2>&1
if errorlevel 1 goto :NoWinget

winget install --id Python.Python.3.12 -e --accept-package-agreements --accept-source-agreements --silent
if errorlevel 1 goto :WingetFailed

rem The just-installed Python is not visible to this window yet,
rem so look for it again (including in its default install folder).
call :FindPython
if defined PYTHON_CMD goto :HavePython
goto :PythonStillMissing

:HavePython
echo      OK - Python is ready.
echo.

rem ============================================================================
rem  STEP 2 of 4: Create the private virtual environment (.venv)
rem ============================================================================
echo  [Step 2 of 4] Preparing a private workspace for the test...

if exist ".venv\Scripts\python.exe" (
    echo      Already exists - skipping.
) else (
    %PYTHON_CMD% -m venv .venv
    if errorlevel 1 goto :VenvFailed
    echo      OK - workspace created.
)
echo.

set "VENV_PY=%CD%\.venv\Scripts\python.exe"

rem ============================================================================
rem  STEP 3 of 4: Install the packages and the test browser
rem ============================================================================
echo  [Step 3 of 4] Downloading and installing the test software...
echo      (this is the slow part - please be patient)
echo.

"%VENV_PY%" -m pip install --upgrade pip --quiet --disable-pip-version-check
"%VENV_PY%" -m pip install -r requirements.txt --disable-pip-version-check
if errorlevel 1 goto :PipFailed

rem Playwright needs its own copy of the Chromium browser (~150 MB download).
"%VENV_PY%" -m playwright install chromium
if errorlevel 1 goto :BrowserFailed

echo.
echo      OK - all software installed.
echo.

rem ============================================================================
rem  STEP 4 of 4: Create the Desktop shortcut
rem ============================================================================
echo  [Step 4 of 4] Creating the "Laptop Battery Test" shortcut on your Desktop...

set "REPO_DIR=%CD%"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; $desktop=[Environment]::GetFolderPath('Desktop'); $ws=New-Object -ComObject WScript.Shell; $lnk=$ws.CreateShortcut((Join-Path $desktop 'Laptop Battery Test.lnk')); $lnk.TargetPath=(Join-Path $env:REPO_DIR 'Start Battery Test.bat'); $lnk.WorkingDirectory=$env:REPO_DIR; $lnk.Description='Runs the laptop battery browsing test'; $lnk.Save()"
if errorlevel 1 goto :ShortcutFailed

echo      OK - shortcut created.
echo.
echo  ==========================================================
echo    ALL DONE!
echo.
echo    From now on, just double-click the
echo    "Laptop Battery Test" shortcut on your Desktop
echo    to start the test. You never need to run this
echo    Setup file again on this computer.
echo  ==========================================================
echo.
pause
exit /b 0


rem ============================================================================
rem  Subroutine: FindPython
rem  Tries, in order:
rem    1. the "py" launcher            (installed with python.org Python)
rem    2. "python" on the PATH         (verified by actually running it, so the
rem                                     fake Microsoft Store stub is rejected)
rem    3. Python's default per-user install folder
rem  Sets PYTHON_CMD (already quoted if it is a file path) or leaves it empty.
rem ============================================================================
:FindPython
py -3 -c "exit()" >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_CMD=py -3"
    goto :eof
)
python -c "exit()" >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_CMD=python"
    goto :eof
)
for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python3*") do (
    if exist "%%D\python.exe" set "PYTHON_CMD="%%D\python.exe""
)
if defined PYTHON_CMD (
    %PYTHON_CMD% -c "exit()" >nul 2>&1
    if errorlevel 1 set "PYTHON_CMD="
)
goto :eof


rem ============================================================================
rem  Friendly error messages
rem ============================================================================
:NoWinget
echo.
echo  ----------------------------------------------------------
echo   SORRY - we could not install Python automatically,
echo   because this computer does not have the Windows app
echo   installer ("winget").
echo.
echo   Please do this instead:
echo     1. Open this link in your web browser:
echo          https://www.python.org/downloads/windows/
echo     2. Click the big "Download Python" button and run it.
echo        IMPORTANT: on the first screen, tick the box
echo        "Add python.exe to PATH", then click Install Now.
echo     3. When it finishes, double-click Setup.bat again.
echo  ----------------------------------------------------------
goto :Fail

:WingetFailed
echo.
echo  ----------------------------------------------------------
echo   SORRY - the automatic Python installation did not work.
echo   The most common reason is no internet connection.
echo.
echo   Please check that you are connected to the internet and
echo   double-click Setup.bat again. If it still fails, install
echo   Python yourself from:
echo          https://www.python.org/downloads/windows/
echo   (tick "Add python.exe to PATH" during install), then run
echo   Setup.bat once more.
echo  ----------------------------------------------------------
goto :Fail

:PythonStillMissing
echo.
echo  ----------------------------------------------------------
echo   Python was installed, but this window cannot see it yet.
echo   This is normal on some computers.
echo.
echo   Please simply CLOSE this window and double-click
echo   Setup.bat one more time - it will carry on from here.
echo  ----------------------------------------------------------
goto :Fail

:VenvFailed
echo.
echo  ----------------------------------------------------------
echo   SORRY - we could not create the test's private workspace
echo   folder. This can happen if the folder is read-only
echo   (for example, still inside a zip file).
echo.
echo   Make sure you UNZIPPED the folder first (right-click the
echo   downloaded zip and choose "Extract All..."), then run
echo   Setup.bat from inside the unzipped folder.
echo  ----------------------------------------------------------
goto :Fail

:PipFailed
echo.
echo  ----------------------------------------------------------
echo   SORRY - downloading the software packages failed.
echo   The most common reason is no internet connection.
echo.
echo   Please check your internet connection and double-click
echo   Setup.bat again. It will pick up where it left off.
echo  ----------------------------------------------------------
goto :Fail

:BrowserFailed
echo.
echo  ----------------------------------------------------------
echo   SORRY - downloading the test browser failed.
echo   The most common reason is no internet connection or a
echo   download that was interrupted.
echo.
echo   Please check your internet connection and double-click
echo   Setup.bat again. It will pick up where it left off.
echo  ----------------------------------------------------------
goto :Fail

:ShortcutFailed
echo.
echo  ----------------------------------------------------------
echo   Everything installed correctly, but creating the Desktop
echo   shortcut failed.
echo.
echo   You can still run the test: open this folder and
echo   double-click the file called "Start Battery Test.bat".
echo  ----------------------------------------------------------
goto :Fail

:Fail
echo.
pause
exit /b 1
