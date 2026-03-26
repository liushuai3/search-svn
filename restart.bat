@echo off
cd /d "%~dp0"
echo ==========================================
echo SVN File Search System - Windows Restart
echo ==========================================
echo.

set BACKEND_DIR=%~dp0backend
set FRONTEND_DIR=%~dp0frontend

set ENV_FILE=%~dp0frontend\.env
set BACKEND_PORT=8001
set FRONTEND_PORT=5173

if exist "%ENV_FILE%" (
    for /f "tokens=1,2 delims==" %%a in ('type "%ENV_FILE%" ^| findstr /r "^VITE_BACKEND_PORT=^FRONTEND_PORT="') do (
        if "%%a"=="VITE_BACKEND_PORT" set BACKEND_PORT=%%b
        if "%%a"=="FRONTEND_PORT" set FRONTEND_PORT=%%b
    )
)

if defined BACKEND_PORT_ENV (set BACKEND_PORT=%BACKEND_PORT_ENV%)
if defined FRONTEND_PORT_ENV (set FRONTEND_PORT=%FRONTEND_PORT_ENV%)

echo Using BACKEND_PORT=%BACKEND_PORT%
echo Using FRONTEND_PORT=%FRONTEND_PORT%

echo [1/3] Stopping existing services...

taskkill /F /IM python.exe 2>nul
taskkill /F /IM uvicorn.exe 2>nul
taskkill /F /IM node.exe 2>nul

echo [2/3] Starting backend service...
cd /d "%BACKEND_DIR%"

netstat -ano | findstr ":%BACKEND_PORT%" >nul
if %errorlevel% equ 0 (
    echo [Warning] Port %BACKEND_PORT% is in use, releasing...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%BACKEND_PORT%"') do (
        taskkill /F /PID %%a 2>nul
    )
)

start /B cmd /c "uvicorn main:app --host 0.0.0.0 --port %BACKEND_PORT% --reload > backend.log 2>&1"
echo [Success] Backend started on port %BACKEND_PORT%
echo [Info] Backend log: %BACKEND_DIR%\backend.log

echo.
echo [3/3] Starting frontend service...
cd /d "%FRONTEND_DIR%"

netstat -ano | findstr ":%FRONTEND_PORT%" >nul
if %errorlevel% equ 0 (
    echo [Warning] Port %FRONTEND_PORT% is in use, releasing...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%FRONTEND_PORT%"') do (
        taskkill /F /PID %%a 2>nul
    )
)

start /B cmd /c "npm run dev > frontend.log 2>&1"
echo [Success] Frontend started on port %FRONTEND_PORT%
echo [Info] Frontend log: %FRONTEND_DIR%\frontend.log

echo.
echo ==========================================
echo [Success] All services started!
echo ==========================================
echo.
echo Access URLs:
echo   - Frontend: http://localhost:%FRONTEND_PORT%
echo   - Backend: http://localhost:%BACKEND_PORT%
echo   - API Docs: http://localhost:%BACKEND_PORT%/docs
echo.
echo Log files:
echo   - Backend: %BACKEND_DIR%\backend.log
echo   - Frontend: %FRONTEND_DIR%\frontend.log
echo.
echo Stop services: run stop.bat
echo.
pause
