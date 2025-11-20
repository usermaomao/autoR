#!/bin/bash
# autoR 网络检查脚本
# 用途: 检查服务的网络监听状态和可访问性

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}autoR 网络检查脚本${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 1. 获取 WSL IP 地址
echo -e "${YELLOW}[1/4] 检查 WSL IP 地址...${NC}"
WSL_IP=$(ip addr show eth0 | grep "inet " | awk '{print $2}' | cut -d/ -f1)
if [ -z "$WSL_IP" ]; then
    echo -e "${RED}✗ 无法获取 WSL IP 地址${NC}"
    exit 1
fi
echo -e "${GREEN}✓ WSL IP: $WSL_IP${NC}"
echo ""

# 2. 检查端口监听状态
echo -e "${YELLOW}[2/4] 检查端口监听状态...${NC}"

# 后端端口
BACKEND_LISTEN=$(netstat -tuln 2>/dev/null | grep :8000 || ss -tuln 2>/dev/null | grep :8000 || echo "")
if [ -z "$BACKEND_LISTEN" ]; then
    echo -e "${RED}✗ 后端 (8000) 未监听${NC}"
    BACKEND_STATUS="停止"
else
    if echo "$BACKEND_LISTEN" | grep -q "0.0.0.0:8000"; then
        echo -e "${GREEN}✓ 后端监听: 0.0.0.0:8000 (可从局域网访问)${NC}"
        BACKEND_STATUS="运行中 (局域网)"
    else
        echo -e "${YELLOW}⚠ 后端监听: 127.0.0.1:8000 (仅本地)${NC}"
        BACKEND_STATUS="运行中 (仅本地)"
    fi
fi

# 前端端口
FRONTEND_LISTEN=$(netstat -tuln 2>/dev/null | grep :5173 || ss -tuln 2>/dev/null | grep :5173 || echo "")
if [ -z "$FRONTEND_LISTEN" ]; then
    echo -e "${RED}✗ 前端 (5173) 未监听${NC}"
    FRONTEND_STATUS="停止"
else
    if echo "$FRONTEND_LISTEN" | grep -q "0.0.0.0:5173"; then
        echo -e "${GREEN}✓ 前端监听: 0.0.0.0:5173 (可从局域网访问)${NC}"
        FRONTEND_STATUS="运行中 (局域网)"
    else
        echo -e "${YELLOW}⚠ 前端监听: 127.0.0.1:5173 (仅本地)${NC}"
        FRONTEND_STATUS="运行中 (仅本地)"
    fi
fi
echo ""

# 3. 测试 API 连通性
echo -e "${YELLOW}[3/4] 测试 API 连通性...${NC}"

# 本地测试
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/ | grep -q "200\|403"; then
    echo -e "${GREEN}✓ 本地访问: http://localhost:8000/api/${NC}"
else
    echo -e "${RED}✗ 本地访问失败${NC}"
fi

# 局域网测试
if curl -s -o /dev/null -w "%{http_code}" http://$WSL_IP:8000/api/ | grep -q "200\|403"; then
    echo -e "${GREEN}✓ 局域网访问: http://$WSL_IP:8000/api/${NC}"
else
    echo -e "${RED}✗ 局域网访问失败${NC}"
fi
echo ""

# 4. 显示访问信息
echo -e "${YELLOW}[4/4] 访问信息汇总${NC}"
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}服务状态${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "  后端: ${GREEN}$BACKEND_STATUS${NC}"
echo -e "  前端: ${GREEN}$FRONTEND_STATUS${NC}"
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}访问地址 - WSL 本地${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "  前端: ${GREEN}http://localhost:5173/${NC}"
echo -e "  后端: ${GREEN}http://localhost:8000/api/${NC}"
echo -e "  管理: ${GREEN}http://localhost:8000/admin/${NC}"
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}访问地址 - PC 局域网${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "  前端: ${GREEN}http://$WSL_IP:5173/${NC}"
echo -e "  后端: ${GREEN}http://$WSL_IP:8000/api/${NC}"
echo -e "  管理: ${GREEN}http://$WSL_IP:8000/admin/${NC}"
echo ""

# 5. 配置检查建议
if [ "$BACKEND_STATUS" = "停止" ] || [ "$FRONTEND_STATUS" = "停止" ]; then
    echo -e "${YELLOW}提示: 服务未运行，请执行 ./start.sh 启动${NC}"
    echo ""
elif [ "$BACKEND_STATUS" = "运行中 (仅本地)" ] || [ "$FRONTEND_STATUS" = "运行中 (仅本地)" ]; then
    echo -e "${YELLOW}⚠ 警告: 服务仅监听本地，无法从 PC 访问${NC}"
    echo ""
    echo "解决方法:"
    echo "1. 停止服务: ./stop.sh"
    echo "2. 重新启动: ./start.sh"
    echo "3. 或查看配置文档: docs/局域网访问配置.md"
    echo ""
fi

echo -e "${GREEN}检查完成！${NC}"
echo ""
