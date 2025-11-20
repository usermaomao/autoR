#!/bin/bash
# autoR 项目清理脚本
# 用途: 删除临时文件、缓存、未使用的依赖文件

set -e

echo "=========================================="
echo "autoR 项目清理工具 v1.0"
echo "=========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 统计函数
count_files() {
    find "$1" -type f 2>/dev/null | wc -l
}

get_size() {
    du -sh "$1" 2>/dev/null | cut -f1
}

# 1. 清理 Python 缓存文件
echo -e "${YELLOW}[1/7] 清理 Python 缓存文件 (__pycache__, *.pyc)${NC}"
BEFORE_PYC=$(count_files "backend" | grep -E "\.pyc$|__pycache__" | wc -l || echo 0)
find backend -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find backend -type f -name "*.pyc" -delete 2>/dev/null || true
find backend -type f -name "*.pyo" -delete 2>/dev/null || true
echo -e "${GREEN}✓ 完成${NC}"
echo ""

# 2. 清理 SQLite WAL 文件（不删除主数据库）
echo -e "${YELLOW}[2/7] 清理 SQLite 临时文件 (*.sqlite3-shm, *.sqlite3-wal)${NC}"
find backend/db -name "*.sqlite3-shm" -delete 2>/dev/null || true
find backend/db -name "*.sqlite3-wal" -delete 2>/dev/null || true
echo -e "${GREEN}✓ 完成${NC}"
echo ""

# 3. 清理 pytest 缓存
echo -e "${YELLOW}[3/7] 清理 pytest 缓存 (.pytest_cache)${NC}"
find backend -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
echo -e "${GREEN}✓ 完成${NC}"
echo ""

# 4. 清理未使用的 ECDICT 工具脚本（保留 import_ecdict.py）
echo -e "${YELLOW}[4/7] 清理未使用的 ECDICT 工具脚本${NC}"
if [ -d "backend/data/ECDICT" ]; then
    # 备份到 .backup 目录
    mkdir -p backend/data/ECDICT/.backup
    mv backend/data/ECDICT/*.py backend/data/ECDICT/.backup/ 2>/dev/null || true
    echo -e "${GREEN}✓ 已移动到 backend/data/ECDICT/.backup/${NC}"
else
    echo -e "${YELLOW}⚠ ECDICT 目录不存在，跳过${NC}"
fi
echo ""

# 5. 清理根目录测试文件（移动到 backend/tests/）
echo -e "${YELLOW}[5/7] 整理测试文件${NC}"
if [ ! -d "backend/tests" ]; then
    mkdir -p backend/tests
fi
mv backend/test_*.py backend/tests/ 2>/dev/null || true
echo -e "${GREEN}✓ 已移动到 backend/tests/${NC}"
echo ""

# 6. 清理 .DS_Store（macOS）
echo -e "${YELLOW}[6/7] 清理 macOS 缓存文件 (.DS_Store)${NC}"
find . -name ".DS_Store" -delete 2>/dev/null || true
echo -e "${GREEN}✓ 完成${NC}"
echo ""

# 7. 清理 node_modules 中的无用文件（可选）
echo -e "${YELLOW}[7/7] 清理 node_modules 中的测试/文档文件（可选）${NC}"
read -p "是否清理 node_modules 中的 README/LICENSE/test 文件？(y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    find frontend/node_modules -name "README.md" -delete 2>/dev/null || true
    find frontend/node_modules -name "LICENSE" -delete 2>/dev/null || true
    find frontend/node_modules -name "*.test.js" -delete 2>/dev/null || true
    echo -e "${GREEN}✓ 完成${NC}"
else
    echo -e "${YELLOW}⊘ 跳过${NC}"
fi
echo ""

# 8. 生成 .gitignore 文件（如果不存在）
echo -e "${YELLOW}[附加] 更新 .gitignore 文件${NC}"
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
*.egg-info/
dist/
build/

# Virtual Environment
backend/venv/
backend/env/

# Django
*.log
*.pot
*.sqlite3
*.sqlite3-shm
*.sqlite3-wal
db.sqlite3
media/
staticfiles/

# Environment
.env
.env.local
*.env

# Testing
.pytest_cache/
.coverage
htmlcov/
*.cover

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Node
frontend/node_modules/
frontend/dist/
frontend/.vite/

# OS
.DS_Store
Thumbs.db

# Backup
*.backup
*.bak
.backup/

# Logs
npm-debug.log*
yarn-debug.log*
yarn-error.log*
EOF
echo -e "${GREEN}✓ .gitignore 已更新${NC}"
echo ""

# 9. 显示清理后的统计信息
echo "=========================================="
echo -e "${GREEN}清理完成！${NC}"
echo "=========================================="
echo ""
echo "项目当前大小统计:"
echo "  - backend/ (不含 venv): $(du -sh backend --exclude=venv 2>/dev/null | cut -f1)"
echo "  - frontend/ (不含 node_modules): $(du -sh frontend --exclude=node_modules 2>/dev/null | cut -f1)"
echo "  - data/: $(get_size data)"
echo ""
echo "大文件提示:"
echo "  - backend/db/db.sqlite3: $(get_size backend/db/db.sqlite3) (包含 ECDICT 77万词条)"
echo "  - backend/venv/: $(get_size backend/venv) (虚拟环境，建议加入 .gitignore)"
echo "  - frontend/node_modules/: $(get_size frontend/node_modules) (依赖包，建议加入 .gitignore)"
echo ""
echo -e "${YELLOW}建议操作:${NC}"
echo "  1. 确认 backend/venv/ 已在 .gitignore 中"
echo "  2. 确认 frontend/node_modules/ 已在 .gitignore 中"
echo "  3. 定期运行此脚本清理缓存"
echo "  4. 备份的 ECDICT 工具脚本在 backend/data/ECDICT/.backup/"
echo ""
