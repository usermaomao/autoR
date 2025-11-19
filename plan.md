# 项目实施计划 - 基于艾宾浩斯记忆曲线的词汇/生字学习网站 v2.0

## 项目概览

**项目名称**: 基于艾宾浩斯记忆曲线的词汇/生字学习网站
**版本**: v2.0 (PWA 架构升级版)
**目标用户**: ≤10 人自用、小团队
**总工时**: 218 小时 (5.45 周 @ 40h/周)
**核心价值**: 移动端优先、支持离线、高可用、科学复习算法

### 技术栈

```
后端:  Django 5 + Django REST Framework + SQLite
前端:  Vue 3 + Vite + Tailwind CSS
PWA:   Workbox (Service Worker + IndexedDB)
数据:  ECDICT (77万词条) + UniHan Database + dictionaryapi.dev
部署:  Docker Compose + Nginx + S3 备份
```

### 关键优化点 (相比 v1.0)

**P0 必须修复:**
1. 本地字典降级方案 (四层: IndexedDB → ECDICT → API → 手动)
2. 完整 SM-2 算法 (引入 EF + D 参数)
3. 自动备份机制 (cron + S3 异地容灾)

**P1 强烈建议:**
4. PWA 离线支持 (Workbox + Background Sync)
5. 性能优化 (首屏 P95 <900ms)
6. 多音字语境推断 (jieba 分词)

---

## 里程碑时间线

```
+----------------+----------------+----------------+
|  M1 (1.7 周)   |  M2 (2.25 周)  |  M3 (1.5 周)   |
|   后端基础     |   PWA 前端     |   优化增强     |
|   68 小时      |   90 小时      |   60 小时      |
+----------------+----------------+----------------+
      |                 |                 |
      v                 v                 v
 数据模型+算法      Vue3+离线支持      性能+多音字
 ECDICT+备份        四层数据源         统计+导入导出
```

**关键路径** (影响交付时间):
```
M1.2 (数据模型) → M1.4 (SM-2 算法) → M1.5 (ECDICT)
    ↓
M2.2 (复习会话) → M2.4 (PWA 基础) → M2.6 (离线同步)
    ↓
M3.3 (多音字推断) → M3.4 (性能优化)
```

---

## M1 里程碑: 后端基础设施 (1.7 周 / 68 小时)

**目标**: 搭建后端基础设施，集成核心算法和数据源，建立自动化备份机制

### 1.1 环境搭建与项目初始化 (6h)

- [ ] 创建 Django 5 项目，配置虚拟环境
- [ ] 安装 DRF、corsheaders、django-extensions 等依赖
- [ ] 配置 SQLite 数据库（启用 WAL 模式提升并发）
- [ ] 配置 Git、.gitignore、pre-commit hooks

**验收标准**:
- `python manage.py runserver` 成功启动
- Django Admin 可访问

**依赖**: 无
**风险**: 无

---

### 1.2 数据模型设计与迁移 (8h)

- [ ] 设计 User、Deck、Card、ReviewLog 等核心模型
- [ ] 添加字段:
  - EF (易忘因子, 初始 2.5)
  - D (难度, 动态调整)
  - S (稳定度, 继承 v1.0)
  - lapses (错误次数)
  - due_at (下次复习时间)
- [ ] 支持英语/汉字两种 Card 类型（使用 JSONField 存储特定字段）
- [ ] 创建数据库索引（due_at、user_id、deck_id）
- [ ] 编写 migration 并测试

**验收标准**:
- 所有模型可在 Django Admin 中 CRUD
- 数据库索引生效

**依赖**: 1.1
**技术决策**: 使用 JSONField 存储语言特定字段（灵活性高）

---

### 1.3 DRF API 开发 - 认证与 CRUD (10h)

- [ ] 实现用户注册/登录 API (JWT 或 Session)
- [ ] 实现 Deck CRUD 接口 (`/api/decks/`)
- [ ] 实现 Card CRUD 接口 (`/api/cards/`)
- [ ] 添加分页、过滤、搜索功能
- [ ] 编写 API 单元测试（覆盖率 ≥80%）

