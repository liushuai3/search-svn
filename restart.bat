@echo off
chcp 65001 >nul
echo ==========================================
echo SVN文件搜索系统 - Windows重启脚本
echo ==========================================
echo.

set BACKEND_DIR=%~dp0backend
set FRONTEND_DIR=%~dp0frontend
set BACKEND_PORT=8001
set FRONTEND_PORT=5173

echo [1/3] 正在停止现有服务...

:: 停止Python/uvicorn进程
taskkill /F /IM python.exe 2>nul
taskkill /F /IM uvicorn.exe 2>nul

:: 停止Node进程（前端）
taskkill /F /IM node.exe 2>nul

echo [2/3] 正在启动后端服务...
cd /d "%BACKEND_DIR%"

:: 检查端口是否被占用
netstat -ano | findstr ":%BACKEND_PORT%" >nul
if %errorlevel% equ 0 (
    echo [警告] 端口 %BACKEND_PORT% 已被占用，尝试释放...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%BACKEND_PORT%"') do (
        taskkill /F /PID %%a 2>nul
    )
)

:: 启动后端（后台运行）
start /B cmd /c "uvicorn main:app --host 0.0.0.0 --port %BACKEND_PORT% --reload > backend.log 2>&1"
if errorlevel 1 (
    echo [错误] 后端启动失败
    exit /b 1
)
echo [成功] 后端服务已启动，端口: %BACKEND_PORT%
echo [信息] 后端日志: %BACKEND_DIR%\backend.log

echo.
echo [3/3] 正在启动前端服务...
cd /d "%FRONTEND_DIR%"

:: 检查端口是否被占用
netstat -ano | findstr ":%FRONTEND_PORT%" >nul
if %errorlevel% equ 0 (
    echo [警告] 端口 %FRONTEND_PORT% 已被占用，尝试释放...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%FRONTEND_PORT%"') do (
        taskkill /F /PID %%a 2>nul
    )
)

:: 启动前端（后台运行）
start /B cmd /c "npm run dev > frontend.log 2>&1"
if errorlevel 1 (
    echo [错误] 前端启动失败
    exit /b 1
)
echo [成功] 前端服务已启动，端口: %FRONTEND_PORT%
echo [信息] 前端日志: %FRONTEND_DIR%\frontend.log

echo.
echo ==========================================
echo [成功] 所有服务已启动！
echo ==========================================
echo.
echo 访问地址:
echo   - 前端: http://localhost:%FRONTEND_PORT%
echo   - 后端: http://localhost:%BACKEND_PORT%
echo   - API文档: http://localhost:%BACKEND_PORT%/docs
echo.
echo 日志文件:
echo   - 后端日志: %BACKEND_DIR%\backend.log
echo   - 前端日志: %FRONTEND_DIR%\frontend.log
echo.
echo 停止服务: 运行 stop.bat 或关闭命令行窗口
echo.
pause
