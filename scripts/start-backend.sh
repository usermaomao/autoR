#!/bin/bash
# autoR 后端启动脚本
# 用途: 自动配置并启动 Django 后端服务

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}autoR 后端启动脚本 v1.0${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 未安装${NC}"
    echo "请安装 Python 3.8+: sudo apt install python3"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo -e "${GREEN}✓ Python 版本: $PYTHON_VERSION${NC}"

# 进入后端目录
cd "$BACKEND_DIR"

# 1. 检查并创建虚拟环境
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}[1/5] 创建虚拟环境...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✓ 虚拟环境已创建${NC}"
else
    echo -e "${GREEN}[1/5] 虚拟环境已存在${NC}"
fi
echo ""

# 2. 激活虚拟环境并安装依赖
echo -e "${YELLOW}[2/5] 检查依赖...${NC}"
source venv/bin/activate

# 检查是否需要安装依赖
if ! python -c "import django" 2>/dev/null; then
    echo "安装 Python 依赖..."
    pip install -r requirements.txt -q
    echo -e "${GREEN}✓ 依赖已安装${NC}"
else
    echo -e "${GREEN}✓ 依赖已就绪${NC}"
fi
echo ""

# 3. 检查数据库
echo -e "${YELLOW}[3/5] 检查数据库...${NC}"
if [ ! -f "db/db.sqlite3" ]; then
    echo "数据库不存在，创建数据库..."
    mkdir -p db
    python manage.py migrate
    echo -e "${GREEN}✓ 数据库已创建${NC}"

    # 询问是否创建超级用户
    echo ""
    read -p "是否创建管理员账户？(y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        python manage.py createsuperuser
    fi
else
    # 检查是否有未应用的迁移
    if python manage.py showmigrations | grep -q "\[ \]"; then
        echo "检测到未应用的数据库迁移，正在应用..."
        python manage.py migrate
    fi
    echo -e "${GREEN}✓ 数据库已就绪${NC}"
fi
echo ""

# 4. 检查 ECDICT 数据
echo -e "${YELLOW}[4/5] 检查 ECDICT 字典数据...${NC}"
ECDICT_COUNT=$(python -c "from cards.models import ECDict; print(ECDict.objects.count())" 2>/dev/null || echo "0")
if [ "$ECDICT_COUNT" -lt 100000 ]; then
    echo -e "${YELLOW}⚠ ECDICT 数据不完整 (当前: $ECDICT_COUNT 条)${NC}"
    echo "提示: 如需完整字典，运行: python manage.py import_ecdict /path/to/stardict.csv"
else
    echo -e "${GREEN}✓ ECDICT 数据已就绪 ($ECDICT_COUNT 条词条)${NC}"
fi
echo ""

# 5. 启动开发服务器
echo -e "${YELLOW}[5/5] 启动 Django 开发服务器...${NC}"
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}后端服务已启动！${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "访问地址:"
echo -e "  - 本地: ${GREEN}http://localhost:8000/api/${NC}"
echo -e "  - 局域网: ${GREEN}http://172.17.33.11:8000/api/${NC}"
echo -e "  - Django 管理: ${GREEN}http://172.17.33.11:8000/admin/${NC}"
echo ""
echo -e "按 ${RED}Ctrl+C${NC} 停止服务"
echo ""

# 启动服务器（监听所有网络接口，允许局域网访问）
python manage.py runserver 0.0.0.0:8000