**验收标准**:
- Postman/curl 可完成所有 CRUD 操作
- API 响应 P99 <500ms
- 单元测试通过

**依赖**: 1.2
**风险**: 无

---

### 1.4 完整 SM-2 算法实现 (12h) ⭐ 关键路径

- [ ] 实现 EF 计算公式:
  ```
  EF' = EF + (0.1 - (5-q)*(0.08+(5-q)*0.02))
  // q 为评分映射 0-5 (Again=0, Hard=2, Good=4, Easy=5)
  ```
- [ ] 实现间隔计算:
  ```
  interval_new = interval_old * EF'
  EF 下限: 1.3
  ```
- [ ] 实现学习小步:
  - 新学: 10 分钟 → 1 天
  - Again: 回退到学习队列
  - Good/Easy: 可直接进入复习
- [ ] 实现队列生成逻辑:
  - 先到期卡片、后新卡
  - 难项优先（lapses ≥ 3）
  - `daily_new_limit` 与 `daily_review_limit` 控制负荷
- [ ] 实现难项标记 (lapses≥3 → Leech)
- [ ] 编写算法单元测试（覆盖边界情况）

**验收标准**:
- 队列生成 ≤300ms (1000 卡片)
- 评分后即时更新 due_at、EF、interval
- 算法参数可通过配置调整
- 单元测试覆盖率 ≥90%

**依赖**: 1.3
**风险**: 算法复杂，需要充分测试

---

### 1.5 ECDICT 本地字典集成 (15h) ⭐ 关键路径

- [ ] 下载 ECDICT 开源数据
  - 仓库: https://github.com/skywind3000/ECDICT
  - 数据量: 77 万词条
- [ ] 预处理: 导入到 SQLite，建立 FTS5 全文搜索索引
- [ ] 实现查询 API: `/api/dict/en/{word}`
- [ ] 返回字段:
  - ipa (国际音标)
  - pos (词性)
  - meaning_en (英文释义)
  - examples[] (例句数组)
  - frequency (词频)
  - CEFR (欧洲语言标准等级: A1-C2)
- [ ] 性能优化: 添加查询缓存（Django cache）
- [ ] 编写集成测试

**验收标准**:
- 常见词查询 P95 <300ms
- 覆盖率 ≥90% (测试 1000 个常见词)
- 数据库大小 <200MB

**依赖**: 1.2
**风险**: ECDICT 数据量大，导入和索引耗时 (预计 2-3 小时)

**应对方案**:
- M1 第一周完成 POC 验证
- 准备 Plan B: 使用 StarDict 格式字典
- 性能不达标时使用 Redis 缓存

---

### 1.6 UniHan 汉字数据库集成 (10h)

- [ ] 下载 UniHan Database
  - 来源: https://unicode.org/charts/unihan.html
- [ ] 预处理: 提取拼音、部首、笔画、简繁体对照
- [ ] 导入到 SQLite，建立索引
- [ ] 实现查询 API: `/api/dict/zh/{hanzi}`
- [ ] 返回字段:
  - pinyin (拼音，含声调)
  - variants[] (多音字候选数组)
  - meaning_zh (基础释义)
  - examples (例句/组词)
  - radical (部首)
  - strokes (笔画数)
  - simplified/traditional (简繁体对照)
- [ ] 编写集成测试

**验收标准**:
- 常见字查询 P95 <300ms
- 覆盖率 ≥95% (GB2312 常用字 6763 个)

**依赖**: 1.2
**技术决策**: 多音字以数组形式返回所有读音

---

### 1.7 自动备份机制实现 (7h)

- [ ] 编写备份脚本 `scripts/backup.sh`:
  ```bash
  #!/bin/bash
  DB_PATH="/app/db/db.sqlite3"
  BACKUP_DIR="/backup/$(date +%Y%m%d_%H%M%S)"
  S3_BUCKET="s3://rpd-backup"

  # 在线备份（不锁表）
  sqlite3 "$DB_PATH" ".backup '$BACKUP_DIR/db.sqlite3'"

  # 计算 MD5
  md5sum "$BACKUP_DIR/db.sqlite3" > "$BACKUP_DIR/checksum.md5"

  # 上传到 S3
  aws s3 cp "$BACKUP_DIR/db.sqlite3" "$S3_BUCKET/"

  # 保留 30 天
  find /backup -mtime +30 -delete
  ```
