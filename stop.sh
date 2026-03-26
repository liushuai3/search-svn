#!/bin/bash

echo "=========================================="
echo "SVN 文件搜索系统 - Linux停止脚本"
echo "=========================================="
echo ""

BACKEND_PORT=8001
FRONTEND_PORT=5173

echo "[1/3] 正在停止后端服务..."

# 停止后端（查找并杀死 uvicorn 进程）
pkill -f "uvicorn main:app" 2>/dev/null
pkill -f "python.*main:app" 2>/dev/null

echo "[成功] 后端服务已停止"

echo ""
echo "[2/3] 正在停止前端服务..."

# 停止前端（查找并杀死 npm run dev 进程）
pkill -f "npm run dev" 2>/dev/null
pkill -f "node.*vite" 2>/dev/null

echo "[成功] 前端服务已停止"

echo ""
echo "[3/3] 正在清理端口占用..."

# 释放后端端口
if lsof -Pi :$BACKEND_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    lsof -Pi :$BACKEND_PORT -sTCP:LISTEN -t | xargs kill -9 2>/dev/null
    echo "[成功] 后端端口 $BACKEND_PORT 已释放"
fi

# 释放前端端口
if lsof -Pi :$FRONTEND_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    lsof -Pi :$FRONTEND_PORT -sTCP:LISTEN -t | xargs kill -9 2>/dev/null
    echo "[成功] 前端端口 $FRONTEND_PORT 已释放"
fi

# 等待进程完全停止
sleep 1

echo ""
echo "=========================================="
echo "[成功] 所有服务已停止！"
echo "=========================================="
echo ""
