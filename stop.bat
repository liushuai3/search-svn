@echo off
cd /d "%~dp0"
echo ==========================================
echo SVN File Search System - Windows Stop
echo ==========================================
echo.

echo [1/3] Stopping backend service...
taskkill /F /IM python.exe 2>nul
taskkill /F /IM uvicorn.exe 2>nul
echo [Success] Backend stopped

echo.
echo [2/3] Stopping frontend service...
taskkill /F /IM node.exe 2>nul
echo [Success] Frontend stopped

echo.
echo [3/3] Cleaning up port usage...

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

for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%BACKEND_PORT%"') do (
    taskkill /F /PID %%a 2>nul
)

for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%FRONTEND_PORT%"') do (
    taskkill /F /PID %%a 2>nul
)

echo [Success] Ports released

echo.
echo ==========================================
echo [Success] All services stopped!
echo ==========================================
echo.
pause