- [ ] 配置 cron 任务（每日凌晨 2:00）
  ```
  0 2 * * * /app/scripts/backup.sh
  ```
- [ ] 实现 S3 上传（使用 boto3 或 AWS CLI）
- [ ] 实现自动清理（保留 30 天）
- [ ] 编写恢复测试脚本 `scripts/restore.sh`

**验收标准**:
- 备份成功率 100%
- 恢复流程 <15 分钟
- S3 存储正常
- MD5 校验通过

**依赖**: 1.2
**风险**: S3 配置需要 AWS 账号和 IAM 权限

**应对方案**:
- 提前准备 MinIO 自托管方案
- 使用 AWS CLI 预配置 IAM 角色
- 临时改为本地备份 + 手动上传

---

### M1 总结

**总工时**: 68 小时
**关键路径**: 1.2 → 1.4 → 1.5
**里程碑交付**: 可通过 API 完成核心操作，备份机制可用
**技术债务**: 暂未实现在线 API (dictionaryapi.dev) 集成，留待 M2

---

## M2 里程碑: PWA 前端开发 (2.25 周 / 90 小时)

**目标**: 构建 Vue 3 + PWA 前端，实现离线支持和四层数据源降级策略

### 2.1 Vue 3 项目搭建与基础配置 (8h)

- [ ] 使用 Vite 创建 Vue 3 项目
  ```bash
  npm create vite@latest frontend -- --template vue
  ```
- [ ] 安装依赖:
  - Vue Router (路由)
  - Pinia (状态管理)
  - Tailwind CSS (样式)
  - Axios (HTTP 客户端)
- [ ] 配置 Tailwind (含暗色模式)
- [ ] 配置 Vite proxy 连接后端 API
  ```js
  // vite.config.js
  export default {
    server: {
      proxy: {
        '/api': 'http://localhost:8000'
      }
    }
  }
  ```
- [ ] 配置 ESLint + Prettier

**验收标准**:
- 开发服务器启动，可访问首页
- Tailwind 样式生效
- 可调用后端 API

**依赖**: M1 完成
**风险**: 无

---

### 2.2 核心页面开发 - 复习会话 (20h) ⭐ 关键路径

- [ ] 实现闪卡组件（正反面切换、逐步揭示）
- [ ] 实现四档评分按钮 (Again/Hard/Good/Easy)
- [ ] 添加键盘快捷键:
  - 1: Again
  - 2: Hard
  - 3: Good
  - 4 或 Space: Easy
- [ ] 实现撤销功能 (Undo)
- [ ] 接入后端复习队列 API (`GET /api/review/queue/`)
- [ ] 实现评分提交 (`POST /api/review/submit/`)
- [ ] 实现响应时长记录
- [ ] 添加 TTS 播放按钮 (Web Speech API)
- [ ] 编写组件测试 (Vitest)

**验收标准**:
- 复习翻面 <100ms
- 键盘操作全流程可完成
- 移动端单手可用
- 组件测试覆盖率 ≥80%

**依赖**: 2.1, M1.4
**技术决策**: 使用 Vue 3 Composition API 优化性能

---

### 2.3 核心页面开发 - 条目录入 (15h)

- [ ] 实现条目表单（英语/汉字模式切换）
- [ ] 实现失焦自动补全触发
- [ ] 实现多候选弹窗（多音字/多义词）
- [ ] 实现操作选项: 补全/覆盖/合并/跳过
- [ ] 接入后端 ECDICT/UniHan API
  - `GET /api/dict/en/{word}`
  - `GET /api/dict/zh/{hanzi}`
- [ ] 编写表单验证逻辑
- [ ] 添加加载状态和错误提示

**验收标准**:
- 自动补全触发延迟 <500ms
- 失败降级不阻塞保存
- 表单验证准确
- 多候选交互流畅

