@echo off
chcp 65001 >nul
echo ==========================================
echo SVN文件搜索系统 - Windows部署脚本
echo ==========================================
echo.

set BACKEND_DIR=%~dp0backend
set FRONTEND_DIR=%~dp0frontend

:: 检查目录是否存在
if not exist "%BACKEND_DIR%" (
    echo [错误] 后端目录不存在: %BACKEND_DIR%
    exit /b 1
)

if not exist "%FRONTEND_DIR%" (
    echo [错误] 前端目录不存在: %FRONTEND_DIR%
    exit /b 1
)

echo [1/4] 正在安装后端依赖...
cd /d "%BACKEND_DIR%"
if exist "requirements.txt" (
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [错误] 后端依赖安装失败
        exit /b 1
    )
) else (
    echo [警告] 未找到requirements.txt
)

echo.
echo [2/4] 正在安装前端依赖...
cd /d "%FRONTEND_DIR%"
if exist "package.json" (
    call npm install
    if errorlevel 1 (
        echo [错误] 前端依赖安装失败
        exit /b 1
    )
) else (
    echo [警告] 未找到package.json
)

echo.
echo [3/4] 正在初始化数据库...
cd /d "%BACKEND_DIR%"
python -c "from app.models.database import Base, engine; Base.metadata.create_all(bind=engine); print('数据库初始化完成')"

echo.
echo [4/4] 正在构建前端...
cd /d "%FRONTEND_DIR%"
if exist "package.json" (
    call npm run build
    if errorlevel 1 (
        echo [警告] 前端构建失败，继续部署...
    )
)

echo.
echo ==========================================
echo [成功] 部署完成！
echo ==========================================
echo.
echo 启动命令:
echo   - 后端: cd backend ^&^& uvicorn main:app --host 0.0.0.0 --port 8001
echo   - 前端: cd frontend ^&^& npm run dev
echo.
pause
