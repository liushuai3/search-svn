#!/bin/bash

echo "=========================================="
echo "SVN 文件搜索系统 - Linux重启脚本"
echo "=========================================="
echo ""

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"

# 尝试从 .env 文件读取端口配置
ENV_FILE="$SCRIPT_DIR/frontend/.env"
BACKEND_PORT=8001
FRONTEND_PORT=5173

if [ -f "$ENV_FILE" ]; then
    while IFS='=' read -r key value; do
        # 去除空格和注释
        key=$(echo "$key" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
        value=$(echo "$value" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
        
        case "$key" in
            "VITE_BACKEND_PORT") BACKEND_PORT="${value:-8001}" ;;
            "FRONTEND_PORT") FRONTEND_PORT="${value:-5173}" ;;
        esac
    done < "$ENV_FILE"
fi

# 环境变量优先级高于 .env 文件
BACKEND_PORT="${BACKEND_PORT_ENV:-$BACKEND_PORT}"
FRONTEND_PORT="${FRONTEND_PORT_ENV:-$FRONTEND_PORT}"

# 导出前端端口，供 vite 使用
export FRONTEND_PORT

echo "Using BACKEND_PORT=$BACKEND_PORT"
echo "Using FRONTEND_PORT=$FRONTEND_PORT"

# 日志文件
BACKEND_LOG="$BACKEND_DIR/backend.log"
FRONTEND_LOG="$FRONTEND_DIR/frontend.log"

# 停止现有服务
echo "[1/3] 正在停止现有服务..."

# 停止后端（查找并杀死 uvicorn 进程）
pkill -f "uvicorn main:app" 2>/dev/null
pkill -f "python.*main:app" 2>/dev/null

# 停止前端（查找并杀死 npm run dev 进程）
pkill -f "npm run dev" 2>/dev/null
pkill -f "node.*vite" 2>/dev/null

# 等待进程完全停止
sleep 2

echo "[成功] 现有服务已停止"

# 启动后端服务
echo ""
echo "[2/3] 正在启动后端服务..."
cd "$BACKEND_DIR" || exit 1

# 检查端口是否被占用
if lsof -Pi :$BACKEND_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "[警告] 端口 $BACKEND_PORT 已被占用，尝试释放..."
    lsof -Pi :$BACKEND_PORT -sTCP:LISTEN -t | xargs kill -9 2>/dev/null
    sleep 1
fi

# 启动后端（后台运行）
nohup uvicorn main:app --host 0.0.0.0 --port $BACKEND_PORT --reload > "$BACKEND_LOG" 2>&1 &
BACKEND_PID=$!

# 等待后端启动
sleep 3

# 检查后端是否成功启动
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo "[错误] 后端启动失败，请查看日志：$BACKEND_LOG"
    exit 1
fi

echo "[成功] 后端服务已启动，PID: $BACKEND_PID，端口: $BACKEND_PORT"
echo "[信息] 后端日志：$BACKEND_LOG"

# 启动前端服务
echo ""
echo "[3/3] 正在启动前端服务..."
cd "$FRONTEND_DIR" || exit 1

# 检查端口是否被占用
if lsof -Pi :$FRONTEND_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "[警告] 端口 $FRONTEND_PORT 已被占用，尝试释放..."
    lsof -Pi :$FRONTEND_PORT -sTCP:LISTEN -t | xargs kill -9 2>/dev/null
    sleep 1
fi

# 启动前端（后台运行）
nohup npm run dev > "$FRONTEND_LOG" 2>&1 &
FRONTEND_PID=$!

# 等待前端启动
sleep 3

# 检查前端是否成功启动
if ! kill -0 $FRONTEND_PID 2>/dev/null; then
    echo "[错误] 前端启动失败，请查看日志：$FRONTEND_LOG"
    exit 1
fi

echo "[成功] 前端服务已启动，PID: $FRONTEND_PID，端口: $FRONTEND_PORT"
echo "[信息] 前端日志：$FRONTEND_LOG"

echo ""
echo "=========================================="
echo "[成功] 所有服务已启动！"
echo "=========================================="
echo ""
echo "访问地址："
echo "  - 前端：http://localhost:$FRONTEND_PORT"
echo "  - 后端：http://localhost:$BACKEND_PORT"
echo "  - API文档：http://localhost:$BACKEND_PORT/docs"
echo ""
echo "日志文件："
echo "  - 后端日志：$BACKEND_LOG"
echo "  - 前端日志：$FRONTEND_LOG"
echo ""
echo "进程信息："
echo "  - 后端 PID：$BACKEND_PID"
echo "  - 前端 PID：$FRONTEND_PID"
echo ""
echo "停止服务：运行 ./stop.sh"
echo ""
