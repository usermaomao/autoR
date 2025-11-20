#!/bin/bash
# autoR 一键启动脚本
# 用途: 同时启动前端和后端开发服务器

set -e

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPTS_DIR="$PROJECT_ROOT/scripts"

# 显示 Logo
clear
cat << "EOF"
   ___        __       ____
  / _ | __ __/ /_ ___ / __ \
 / __ |/ // / __// _ \/ /_/ /
/_/ |_|\_,_/\__/ \___/_____/

基于艾宾浩斯记忆曲线的词汇学习系统
EOF

echo ""
echo "========================================"
echo "autoR 一键启动脚本 v1.0"
echo "========================================"
echo ""

# 检查依赖
echo "[系统检查]"
echo ""

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "✗ Python 3 未安装"
    echo "请安装 Python 3.8+: sudo apt install python3"
    exit 1
fi
echo "✓ Python $(python3 --version | cut -d' ' -f2)"

# 检查 Node.js
if ! command -v node &> /dev/null; then
    echo "✗ Node.js 未安装"
    echo "请安装 Node.js 18+: https://nodejs.org/"
    exit 1
fi
echo "✓ Node.js $(node --version)"

# 检查 npm
if ! command -v npm &> /dev/null; then
    echo "✗ npm 未安装"
    exit 1
fi
echo "✓ npm $(npm --version)"

echo ""
echo "========================================"
echo ""

# 选择启动模式
echo "请选择启动模式:"
echo "  1 - 完整模式 (前端 + 后端)"
echo "  2 - 仅后端"
echo "  3 - 仅前端"
echo "  4 - 后台运行"
echo "  q - 退出"
echo ""
read -p "请输入选项 [1-4/q]: " -n 1 -r MODE
echo ""
echo ""

case $MODE in
    1)
        # 完整模式 - 顺序启动
        echo "启动完整模式 (前端 + 后端)..."
        echo ""

        # 先启动后端（后台）
        echo "[1/2] 启动后端服务 (后台)..."
        bash "$SCRIPTS_DIR/start-backend.sh" &
        BACKEND_PID=$!
        echo "后端 PID: $BACKEND_PID"
        sleep 3

        # 启动前端（前台）
        echo "[2/2] 启动前端服务..."
        echo ""
        trap "kill $BACKEND_PID 2>/dev/null" EXIT
        bash "$SCRIPTS_DIR/start-frontend.sh"
        ;;

    2)
        # 仅后端
        echo "启动后端服务..."
        echo ""
        bash "$SCRIPTS_DIR/start-backend.sh"
        ;;

    3)
        # 仅前端
        echo "启动前端服务..."
        echo ""
        bash "$SCRIPTS_DIR/start-frontend.sh"
        ;;

    4)
        # 后台运行模式
        echo "后台运行模式..."
        echo ""

        # 启动后端（后台）
        echo "[1/2] 启动后端服务 (后台)..."
        cd "$PROJECT_ROOT/backend"
        source venv/bin/activate
        nohup python manage.py runserver 0.0.0.0:8000 > /tmp/autoR-backend.log 2>&1 &
        BACKEND_PID=$!
        echo "后端 PID: $BACKEND_PID"
        sleep 2

        # 启动前端（后台）
        echo "[2/2] 启动前端服务 (后台)..."
        cd "$PROJECT_ROOT/frontend"
        nohup npm run dev > /tmp/autoR-frontend.log 2>&1 &
        FRONTEND_PID=$!
        echo "前端 PID: $FRONTEND_PID"

        echo ""
        echo "✓ 服务已在后台启动"
        echo ""
        echo "访问地址:"
        echo "  - 前端: http://localhost:5173/"
        echo "  - 后端: http://localhost:8000/api/"
        echo ""
        echo "查看日志:"
        echo "  - 后端: tail -f /tmp/autoR-backend.log"
        echo "  - 前端: tail -f /tmp/autoR-frontend.log"
        echo ""
        echo "停止服务:"
        echo "  - 后端: kill $BACKEND_PID"
        echo "  - 前端: kill $FRONTEND_PID"
        echo "  - 全部: pkill -f 'runserver|vite'"
        echo ""

        # 保存 PID 到文件
        echo $BACKEND_PID > /tmp/autoR-backend.pid
        echo $FRONTEND_PID > /tmp/autoR-frontend.pid
        ;;

    q|Q)
        echo "退出"
        exit 0
        ;;

    *)
        echo "无效选项"
        exit 1
        ;;
esac
