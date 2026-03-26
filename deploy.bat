@echo off
cd /d "%~dp0"
echo ==========================================
echo SVN File Search System - Windows Deploy
echo ==========================================
echo.

set BACKEND_DIR=%~dp0backend
set FRONTEND_DIR=%~dp0frontend

if not exist "%BACKEND_DIR%" (
    echo [Error] Backend directory not found: %BACKEND_DIR%
    pause
    exit /b 1
)

if not exist "%FRONTEND_DIR%" (
    echo [Error] Frontend directory not found: %FRONTEND_DIR%
    pause
    exit /b 1
)

echo [1/4] Installing backend dependencies...
cd /d "%BACKEND_DIR%"
if exist "requirements.txt" (
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [Error] Backend dependencies installation failed
        pause
        exit /b 1
    )
) else (
    echo [Warning] requirements.txt not found
)

echo.
echo [2/4] Installing frontend dependencies...
cd /d "%FRONTEND_DIR%"
if exist "package.json" (
    call npm install
    if errorlevel 1 (
        echo [Error] Frontend dependencies installation failed
        pause
        exit /b 1
    )
) else (
    echo [Warning] package.json not found
)

echo.
echo [3/4] Initializing database...
cd /d "%BACKEND_DIR%"
python -c "from app.models.database import Base, engine; Base.metadata.create_all(bind=engine); print('Database initialized')"

echo.
echo [4/4] Building frontend...
cd /d "%FRONTEND_DIR%"
if exist "package.json" (
    call npm run build
    if errorlevel 1 (
        echo [Warning] Frontend build failed, continuing...
    )
)

echo.
echo ==========================================
echo [Success] Deployment completed!
echo ==========================================
echo.
echo Start commands:
echo   - Backend: cd backend ^&^& uvicorn main:app --host 0.0.0.0 --port 8001
echo   - Frontend: cd frontend ^&^& npm run dev
echo.
pause
