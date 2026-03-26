#!/bin/bash

echo "=========================================="
echo "SVN 文件搜索系统 - Linux部署脚本"
echo "=========================================="
echo ""

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"

# 检查目录是否存在
if [ ! -d "$BACKEND_DIR" ]; then
    echo "[错误] 后端目录不存在：$BACKEND_DIR"
    exit 1
fi

if [ ! -d "$FRONTEND_DIR" ]; then
    echo "[错误] 前端目录不存在：$FRONTEND_DIR"
    exit 1
fi

# 安装后端依赖
echo "[1/4] 正在安装后端依赖..."
cd "$BACKEND_DIR" || exit 1
if [ -f "requirements.txt" ]; then
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "[错误] 后端依赖安装失败"
        exit 1
    fi
else
    echo "[警告] 未找到 requirements.txt"
fi

# 安装前端依赖
echo ""
echo "[2/4] 正在安装前端依赖..."
cd "$FRONTEND_DIR" || exit 1
if [ -f "package.json" ]; then
    npm install
    if [ $? -ne 0 ]; then
        echo "[错误] 前端依赖安装失败"
        exit 1
    fi
else
    echo "[警告] 未找到 package.json"
fi

# 初始化数据库
echo ""
echo "[3/4] 正在初始化数据库..."
cd "$BACKEND_DIR" || exit 1
python3 -c "from app.models.database import Base, engine; Base.metadata.create_all(bind=engine); print('数据库初始化完成')"

# 构建前端
echo ""
echo "[4/4] 正在构建前端..."
cd "$FRONTEND_DIR" || exit 1
if [ -f "package.json" ]; then
    npm run build
    if [ $? -ne 0 ]; then
        echo "[警告] 前端构建失败，继续部署..."
    fi
fi

echo ""
echo "=========================================="
echo "[成功] 部署完成！"
echo "=========================================="
echo ""
echo "启动命令:"
echo "  - 后端：cd backend && uvicorn main:app --host 0.0.0.0 --port 8001"
echo "  - 前端：cd frontend && npm run dev"
echo ""
