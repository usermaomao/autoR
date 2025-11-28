#!/bin/bash
# autoR 项目清理脚本 - 基础清理版本
# 用途：定期清理缓存和临时文件，保持项目整洁
# 安全性：仅删除可自动重新生成的文件

set -e

echo "🧹 autoR 项目清理工具"
echo "===================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 显示清理前大小
echo -e "${BLUE}清理前项目大小：${NC}"
du -sh . 2>/dev/null
echo ""

# 1. 清理 Python 缓存
echo -e "${BLUE}1️⃣ 清理 Python 缓存文件...${NC}"
pycache_count=$(find . -type d -name "__pycache__" 2>/dev/null | wc -l)
echo "   找到 $pycache_count 个 __pycache__ 目录"

find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true
echo -e "   ${GREEN}✓ Python 缓存已清理${NC}"
echo ""

# 2. 清理前端缓存
echo -e "${BLUE}2️⃣ 清理前端缓存...${NC}"
if [ -d "frontend/.vite" ]; then
    rm -rf frontend/.vite
    echo -e "   ${GREEN}✓ Vite 缓存已删除${NC}"
else
    echo "   ℹ️  Vite 缓存不存在"
fi
echo ""

# 3. 清理备份文件
echo -e "${BLUE}3️⃣ 清理备份和临时文件...${NC}"
if [ -d "backend/data/ECDICT/.backup" ]; then
    rm -rf backend/data/ECDICT/.backup
    echo -e "   ${GREEN}✓ ECDICT 备份已删除${NC}"
else
    echo "   ℹ️  备份目录不存在"
fi

# 清理其他临时文件
find . -name "*.tmp" -delete 2>/dev/null || true
find . -name "*.bak" -delete 2>/dev/null || true
find . -name "*~" -delete 2>/dev/null || true
echo -e "   ${GREEN}✓ 临时文件已清理${NC}"
echo ""

# 4. 清理测试覆盖率文件
echo -e "${BLUE}4️⃣ 清理测试覆盖率文件...${NC}"
rm -rf .pytest_cache 2>/dev/null || true
rm -rf htmlcov 2>/dev/null || true
rm -f .coverage 2>/dev/null || true
echo -e "   ${GREEN}✓ 测试缓存已清理${NC}"
echo ""

# 显示清理后大小
echo -e "${BLUE}清理后项目大小：${NC}"
du -sh . 2>/dev/null
echo ""

# 5. 验证项目完整性
echo -e "${BLUE}5️⃣ 验证项目完整性...${NC}"
cd backend
if python3 manage.py check > /dev/null 2>&1; then
    echo -e "   ${GREEN}✓ 后端检查通过${NC}"
else
    echo -e "   ⚠️  后端检查失败，请手动检查"
fi
cd ..
echo ""

echo "✅ 清理完成！"
echo ""
echo "💡 提示："
echo "   - 清理的文件会在下次运行时自动重新生成"
echo "   - 如需深度清理（删除依赖），请运行：./scripts/cleanup-deep.sh"
echo ""