**依赖**: 2.1, M1.5, M1.6
**风险**: 多候选交互复杂度高

---

### 2.4 PWA 基础设施搭建 (12h) ⭐ 关键路径

- [ ] 安装 Workbox 插件
  ```bash
  npm install -D vite-plugin-pwa
  ```
- [ ] 配置 Service Worker 缓存策略:
  ```js
  // vite.config.js
  import { VitePWA } from 'vite-plugin-pwa'

  export default {
    plugins: [
      VitePWA({
        registerType: 'autoUpdate',
        workbox: {
          runtimeCaching: [
            {
              urlPattern: /^https:\/\/api\//,
              handler: 'NetworkFirst',
              options: {
                cacheName: 'api-cache',
                expiration: {
                  maxEntries: 100,
                  maxAgeSeconds: 86400 // 1 天
                }
              }
            },
            {
              urlPattern: /\.(js|css|png|jpg|svg)$/,
              handler: 'CacheFirst'
            }
          ]
        }
      })
    ]
  }
  ```
- [ ] 配置 manifest.json (名称、图标、主题色)
- [ ] 实现离线检测 UI 提示
- [ ] 测试 PWA 安装流程 (Chrome/Safari)

**验收标准**:
- PWA 可安装到主屏幕
- 离线时核心页面可访问
- 缓存策略生效

**依赖**: 2.1
**风险**: iOS Safari 对 PWA 支持有限 (Service Worker 限制)

---

### 2.5 IndexedDB 本地缓存实现 (L1 数据源) (10h)

- [ ] 使用 Dexie.js 封装 IndexedDB 操作
  ```js
  import Dexie from 'dexie'

  const db = new Dexie('RPD')
  db.version(1).stores({
    dict_cache: 'word, data, timestamp'
  })
  ```
- [ ] 设计表结构:
  - word/hanzi (主键)
  - data (JSON 数据)
  - timestamp (缓存时间)
- [ ] 实现缓存写入逻辑 (TTL 30 天)
- [ ] 实现缓存查询逻辑 (优先级最高)
- [ ] 实现缓存失效清理
- [ ] 编写单元测试

**验收标准**:
- 缓存命中延迟 <100ms
- TTL 过期自动清理
- 缓存容量上限控制 (10MB)

**依赖**: 2.4
**技术决策**: 使用 Dexie.js 简化 IndexedDB 操作

---

### 2.6 离线队列与后台同步 (15h) ⭐ 关键路径

- [ ] 实现离线操作队列 (新增卡片、评分记录)
  ```js
  // 使用 IndexedDB 存储离线操作
  db.version(1).stores({
    offline_queue: '++id, type, data, timestamp'
  })
  ```
- [ ] 使用 Background Sync API 自动同步
  ```js
  navigator.serviceWorker.ready.then(registration => {
    registration.sync.register('sync-offline-queue')
  })
  ```
- [ ] 实现同步冲突检测 (后来者优先)
- [ ] 实现同步状态 UI (同步中/成功/失败)
- [ ] 编写同步失败重试逻辑

**验收标准**:
- 离线操作不丢失
- 网络恢复后自动同步
- 冲突提示清晰
- 重试机制生效

**依赖**: 2.4
**风险**: Background Sync API 浏览器兼容性 (iOS 不支持)

**应对方案**:
- 采用"后来者优先" + UI 提示策略
- M2 早期进行多设备测试
- 仅同步新增卡片，评分记录改为覆盖

---

### 2.7 在线 API 集成 (L3 数据源) (10h)

