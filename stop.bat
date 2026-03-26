@echo off
chcp 65001 >nul
echo ==========================================
echo SVN文件搜索系统 - Windows停止脚本
echo ==========================================
echo.

echo [1/3] 正在停止后端服务...
taskkill /F /IM python.exe 2>nul
taskkill /F /IM uvicorn.exe 2>nul
echo [成功] 后端服务已停止

echo.
echo [2/3] 正在停止前端服务...
taskkill /F /IM node.exe 2>nul
echo [成功] 前端服务已停止

echo.
echo [3/3] 正在清理端口占用...
set BACKEND_PORT=8001
set FRONTEND_PORT=5173

:: 释放后端端口
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%BACKEND_PORT%"') do (
    taskkill /F /PID %%a 2>nul
)

:: 释放前端端口
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%FRONTEND_PORT%"') do (
    taskkill /F /PID %%a 2>nul
)

echo [成功] 端口已释放

echo.
echo ==========================================
echo [成功] 所有服务已停止！
echo ==========================================
echo.
pause
