#!/bin/bash
# autoR 快速启动卡片
# 用途: 显示快速参考命令

cat << 'EOF'
╔══════════════════════════════════════════════════════╗
║        autoR 快速启动参考卡片 v1.0                  ║
╚══════════════════════════════════════════════════════╝

📦 一键启动
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ./start.sh                    # 主启动脚本（推荐）
  ./stop.sh                     # 停止所有服务
  ./scripts/check-network.sh    # 检查网络状态和访问地址

🚀 分别启动
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ./scripts/start-backend.sh    # 仅后端 (端口 8000)
  ./scripts/start-frontend.sh   # 仅前端 (端口 5173)

🌐 访问地址
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  本地访问:
    前端应用: http://localhost:5173
    后端 API: http://localhost:8000/api/
    管理后台: http://localhost:8000/admin/

  PC 局域网访问（从 Windows 访问 WSL）:
    前端应用: http://172.17.33.11:5173
    后端 API: http://172.17.33.11:8000/api/
    管理后台: http://172.17.33.11:8000/admin/
    提示: 运行 ./scripts/check-network.sh 查看实时 IP

⌨️  tmux 快捷键（完整模式）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Ctrl+B, ←/→      切换前后端窗口
  Ctrl+B, D        分离会话（服务继续运行）
  Ctrl+C           停止当前窗口服务
  tmux attach -t autoR  重新附加会话
  tmux kill-session -t autoR  关闭会话

🛠️ 管理命令
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  # 后端 (在 backend/ 目录下)
  source venv/bin/activate      # 激活虚拟环境
  python manage.py migrate      # 运行数据库迁移
  python manage.py createsuperuser  # 创建管理员
  python manage.py shell        # Django Shell
  pytest                        # 运行测试

  # 前端 (在 frontend/ 目录下)
  npm install                   # 安装依赖
  npm run dev                   # 启动开发服务器
  npm run build                 # 构建生产版本

🧹 维护命令
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ./cleanup.sh                  # 清理缓存和临时文件
  ./stop.sh                     # 停止所有服务

📊 日志查看
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  tail -f /tmp/autoR-backend.log   # 后端日志（后台模式）
  tail -f /tmp/autoR-frontend.log  # 前端日志（后台模式）

🐛 问题排查
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  lsof -i :8000                 # 检查后端端口占用
  lsof -i :5173                 # 检查前端端口占用
  pkill -f runserver            # 强制停止 Django
  pkill -f vite                 # 强制停止 Vite

📦 导入导出功能 (Phase 1.1 & 1.2 已完成)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  API 端点:
    POST /api/cards/import/      # 导入 CSV/JSON (Anki 兼容)
    GET  /api/cards/export/      # 导出 CSV/JSON

  CSV 格式示例:
    Front,Back,Tags
    apple,苹果,水果
    banana,香蕉,"水果,热带"

  JSON 格式示例:
    {"cards": [
      {"Front": "hello", "Back": "你好", "Tags": "问候"}
    ]}

  测试命令:
    python backend/test_import_export.py

  功能特性:
    ✓ 语义去重 (MD5 指纹)
    ✓ 冲突策略: skip/overwrite/merge
    ✓ 批量导入 (10MB 限制)

📚 文档
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  CLAUDE.md                     # 完整开发指南
  docs/启动指南.md              # 详细启动说明
  docs/项目整理完成报告.md      # 项目状态总结
  docs/phase1-plan.md           # Phase 1 开发计划

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
提示: 运行 ./start.sh 选择启动模式
      首次启动会自动配置环境和安装依赖
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EOF