- [ ] 封装 dictionaryapi.dev 调用
  ```js
  async function fetchOnlineDict(word) {
    const res = await fetch(`https://api.dictionaryapi.dev/api/v2/entries/en/${word}`)
    return res.json()
  }
  ```
- [ ] 实现四层降级逻辑:
  ```
  L1 (IndexedDB) 未命中
    ↓
  L2 (本地字典 API) 查询
    ↓
  L3 (在线 API) 调用
    ↓
  L4 (手动填写) UI 保持可用
  ```
- [ ] 添加请求超时 (1.2s)
- [ ] 实现 CORS 处理
- [ ] 编写降级逻辑测试

**验收标准**:
- 四层降级策略按预期工作
- 在线 API 查询 P95 <1200ms
- 失败不影响核心使用
- 自动补全可用性 ≥99%

**依赖**: 2.5, M1.5
**风险**: dictionaryapi.dev 可能限流或下线

---

### M2 总结

**总工时**: 90 小时
**关键路径**: 2.2 → 2.4 → 2.6
**里程碑交付**: 可离线使用的 PWA 应用，核心功能闭环
**技术债务**: 性能优化（代码分割、CDN）留待 M3

---

## M3 里程碑: 优化与增强 (1.5 周 / 60 小时)

**目标**: 完成辅助功能、性能优化、多音字推断

### 3.1 统计面板开发 (10h)

- [ ] 实现今日面板 (完成数/正确率/耗时)
- [ ] 实现未来 7/30 天任务预测曲线 (使用 Chart.js)
- [ ] 实现连续打卡天数 (Streak)
- [ ] 实现难项排行榜 (lapses 降序)
- [ ] 实现记忆稳定度趋势图 (S 值变化)

**验收标准**:
- 指标与日志一致
- 图表渲染流畅
- 移动端适配

**依赖**: M2 完成
**风险**: 无

---

### 3.2 内容管理功能 (12h)

- [ ] 实现高级检索 (Deck/Tag/State/Due/难度筛选)
- [ ] 实现批量操作 (标签/移动/删除/重排程)
- [ ] 实现重复检测 (语义指纹 + 编辑距离)
  ```js
  function semanticHash(card) {
    const content = `${card.word}${card.meaning}${card.examples.join('')}`
    return md5(content.toLowerCase().replace(/\s+/g, ''))
  }
  ```
- [ ] 实现历史记录可视化
- [ ] 添加分页和虚拟滚动 (1000+ 条目)

**验收标准**:
- 1000 条目列表 P95 <500ms
- 批量操作无卡顿
- 重复检测准确率 ≥95%

**依赖**: M2 完成
**技术决策**: 使用 virtual-scroller 优化长列表

---

### 3.3 多音字语境推断 (12h) ⭐ P1 优化

- [ ] 安装 jieba-js 分词库
  ```bash
  npm install nodejieba
  ```
- [ ] 实现语境分析函数 (提取当前字所在词)
  ```js
  import jieba from 'nodejieba'

  function inferPinyin(char, context) {
    const words = jieba.cut(context)
    for (const word of words) {
      if (word.includes(char)) {
        return PINYIN_DICT[word]?.[char]
      }
    }
    return null // 降级为候选面板
  }
  ```
- [ ] 建立词-读音映射表 (扩展 UniHan 数据)
- [ ] 实现推断逻辑 (词库匹配 → 词性标注)
- [ ] 失败时显示候选面板
- [ ] 编写推断准确率测试

**验收标准**:
- 常见词语境推断准确率 ≥85%
- 推断延迟 <200ms
- 失败降级正常

**依赖**: M1.6, M2.3
**风险**: jieba-js 性能可能不如 Python 版本

**应对方案**:
- 使用更大的词-读音映射表
- 失败时自动降级为候选面板
- 完全依赖候选面板手动选择

---

### 3.4 性能优化 (15h) ⭐ P1 优化

- [ ] 代码分割 (按路由懒加载)
  ```js
  const routes = [
    {
      path: '/review',
      component: () => import('./views/Review.vue')
    }
  ]
  ```
- [ ] 配置 CDN (Cloudflare 或阿里云)
- [ ] 启用 Gzip/Brotli 压缩
  ```nginx
  # nginx.conf
  gzip on;
  gzip_types text/plain text/css application/json application/javascript;
  ```
- [ ] 优化 Django 缓存 (Redis 或 Memcached)
- [ ] 添加数据库查询索引
- [ ] 图片压缩和 WebP 转换
- [ ] 使用 Lighthouse 测试并优化

**验收标准**:
- 首屏加载 P95 <900ms
- Lighthouse 性能分数 ≥85
- API 响应 P99 <500ms

**依赖**: M2 完成
**技术决策**: 使用 Vite 自动代码分割

**应对方案**:
- M2 结束时提前进行 Lighthouse 测试
- 预留额外 5 小时调优时间
- 放宽指标至 <1200ms，标记为技术债务

---

### 3.5 导入导出功能 (8h)

- [ ] 实现 CSV/JSON 导入解析
- [ ] 实现 Anki 格式兼容
  ```
  字段映射: word → Front, meaning → Back, tags → Tags
  ```
- [ ] 实现语义指纹冲突检测
- [ ] 实现导出功能 (CSV/JSON)
- [ ] 添加导入进度条

**验收标准**:
- 导入 1000 行 ≤5s
- 冲突检测准确率 ≥95%
- 导出数据可复算

**依赖**: M2 完成, 3.2
**风险**: Anki 格式映射复杂

---

### 3.6 提醒机制 (3h)

- [ ] 实现 PWA 推送通知请求
  ```js
  Notification.requestPermission().then(permission => {
    if (permission === 'granted') {
      new Notification('今日复习提醒')
    }
  })
  ```
- [ ] 配置时间窗口 (20:00-22:00)
- [ ] 实现邮件提醒降级 (可选)
- [ ] 添加关闭开关

**验收标准**:
- 推送通知正常触发
- 用户可完全禁用

**依赖**: M2.4
**风险**: iOS 推送通知限制多

---

### M3 总结

**总工时**: 60 小时
**关键路径**: 3.3 → 3.4
**里程碑交付**: 功能完整的 v2.0 版本
**技术债务**: FSRS 算法、Azure TTS 留待 M4

---

## 测试策略

### 单元测试 (覆盖率目标 ≥85%)

**后端 (pytest + pytest-django):**
- 模型层: 测试 SM-2 算法逻辑、队列生成
- API 层: 测试所有端点的 CRUD 操作
- 服务层: 测试字典查询、备份逻辑

**前端 (Vitest + Vue Test Utils):**
- 组件测试: 闪卡、表单、统计图表
- 工具函数: 四层降级逻辑、语义指纹算法
- 状态管理: Pinia store 测试

### 集成测试

**E2E 测试 (Playwright):**
- 关键用户流程: 注册 → 录入 → 复习 → 统计
- PWA 离线场景: 断网操作 → 恢复同步
- 多设备同步: 模拟冲突解决

### 性能测试

- **Lighthouse CI**: 每次构建运行，性能分数 <85 则失败
- **API 压测 (Locust)**: 模拟 10 并发用户，验证 P99 <500ms
- **数据库查询分析**: 使用 Django Debug Toolbar 检测 N+1 查询

### 测试覆盖率门槛

- 后端: ≥85% (pytest-cov)
- 前端: ≥80% (Vitest coverage)
- E2E: 覆盖 12 个验收清单场景

---

## 部署流程

### 开发环境

```bash
# 后端
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver

