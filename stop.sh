#!/bin/bash
# autoR 停止服务脚本
# 用途: 停止所有运行中的 autoR 服务

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}autoR 停止服务脚本${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 1. 尝试关闭 tmux 会话
if command -v tmux &> /dev/null; then
    if tmux has-session -t autoR 2>/dev/null; then
        echo -e "${YELLOW}关闭 tmux 会话 'autoR'...${NC}"
        tmux kill-session -t autoR
        echo -e "${GREEN}✓ tmux 会话已关闭${NC}"
    fi
fi

# 2. 停止后台进程（通过 PID 文件）
if [ -f "/tmp/autoR-backend.pid" ]; then
    BACKEND_PID=$(cat /tmp/autoR-backend.pid)
    if ps -p $BACKEND_PID > /dev/null 2>&1; then
        echo -e "${YELLOW}停止后端服务 (PID: $BACKEND_PID)...${NC}"
        kill $BACKEND_PID 2>/dev/null || true
        rm /tmp/autoR-backend.pid
        echo -e "${GREEN}✓ 后端服务已停止${NC}"
    fi
fi

if [ -f "/tmp/autoR-frontend.pid" ]; then
    FRONTEND_PID=$(cat /tmp/autoR-frontend.pid)
    if ps -p $FRONTEND_PID > /dev/null 2>&1; then
        echo -e "${YELLOW}停止前端服务 (PID: $FRONTEND_PID)...${NC}"
        kill $FRONTEND_PID 2>/dev/null || true
        rm /tmp/autoR-frontend.pid
        echo -e "${GREEN}✓ 前端服务已停止${NC}"
    fi
fi

# 3. 强制停止所有 Django runserver 和 Vite 进程
echo ""
echo -e "${YELLOW}检查并停止残留进程...${NC}"

# 停止 Django
DJANGO_PIDS=$(pgrep -f "python.*manage.py runserver" || true)
if [ -n "$DJANGO_PIDS" ]; then
    echo "停止 Django 进程: $DJANGO_PIDS"
    pkill -f "python.*manage.py runserver" || true
    echo -e "${GREEN}✓ Django 进程已停止${NC}"
fi

# 停止 Vite
VITE_PIDS=$(pgrep -f "vite" || true)
if [ -n "$VITE_PIDS" ]; then
    echo "停止 Vite 进程: $VITE_PIDS"
    pkill -f "vite" || true
    echo -e "${GREEN}✓ Vite 进程已停止${NC}"
fi

# 4. 清理日志文件（可选）
echo ""
read -p "是否删除日志文件？(y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -f /tmp/autoR-backend.log /tmp/autoR-frontend.log
    echo -e "${GREEN}✓ 日志文件已删除${NC}"
fi

echo ""
echo -e "${GREEN}所有服务已停止！${NC}"
echo ""
