#!/bin/bash
# autoR 前端启动脚本
# 用途: 自动配置并启动 Vue 3 前端开发服务器

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}autoR 前端启动脚本 v1.0${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 检查 Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}✗ Node.js 未安装${NC}"
    echo "请安装 Node.js 18+: https://nodejs.org/"
    exit 1
fi

NODE_VERSION=$(node --version)
echo -e "${GREEN}✓ Node.js 版本: $NODE_VERSION${NC}"

# 检查 npm
if ! command -v npm &> /dev/null; then
    echo -e "${RED}✗ npm 未安装${NC}"
    exit 1
fi

NPM_VERSION=$(npm --version)
echo -e "${GREEN}✓ npm 版本: $NPM_VERSION${NC}"
echo ""

# 进入前端目录
cd "$FRONTEND_DIR"

# 1. 检查并安装依赖
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}[1/2] 安装 npm 依赖...${NC}"
    npm install
    echo -e "${GREEN}✓ 依赖已安装${NC}"
else
    echo -e "${GREEN}[1/2] 依赖已就绪${NC}"

    # 检查是否需要更新依赖
    if [ package.json -nt node_modules/.package-lock.json ] 2>/dev/null; then
        echo -e "${YELLOW}检测到 package.json 有更新，正在安装新依赖...${NC}"
        npm install
    fi
fi
echo ""

# 2. 启动 Vite 开发服务器
echo -e "${YELLOW}[2/2] 启动 Vite 开发服务器...${NC}"
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}前端服务已启动！${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "访问地址:"
echo -e "  - 本地: ${GREEN}http://localhost:5173/${NC}"
echo -e "  - 局域网: ${GREEN}http://172.17.33.11:5173/${NC}"
echo ""
echo -e "提示:"
echo -e "  - 确保后端服务已启动 (${YELLOW}http://172.17.33.11:8000${NC})"
echo -e "  - 热更新已启用，修改代码会自动刷新"
echo ""
echo -e "按 ${RED}Ctrl+C${NC} 停止服务"
echo ""

# 启动开发服务器
npm run dev