# 前端
cd frontend
npm install
npm run dev
```

### 生产部署 (Docker Compose)

**docker-compose.yml**:
```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    command: gunicorn config.wsgi:application --bind 0.0.0.0:8000
    volumes:
      - db_data:/app/db
    environment:
      - DATABASE_URL=sqlite:////app/db/db.sqlite3
      - AWS_S3_BUCKET=rpd-backup

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./frontend/dist:/usr/share/nginx/html
    depends_on:
      - backend

  cron:
    build: ./backend
    command: crond -f
    volumes:
      - db_data:/app/db
      - /etc/crontab:/etc/crontab
    environment:
      - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
      - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}

volumes:
  db_data:
```

**部署步骤**:
```bash
# 1. 构建前端
cd frontend && npm run build

# 2. 构建镜像
docker-compose build

# 3. 启动服务
docker-compose up -d

# 4. 运行迁移
docker-compose exec backend python manage.py migrate

# 5. 创建超级用户
docker-compose exec backend python manage.py createsuperuser

# 6. 验证备份
docker-compose logs cron
```

### CI/CD 流水线 (GitHub Actions)

```yaml
name: CI/CD
on: [push]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Backend Tests
        run: |
          cd backend
          pip install -r requirements.txt
          pytest --cov --cov-fail-under=85

      - name: Frontend Tests
        run: |
          cd frontend
          npm install
          npm run test:coverage

  deploy:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Server
        run: |
          ssh user@server 'cd /app && git pull && docker-compose up -d --build'
