@echo off
rem ============================================================================
rem  Start Battery Test.bat
rem  This is the file the "Laptop Battery Test" Desktop shortcut points to.
rem  It runs browse.py using the private Python environment (.venv) that
rem  Setup.bat created. Do not move this file out of the project folder.
rem ============================================================================

title Laptop Battery Test
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo.
    echo  The battery test has not been set up on this computer yet.
    echo.
    echo  Please open the project folder and double-click "Setup.bat"
    echo  first. You only need to do that once.
    echo.
    pause
    exit /b 1
)

echo.
echo  Starting the battery test...
echo.
echo  A browser window will open and slowly scroll through websites
echo  on its own, over and over. That is the test working - do not
echo  touch the browser.
echo.
echo  TO STOP THE TEST: close this black window.
echo  (If the browser window stays open afterwards, close it too.)
echo.

".venv\Scripts\python.exe" browse.py

rem The test normally runs until it is stopped, so we only get here if
rem something went wrong (for example, no internet connection).
echo.
echo  The test has stopped. If you did not stop it yourself, check the
echo  internet connection and double-click the shortcut to start again.
echo.
pause
