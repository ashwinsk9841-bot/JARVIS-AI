@echo off
setlocal

REM ============================================================
REM  JARVIS — Windows packaging build script (PyInstaller)
REM
REM  Release: builds single-file dist\JARVIS\JARVIS.exe (no console)
REM           and assembles the external runtime resources next to it.
REM  Debug:   set JARVIS_DEBUG=1 to build dist\JARVIS-DEBUG\ (console logs)
REM
REM  Build tool is isolated in the project's own Python 3.13 venv.
REM  No JARVIS source code is modified by this script.
REM ============================================================

set "PROJ=C:\JARVIS PERSON AGENT\jarvis-main\jarvis-main"
set "PY=C:\JARVIS PERSON AGENT\venv\Scripts\python.exe"

if not exist "%PY%" (
    echo [JARVIS] ERROR: venv python not found: "%PY%"
    exit /b 1
)

echo [JARVIS] Cleaning previous build artifacts...
if exist "%PROJ%\build"  rmdir /S /Q "%PROJ%\build"
if exist "%PROJ%\dist"   rmdir /S /Q "%PROJ%\dist"

echo [JARVIS] Running PyInstaller (JARVIS.spec)...
pushd "%PROJ%"
"%PY%" -m PyInstaller --noconfirm "%PROJ%\JARVIS.spec"
set "RC=%ERRORLEVEL%"
popd
if not "%RC%"=="0" (
    echo [JARVIS] BUILD FAILED
    exit /b 1
)

if defined JARVIS_DEBUG goto release

REM ---- assemble external runtime resources next to the one-file exe ----
set "DIST=%PROJ%\dist"
if exist "%DIST%\JARVIS.exe" (
    echo [JARVIS] Assembling external runtime resources next to the exe...

    if not exist "%DIST%\config" mkdir "%DIST%\config"
    if exist "%PROJ%\config\api_keys.json"        xcopy /Y /I "%PROJ%\config\api_keys.json"        "%DIST%\config\" >nul
    if exist "%PROJ%\config\api_keys.json.example" xcopy /Y /I "%PROJ%\config\api_keys.json.example" "%DIST%\config\" >nul
    if exist "%PROJ%\config\certs"                xcopy /E /Y /I "%PROJ%\config\certs"            "%DIST%\config\certs\" >nul

    if not exist "%DIST%\core" mkdir "%DIST%\core"
    if exist "%PROJ%\core\prompt.txt" xcopy /Y /I "%PROJ%\core\prompt.txt" "%DIST%\core\" >nul

    if not exist "%DIST%\memory" mkdir "%DIST%\memory"
    if exist "%PROJ%\memory\long_term.json" xcopy /Y /I "%PROJ%\memory\long_term.json" "%DIST%\memory\" >nul

    if exist "%PROJ%\face.png" xcopy /Y /I "%PROJ%\face.png" "%DIST%\" >nul
)

echo.
echo ============================================================
echo  JARVIS.EXE: %PROJ%\dist\JARVIS.exe
echo ============================================================
goto :eof

:release
echo.
echo ============================================================
echo  DEBUG EXE: %PROJ%\dist\JARVIS-DEBUG\JARVIS-DEBUG.exe
echo ============================================================

endlocal