```

---

## 风险应对预案

### 高风险项 (P0)

#### 风险 1: ECDICT 导入失败或性能不达标

**概率**: 中 (30%)
**影响**: 严重 (阻塞 M1 交付)

**缓解措施**:
- M1 第一周完成 POC 验证
- 准备 Plan B: 使用 StarDict 格式字典
- 性能不达标时使用 Redis 缓存

**应急方案**:
- 降级为仅在线 API (L3)，牺牲离线能力

---

#### 风险 2: PWA 离线队列同步冲突频发

**概率**: 中 (40%)
**影响**: 中 (用户体验下降)

**缓解措施**:
- 采用"后来者优先" + UI 提示策略
- M2 早期进行多设备测试

**应急方案**:
- 仅同步新增卡片，评分记录改为覆盖

---

#### 风险 3: S3 备份配置复杂，上线延期

**概率**: 低 (20%)
**影响**: 中 (可暂时降级)

**缓解措施**:
- 提前准备 MinIO 自托管方案
- 使用 AWS CLI 预配置 IAM 角色

**应急方案**:
- 临时改为本地备份 + 手动上传

---

### 中风险项 (P1)

#### 风险 4: 性能优化未达 P95 <900ms

**概率**: 中 (30%)
**影响**: 中 (不阻塞上线)

**缓解措施**:
- M2 结束时提前进行 Lighthouse 测试
- 预留 M3 额外 5 小时调优时间

**应急方案**:
- 放宽指标至 <1200ms，标记为技术债务

---

#### 风险 5: 多音字推断准确率不达标

**概率**: 中 (35%)
**影响**: 低 (可降级)

**缓解措施**:
- 使用更大的词-读音映射表
- 失败时自动降级为候选面板

**应急方案**:
- 完全依赖候选面板手动选择

---

## M4 可选扩展 (未计入核心计划)

### 4.1 FSRS 算法集成 (20h)

- [ ] 研究 FSRS-rs Rust 实现
- [ ] 使用 PyO3 绑定到 Python
- [ ] 迁移现有复习记录训练模型
- [ ] A/B 测试对比 SM-2 vs FSRS

### 4.2 Azure TTS 集成 (6h)

- [ ] 注册 Azure 认知服务
- [ ] 实现 TTS API 调用
- [ ] 替换 Web Speech API
- [ ] 添加语音缓存

---

## 项目总结

### 总工时

**218 小时 (5.45 周 @ 40h/周)**

### 关键路径 (影响交付时间)

```
M1.2 (数据模型) → M1.4 (SM-2 算法) → M1.5 (ECDICT)
    ↓
M2.2 (复习会话) → M2.4 (PWA 基础) → M2.6 (离线同步)
    ↓
M3.3 (多音字推断) → M3.4 (性能优化)
```

### 优先级

- **P0 (必须)**: M1.4, M1.5, M1.7, M2.4, M2.6
- **P1 (强烈建议)**: M2.2, M3.3, M3.4
- **P2 (可选)**: M3.1, M3.6

### 成功标准

- [ ] 12 个验收清单全部通过
- [ ] 性能指标达标 (首屏 <900ms, API <500ms)
- [ ] PWA 可离线使用
- [ ] 自动补全可用性 ≥99%
- [ ] 测试覆盖率 ≥85%

### 下一步行动

1. **立即开始**: M1.1 环境搭建
2. **第 3 天**: M1.5 ECDICT POC 验证
3. **每周五**: 里程碑回顾会议

---

**文档版本**: v1.0
**生成时间**: 2025-11-18
**基于**: RPD v2.0 文档
