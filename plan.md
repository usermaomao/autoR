# 项目实施计划 - 基于艾宾浩斯记忆曲线的词汇/生字学习网站 v2.0 (网页版)

## 项目概览

**项目名称**: 基于艾宾浩斯记忆曲线的词汇/生字学习网站
**版本**: v2.0 (Web 架构版)
**目标用户**: ≤10 人自用、小团队
**总工时**: 164 小时 (4.1 周 @ 40h/周)
**核心价值**: 科学复习算法、智能字典、桌面优先、高可用

### 技术栈

```
后端:  Django 5 + Django REST Framework + SQLite
前端:  Vue 3 + Vite + Tailwind CSS + Pinia
缓存:  localStorage (客户端) + Django Cache (服务端)
数据:  ECDICT (77万词条) + UniHan Database + dictionaryapi.dev
部署:  Docker Compose + Nginx + S3/MinIO 备份
```

### 关键优化点 (相比 v1.0)

**P0 必须修复:**
1. 本地字典降级方案 (三层: ECDICT/UniHan → 在线 API → 手动)
2. 完整 SM-2 算法 (引入 EF + D 参数)
3. 自动备份机制 (Django management command + S3 异地容灾)

**P1 强烈建议:**
4. 性能优化 (首屏 P95 <1200ms)
5. 多音字语境推断 (后端 jieba 分词)
6. 键盘快捷键增强

**网页版简化 (相比 PWA 版):**
- ❌ 移除 PWA 离线支持 (Service Worker + IndexedDB)
- ❌ 移除 Background Sync (离线队列同步)
- ✅ 简化为 localStorage 缓存
- ✅ 减少 25% 工时 (218h → 164h)

---

## 里程碑时间线

```
+----------------+----------------+----------------+
|  M1 (1.7 周)   |  M2 (1.2 周)   |  M3 (1.2 周)   |
|   后端基础     |   Web 前端     |   优化增强     |
|   68 小时      |   48 小时      |   48 小时      |
+----------------+----------------+----------------+
      |                 |                 |
      v                 v                 v
 数据模型+算法      Vue3+三层数据源    性能+多音字
 ECDICT+备份        键盘快捷键         统计+导入导出
```

**关键路径** (影响交付时间):
```
M1.2 (数据模型) → M1.4 (SM-2 算法) → M1.5 (ECDICT)
    ↓
M2.2 (复习会话) → M2.3 (条目录入) → M2.4 (字典集成)
    ↓
M3.2 (多音字推断) → M3.3 (性能优化)
```

---

## M1 里程碑: 后端基础设施 (1.7 周 / 68 小时)

**目标**: 搭建后端基础设施，集成核心算法和数据源，建立自动化备份机制

### 1.1 环境搭建与项目初始化 (6h)

- [ ] 创建 Django 5 项目，配置虚拟环境
  ```bash
  mkdir backend && cd backend
  python3 -m venv venv
  source venv/bin/activate
  django-admin startproject config .
  ```
- [ ] 安装依赖:
  - Django 5.0
  - djangorestframework
  - django-cors-headers
  - django-extensions
  - jieba (分词)
  - pypinyin (拼音)
- [ ] 配置 SQLite 数据库（启用 WAL 模式提升并发）
  ```python
  # settings.py
  DATABASES = {
      'default': {
          'ENGINE': 'django.db.backends.sqlite3',
          'NAME': BASE_DIR / 'db' / 'db.sqlite3',
          'OPTIONS': {
              'init_command': 'PRAGMA journal_mode=WAL;'
          }
      }
  }
  ```
- [ ] 配置 CORS (允许前端访问)
- [ ] 配置 Git、.gitignore、pre-commit hooks
- [ ] 创建 requirements.txt

**验收标准**:
- `python manage.py runserver` 成功启动
- Django Admin 可访问
- CORS 配置生效

**依赖**: 无
**风险**: 无

---

### 1.2 数据模型设计与迁移 (8h)

- [ ] 设计核心模型:
  - **User** (Django 自带)
  - **Deck** (卡组)
  - **Card** (卡片)
  - **ReviewLog** (复习记录)

- [ ] Card 模型字段:
  ```python
  class Card(models.Model):
      user = models.ForeignKey(User, on_delete=models.CASCADE)
      deck = models.ForeignKey(Deck, on_delete=models.CASCADE)

      # 通用字段
      word = models.CharField(max_length=200)  # 单词/汉字
      card_type = models.CharField(choices=[('en', '英语'), ('zh', '汉字')])

      # SM-2 算法字段
      ef = models.FloatField(default=2.5)  # 易忘因子
      interval = models.IntegerField(default=0)  # 间隔天数
      difficulty = models.FloatField(default=0)  # 难度
      stability = models.FloatField(default=0)  # 稳定度
      lapses = models.IntegerField(default=0)  # 错误次数
      due_at = models.DateTimeField()  # 下次复习时间

      # 语言特定字段 (JSON)
      metadata = models.JSONField(default=dict)
      # 英语: {ipa, pos, meaning, examples, frequency, cefr}
      # 汉字: {pinyin, radical, strokes, simplified, traditional}

      # 用户自定义
      tags = models.JSONField(default=list)
      notes = models.TextField(blank=True)

      created_at = models.DateTimeField(auto_now_add=True)
      updated_at = models.DateTimeField(auto_now=True)
  ```

- [ ] 创建数据库索引:
  ```python
  class Meta:
      indexes = [
          models.Index(fields=['user', 'due_at']),
          models.Index(fields=['user', 'deck']),
          models.Index(fields=['word']),
      ]
  ```

- [ ] 编写 migration 并测试
- [ ] 注册到 Django Admin

**验收标准**:
- 所有模型可在 Django Admin 中 CRUD
- 数据库索引生效 (使用 `EXPLAIN QUERY PLAN`)
- migration 可回滚

**依赖**: 1.1
**技术决策**: 使用 JSONField 存储语言特定字段（灵活性高，避免多表关联）

---

### 1.3 DRF API 开发 - 认证与 CRUD (10h)

- [ ] 配置 DRF 基础:
  ```python
  # settings.py
  REST_FRAMEWORK = {
      'DEFAULT_AUTHENTICATION_CLASSES': [
          'rest_framework.authentication.SessionAuthentication',
      ],
      'DEFAULT_PERMISSION_CLASSES': [
          'rest_framework.permissions.IsAuthenticated',
      ],
      'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
      'PAGE_SIZE': 50,
  }
  ```

- [ ] 实现用户注册/登录 API:
  - `POST /api/auth/register/`
  - `POST /api/auth/login/`
  - `POST /api/auth/logout/`

- [ ] 实现 Deck CRUD 接口:
  - `GET /api/decks/` (列表)
  - `POST /api/decks/` (创建)
  - `GET /api/decks/{id}/` (详情)
  - `PUT /api/decks/{id}/` (更新)
  - `DELETE /api/decks/{id}/` (删除)

- [ ] 实现 Card CRUD 接口:
  - `GET /api/cards/` (列表，支持过滤)
  - `POST /api/cards/` (创建)
  - `GET /api/cards/{id}/` (详情)
  - `PUT /api/cards/{id}/` (更新)
  - `DELETE /api/cards/{id}/` (删除)

- [ ] 添加分页、过滤、搜索:
  ```python
  # filters.py
  class CardFilter(django_filters.FilterSet):
      deck = django_filters.NumberFilter()
      card_type = django_filters.ChoiceFilter(choices=[('en', '英语'), ('zh', '汉字')])
      tags = django_filters.CharFilter(method='filter_tags')
      search = django_filters.CharFilter(method='search_cards')
  ```

- [ ] 编写 API 单元测试（覆盖率 ≥80%）
  ```python
  # tests/test_api.py
  class CardAPITestCase(APITestCase):
      def test_create_card(self):
          response = self.client.post('/api/cards/', {...})
          self.assertEqual(response.status_code, 201)
  ```

**验收标准**:
- Postman/curl 可完成所有 CRUD 操作
- API 响应 P99 <500ms (使用 Django Debug Toolbar 测量)
- 单元测试通过 (`pytest --cov`)
- API 文档自动生成 (使用 drf-spectacular)

**依赖**: 1.2
**风险**: 无

---

### 1.4 完整 SM-2 算法实现 (15h) ⭐ 关键路径

- [ ] 实现 EF 计算公式:
  ```python
  # services/sm2.py
  def calculate_ef(current_ef: float, quality: int) -> float:
      """
      计算新的易忘因子 (Easiness Factor)
      quality: 0=Again, 2=Hard, 4=Good, 5=Easy
      """
      new_ef = current_ef + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
      return max(1.3, new_ef)  # 最小值 1.3
  ```

- [ ] 实现间隔计算:
  ```python
  def calculate_interval(current_interval: int, ef: float, quality: int) -> int:
      """计算新的复习间隔（天数）"""
      if quality < 3:  # Again/Hard → 回到学习阶段
          return 0

      if current_interval == 0:
          return 1  # 第一次复习: 1 天
      elif current_interval == 1:
          return 6  # 第二次复习: 6 天
      else:
          return int(current_interval * ef)
  ```

- [ ] 实现学习小步:
  ```python
  LEARNING_STEPS = [10, 1440]  # 10 分钟, 1 天 (分钟)

  def get_next_learning_step(card: Card, quality: int):
      if quality == 0:  # Again
          card.learning_step = 0
          return timedelta(minutes=LEARNING_STEPS[0])
      else:
          card.learning_step += 1
          if card.learning_step >= len(LEARNING_STEPS):
              # 进入复习阶段
              card.state = 'review'
              return timedelta(days=calculate_interval(...))
          return timedelta(minutes=LEARNING_STEPS[card.learning_step])
  ```

- [ ] 实现队列生成逻辑:
  ```python
  def generate_review_queue(user_id: int, limit: int = 50) -> List[Card]:
      """
      生成复习队列
      优先级: 到期卡片 > 难项 > 新卡
      """
      now = timezone.now()

      # 1. 到期的复习卡片（按到期时间排序）
      due_cards = Card.objects.filter(
          user_id=user_id,
          state='review',
          due_at__lte=now
      ).order_by('due_at', '-lapses')[:limit]

      # 2. 难项优先（lapses ≥ 3）
      leech_cards = Card.objects.filter(
          user_id=user_id,
          lapses__gte=3
      ).order_by('-lapses')[:10]

      # 3. 新卡（根据 daily_new_limit）
      config = get_user_config(user_id)
      new_cards = Card.objects.filter(
          user_id=user_id,
          state='new'
      ).order_by('created_at')[:config.daily_new_limit]

      # 合并去重
      queue = list(dict.fromkeys([*leech_cards, *due_cards, *new_cards]))
      return queue[:limit]
  ```

- [ ] 实现难项标记:
  ```python
  def mark_leech(card: Card):
      if card.lapses >= 3:
          card.tags.append('leech')
          # 发送通知或标记
  ```

- [ ] 实现评分提交接口:
  ```python
  # views.py
  @api_view(['POST'])
  def submit_review(request):
      card_id = request.data['card_id']
      quality = request.data['quality']  # 0-5

      card = Card.objects.get(id=card_id)

      # 更新 SM-2 参数
      card.ef = calculate_ef(card.ef, quality)
      card.interval = calculate_interval(card.interval, card.ef, quality)
      card.due_at = timezone.now() + timedelta(days=card.interval)

      if quality < 3:
          card.lapses += 1

      card.save()

      # 记录日志
      ReviewLog.objects.create(card=card, quality=quality, ...)

      return Response({'next_due': card.due_at})
  ```

- [ ] 编写算法单元测试（覆盖边界情况）:
  ```python
  def test_ef_calculation():
      assert calculate_ef(2.5, 5) == 2.6
      assert calculate_ef(2.5, 0) >= 1.3  # 最小值

  def test_queue_generation():
      queue = generate_review_queue(user_id=1, limit=20)
      assert len(queue) <= 20
      # 验证优先级正确
  ```

**验收标准**:
- 队列生成 ≤300ms (1000 卡片)
- 评分后即时更新 due_at、EF、interval
- 算法参数可通过配置调整
- 单元测试覆盖率 ≥90%
- 难项自动标记

**依赖**: 1.3
**风险**: 算法复杂，需要充分测试

**应对方案**:
- 增加测试时间 (+3h)
- 准备边界用例清单
- 使用 Anki 作为参考实现

---

### 1.5 ECDICT 本地字典集成 (12h) ⭐ 关键路径

- [ ] 下载 ECDICT 开源数据:
  - 仓库: https://github.com/skywind3000/ECDICT
  - 数据量: 77 万词条
  - 下载 `stardict.csv` 或 `ecdict.db`

- [ ] 预处理: 导入到 SQLite，建立 FTS5 全文搜索索引:
  ```python
  # scripts/import_ecdict.py
  import sqlite3
  from tqdm import tqdm

  def import_ecdict(source_path, target_db):
      conn = sqlite3.connect(target_db)
      cursor = conn.cursor()

      # 启用 WAL 模式和批量优化
      cursor.execute("PRAGMA journal_mode=WAL")
      cursor.execute("PRAGMA synchronous=NORMAL")

      # 创建表
      cursor.execute("""
          CREATE TABLE IF NOT EXISTS ecdict (
              word TEXT PRIMARY KEY,
              phonetic TEXT,
              definition TEXT,
              translation TEXT,
              pos TEXT,
              collins INTEGER,
              oxford INTEGER,
              tag TEXT,
              bnc INTEGER,
              frq INTEGER,
              exchange TEXT
          )
      """)

      # 批量导入
      with open(source_path, 'r', encoding='utf-8') as f:
          batch = []
          for line in tqdm(f, desc="导入 ECDICT"):
              # 解析 CSV
              parts = line.strip().split('\t')
              batch.append(parts)

              if len(batch) >= 5000:
                  cursor.executemany("INSERT OR IGNORE INTO ecdict VALUES (?,?,?,?,?,?,?,?,?,?,?)", batch)
                  conn.commit()
                  batch = []

      # 创建 FTS5 索引
      cursor.execute("""
          CREATE VIRTUAL TABLE ecdict_fts USING fts5(
              word, definition, translation,
              content='ecdict'
          )
      """)
      cursor.execute("INSERT INTO ecdict_fts SELECT word, definition, translation FROM ecdict")

      conn.commit()
      print(f"导入完成，共 {cursor.execute('SELECT COUNT(*) FROM ecdict').fetchone()[0]} 词条")
  ```

- [ ] 实现查询 API: `GET /api/dict/en/{word}`
  ```python
  # views.py
  @api_view(['GET'])
  def lookup_english(request, word):
      conn = sqlite3.connect(settings.ECDICT_DB_PATH)
      cursor = conn.cursor()

      result = cursor.execute(
          "SELECT * FROM ecdict WHERE word = ? COLLATE NOCASE",
          (word,)
      ).fetchone()

      if not result:
          return Response({'error': 'Not found'}, status=404)

      return Response({
          'word': result[0],
          'ipa': result[1],  # phonetic
          'pos': result[4],
          'meaning_en': result[2],  # definition
          'meaning_zh': result[3],  # translation
          'frequency': result[9],  # frq
          'cefr': extract_cefr(result[7]),  # 从 tag 提取
          'examples': []  # ECDICT 无例句，需额外来源
      })
  ```

- [ ] 性能优化: 添加查询缓存:
  ```python
  from django.core.cache import cache

  def lookup_with_cache(word):
      cache_key = f'dict:en:{word}'
      result = cache.get(cache_key)

      if not result:
          result = query_ecdict(word)
          cache.set(cache_key, result, timeout=86400)  # 1 天

      return result
  ```

- [ ] 编写集成测试:
  ```python
  def test_ecdict_lookup():
      response = client.get('/api/dict/en/hello')
      assert response.status_code == 200
      assert 'ipa' in response.data
  ```

**验收标准**:
- 常见词查询 P95 <600ms (网页版放宽标准)
- 覆盖率 ≥90% (测试 1000 个常见词)
- 数据库大小 <200MB
- 导入脚本可重复执行

**依赖**: 1.2
**风险**: ECDICT 数据量大，导入和索引耗时 (预计 30-45 分钟)

**应对方案**:
- M1 第一周完成 POC 验证
- 准备 Plan B: 使用 StarDict 格式字典
- 性能不达标时使用 Redis 缓存
- 提供预处理好的 SQLite 文件下载

---

### 1.6 UniHan 汉字数据库集成 (10h)

- [ ] 使用现有汉字数据库:
  - 项目已有 `data/hanzi_local.db` (4217 个汉字)
  - 无需重新下载 UniHan

- [ ] 编写查询 API: `GET /api/dict/zh/{hanzi}`
  ```python
  @api_view(['GET'])
  def lookup_hanzi(request, hanzi):
      conn = sqlite3.connect('data/hanzi_local.db')
      cursor = conn.cursor()

      result = cursor.execute(
          "SELECT * FROM hanzi WHERE char = ?",
          (hanzi,)
      ).fetchone()

      if not result:
          return Response({'error': '未找到该汉字'}, status=404)

      return Response({
          'char': result[0],
          'pinyin': result[1].split(','),  # 多音字数组
          'radical': result[2],
          'strokes': result[3],
          'frequency': result[4],
          'meaning_zh': result[5],
          'examples': result[6].split('|') if result[6] else []
      })
  ```

- [ ] 实现多音字推断接口 (后端 jieba):
  ```python
  import jieba
  from pypinyin import lazy_pinyin, Style

  @api_view(['POST'])
  def infer_pinyin(request):
      """基于语境推断多音字读音"""
      char = request.data['char']
      context = request.data.get('context', '')

      if not context:
          # 无语境，返回所有候选
          result = lookup_hanzi_raw(char)
          return Response({
              'char': char,
              'pinyin': None,
              'confidence': 0,
              'alternatives': result['pinyin']
          })

      # 使用 jieba 分词
      words = jieba.lcut(context)

      # 查找包含该字的词
      for word in words:
          if char in word:
              # 使用 pypinyin 获取词组读音
              pinyins = lazy_pinyin(word, style=Style.TONE)
              char_index = word.index(char)

              return Response({
                  'char': char,
                  'pinyin': pinyins[char_index],
                  'confidence': 0.9,  # 高置信度
                  'word': word,
                  'alternatives': lookup_hanzi_raw(char)['pinyin']
              })

      # 降级：使用字符级推断
      pinyin = lazy_pinyin(char, style=Style.TONE)[0]
      return Response({
          'char': char,
          'pinyin': pinyin,
          'confidence': 0.6,  # 中等置信度
          'alternatives': lookup_hanzi_raw(char)['pinyin']
      })
  ```

- [ ] 添加缓存:
  ```python
  @cache_page(86400)  # 1 天
  def lookup_hanzi(request, hanzi):
      ...
  ```

- [ ] 编写集成测试:
  ```python
  def test_hanzi_lookup():
      response = client.get('/api/dict/zh/中')
      assert response.status_code == 200
      assert 'pinyin' in response.data

  def test_pinyin_inference():
      response = client.post('/api/dict/zh/infer-pinyin', {
          'char': '长',
          'context': '长城很长'
      })
      assert response.data['pinyin'] == 'cháng'
      assert response.data['confidence'] > 0.8
  ```

**验收标准**:
- 常见字查询 P95 <300ms
- 覆盖率 ≥95% (GB2312 常用字 6763 个，现有 4217 个 = 62%)
- 多音字推断准确率 ≥90% (后端 jieba)

**依赖**: 1.2
**技术决策**: 多音字推断移至后端（Python jieba 性能更好）

---

### 1.7 自动备份机制实现 (7h)

- [ ] 编写备份 Django Management Command:
  ```python
  # management/commands/backup_db.py
  from django.core.management.base import BaseCommand
  import os
  import subprocess
  from datetime import datetime

  class Command(BaseCommand):
      help = '备份 SQLite 数据库到 S3'

      def handle(self, *args, **options):
          timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
          db_path = settings.DATABASES['default']['NAME']
          backup_dir = f'/tmp/backup_{timestamp}'
          os.makedirs(backup_dir, exist_ok=True)

          # 使用 SQLite 在线备份（不锁表）
          backup_path = f'{backup_dir}/db.sqlite3'
          subprocess.run([
              'sqlite3',
              db_path,
              f".backup '{backup_path}'"
          ], check=True)

          # 计算 MD5
          subprocess.run([
              'md5sum',
              backup_path,
              '>',
              f'{backup_dir}/checksum.md5'
          ], shell=True)

          # 上传到 S3
          s3_bucket = os.getenv('S3_BACKUP_BUCKET', 's3://rpd-backup')
          subprocess.run([
              'aws', 's3', 'cp',
              backup_path,
              f'{s3_bucket}/db_{timestamp}.sqlite3'
          ], check=True)

          self.stdout.write(self.style.SUCCESS(f'备份完成: {timestamp}'))

          # 清理 30 天前的备份
          subprocess.run([
              'find', '/tmp',
              '-name', 'backup_*',
              '-mtime', '+30',
              '-exec', 'rm', '-rf', '{}', ';'
          ])
  ```

- [ ] 配置 cron 任务（每日凌晨 2:00）:
  ```bash
  # 添加到 crontab
  0 2 * * * cd /app && /app/venv/bin/python manage.py backup_db >> /var/log/backup.log 2>&1
  ```

- [ ] 编写恢复脚本:
  ```python
  # management/commands/restore_db.py
  class Command(BaseCommand):
      help = '从 S3 恢复数据库'

      def add_arguments(self, parser):
          parser.add_argument('--date', type=str, help='备份日期 (YYYYMMDD)')

      def handle(self, *args, **options):
          date = options['date']
          # 从 S3 下载
          # 验证 MD5
          # 恢复数据库
  ```

- [ ] 添加备份状态监控:
  ```python
  # 记录备份状态到数据库
  class BackupLog(models.Model):
      timestamp = models.DateTimeField(auto_now_add=True)
      status = models.CharField(choices=[('success', '成功'), ('failed', '失败')])
      file_size = models.IntegerField()
      s3_path = models.CharField(max_length=500)
  ```

**验收标准**:
- 备份成功率 100%
- 恢复流程 <15 分钟
- S3 存储正常
- MD5 校验通过
- 备份日志可查询

**依赖**: 1.2
**风险**: S3 配置需要 AWS 账号和 IAM 权限

**应对方案**:
- 优先使用 Backblaze B2 (S3 兼容 + 免费额度 10GB)
- 提前准备 MinIO 自托管方案
- 临时改为本地备份 + 手动上传

---

### M1 总结

**总工时**: 68 小时
**关键路径**: 1.2 → 1.4 → 1.5
**里程碑交付**: 可通过 API 完成核心操作，备份机制可用
**技术债务**: 暂未实现在线 API (dictionaryapi.dev) 集成，留待 M2

---

## M2 里程碑: Web 前端开发 (1.2 周 / 48 小时)

**目标**: 构建 Vue 3 前端，实现三层数据源降级策略和核心交互

### 2.1 Vue 3 项目搭建与基础配置 (8h)

- [ ] 使用 Vite 创建 Vue 3 项目:
  ```bash
  npm create vite@latest frontend -- --template vue
  cd frontend
  npm install
  ```

- [ ] 安装依赖:
  ```bash
  npm install vue-router pinia
  npm install axios
  npm install -D tailwindcss postcss autoprefixer
  npx tailwindcss init -p
  ```

- [ ] 配置 Tailwind CSS:
  ```js
  // tailwind.config.js
  export default {
    content: [
      "./index.html",
      "./src/**/*.{vue,js,ts,jsx,tsx}",
    ],
    darkMode: 'class',  // 支持暗色模式
    theme: {
      extend: {},
    },
  }
  ```

- [ ] 配置 Vite proxy 连接后端 API:
  ```js
  // vite.config.js
  export default {
    server: {
      proxy: {
        '/api': {
          target: 'http://localhost:8000',
          changeOrigin: true,
        }
      }
    }
  }
  ```

- [ ] 配置 Vue Router:
  ```js
  // router/index.js
  import { createRouter, createWebHistory } from 'vue-router'

  const routes = [
    { path: '/', component: () => import('@/views/Home.vue') },
    { path: '/review', component: () => import('@/views/Review.vue') },
    { path: '/cards', component: () => import('@/views/Cards.vue') },
    { path: '/stats', component: () => import('@/views/Stats.vue') },
  ]

  export default createRouter({
    history: createWebHistory(),
    routes
  })
  ```

- [ ] 配置 Pinia 状态管理:
  ```js
  // stores/user.js
  import { defineStore } from 'pinia'

  export const useUserStore = defineStore('user', {
    state: () => ({
      user: null,
      isAuthenticated: false
    }),
    actions: {
      async login(username, password) { ... },
      logout() { ... }
    }
  })
  ```

- [ ] 配置 ESLint + Prettier
- [ ] 创建基础布局组件

**验收标准**:
- 开发服务器启动 (`npm run dev`)
- Tailwind 样式生效
- 可调用后端 API
- 路由切换正常

**依赖**: M1 完成
**风险**: 无

---

### 2.2 核心页面开发 - 复习会话 (18h) ⭐ 关键路径

- [ ] 实现闪卡组件 `FlashCard.vue`:
  ```vue
  <template>
    <div class="flashcard" :class="{ flipped: isFlipped }">
      <div class="flashcard-front">
        <h2>{{ card.word }}</h2>
        <button @click="flip">显示答案</button>
      </div>

      <div class="flashcard-back">
        <div class="answer">{{ card.metadata.meaning }}</div>
        <div class="examples">{{ card.metadata.examples }}</div>

        <div class="rating-buttons">
          <button @click="rate(0)" class="btn-again">再来 (1)</button>
          <button @click="rate(2)" class="btn-hard">困难 (2)</button>
          <button @click="rate(4)" class="btn-good">良好 (3)</button>
          <button @click="rate(5)" class="btn-easy">简单 (4)</button>
        </div>
      </div>
    </div>
  </template>
  ```

- [ ] 添加键盘快捷键:
  ```js
  // composables/useKeyboard.js
  export function useReviewHotkeys(rateCard, undo, showAnswer) {
    onMounted(() => {
      document.addEventListener('keydown', (e) => {
        if (e.target.tagName === 'INPUT') return

        switch(e.key) {
          case '1': rateCard(0); break  // Again
          case '2': rateCard(2); break  // Hard
          case '3': rateCard(4); break  // Good
          case '4':
          case ' ': rateCard(5); break  // Easy
          case 's': showAnswer(); break
          case 'z': undo(); break
        }
      })
    })
  }
  ```

- [ ] 实现撤销功能:
  ```js
  const reviewHistory = ref([])

  function undo() {
    if (reviewHistory.value.length === 0) return

    const lastReview = reviewHistory.value.pop()
    // 调用后端撤销接口
    await axios.post('/api/review/undo/', { review_id: lastReview.id })
    // 重新加载卡片
    loadCard(lastReview.card_id)
  }
  ```

- [ ] 接入后端复习队列 API:
  ```js
  async function loadQueue() {
    const response = await axios.get('/api/review/queue/', {
      params: { limit: 50 }
    })
    queue.value = response.data
    currentCard.value = queue.value[0]
  }
  ```

- [ ] 实现评分提交:
  ```js
  async function submitRating(quality) {
    const startTime = Date.now()

    await axios.post('/api/review/submit/', {
      card_id: currentCard.value.id,
      quality: quality,
      time_taken: Date.now() - startTime
    })

    reviewHistory.value.push({
      card_id: currentCard.value.id,
      quality,
      timestamp: Date.now()
    })

    nextCard()
  }
  ```

- [ ] 添加 TTS 播放按钮 (Web Speech API):
  ```js
  function playTTS(text, lang = 'en-US') {
    const utterance = new SpeechSynthesisUtterance(text)
    utterance.lang = lang
    speechSynthesis.speak(utterance)
  }
  ```

- [ ] 编写组件测试 (Vitest):
  ```js
  // FlashCard.test.js
  import { mount } from '@vue/test-utils'
  import FlashCard from '@/components/FlashCard.vue'

  test('翻转卡片', async () => {
    const wrapper = mount(FlashCard, { props: { card: mockCard } })
    await wrapper.find('.flip-btn').trigger('click')
    expect(wrapper.vm.isFlipped).toBe(true)
  })
  ```

**验收标准**:
- 复习翻面 <100ms
- 键盘操作全流程可完成
- 桌面/平板响应式适配
- 组件测试覆盖率 ≥80%
- 撤销功能正常

**依赖**: 2.1, M1.4
**技术决策**: 使用 Vue 3 Composition API 优化性能

---

### 2.3 核心页面开发 - 条目录入 (12h)

- [ ] 实现条目表单 `CardForm.vue`:
  ```vue
  <template>
    <form @submit.prevent="submitCard">
      <!-- 类型选择 -->
      <div class="type-switch">
        <button @click="cardType = 'en'">英语</button>
        <button @click="cardType = 'zh'">汉字</button>
      </div>

      <!-- 英语模式 -->
      <div v-if="cardType === 'en'">
        <input v-model="form.word" @blur="autoFill" placeholder="单词" />
        <div v-if="suggestions.length" class="suggestions">
          <button v-for="s in suggestions" @click="applySuggestion(s)">
            {{ s.word }} - {{ s.meaning }}
          </button>
        </div>
      </div>

      <!-- 汉字模式 -->
      <div v-else>
        <input v-model="form.word" @blur="autoFill" placeholder="汉字" />
        <div v-if="pinyinCandidates.length" class="pinyin-selector">
          <button v-for="p in pinyinCandidates" @click="selectPinyin(p)">
            {{ p }}
          </button>
        </div>
      </div>

      <textarea v-model="form.notes" placeholder="备注"></textarea>
      <button type="submit">保存</button>
    </form>
  </template>
  ```

- [ ] 实现失焦自动补全:
  ```js
  async function autoFill() {
    if (!form.word) return

    loading.value = true

    try {
      const result = await dictService.lookup(form.word, cardType.value)

      if (result.data) {
        suggestions.value = [result.data]

        if (cardType.value === 'zh') {
          // 多音字推断
          const inference = await axios.post('/api/dict/zh/infer-pinyin', {
            char: form.word,
            context: form.notes || ''
          })

          if (inference.data.confidence > 0.8) {
            form.pinyin = inference.data.pinyin
          } else {
            pinyinCandidates.value = inference.data.alternatives
          }
        }
      }
    } catch (error) {
      // 降级为手动填写
      suggestions.value = []
    } finally {
      loading.value = false
    }
  }
  ```

- [ ] 实现操作选项 (补全/覆盖/跳过):
  ```js
  function applySuggestion(suggestion, mode = 'merge') {
    if (mode === 'replace') {
      form.metadata = suggestion
    } else if (mode === 'merge') {
      form.metadata = { ...form.metadata, ...suggestion }
    }
    suggestions.value = []
  }
  ```

- [ ] 编写表单验证:
  ```js
  const rules = {
    word: { required: true, minLength: 1 },
    cardType: { required: true },
  }

  function validate() {
    if (!form.word) {
      showError('请输入单词或汉字')
      return false
    }
    return true
  }
  ```

**验收标准**:
- 自动补全触发延迟 <500ms
- 失败降级不阻塞保存
- 表单验证准确
- 多候选交互流畅

**依赖**: 2.1, M1.5, M1.6
**风险**: 多候选交互复杂度高

---

### 2.4 字典查询与缓存 (8h)

- [ ] 实现 localStorage 缓存工具:
  ```js
  // utils/cache.js
  export class LocalCache {
    constructor(namespace = 'rpd') {
      this.namespace = namespace
    }

    set(key, value, ttl = 7 * 24 * 60 * 60 * 1000) {
      const item = {
        value,
        expires: Date.now() + ttl
      }
      localStorage.setItem(`${this.namespace}:${key}`, JSON.stringify(item))
    }

    get(key) {
      const raw = localStorage.getItem(`${this.namespace}:${key}`)
      if (!raw) return null

      const item = JSON.parse(raw)
      if (Date.now() > item.expires) {
        this.remove(key)
        return null
      }
      return item.value
    }

    remove(key) {
      localStorage.removeItem(`${this.namespace}:${key}`)
    }

    clear() {
      Object.keys(localStorage)
        .filter(k => k.startsWith(this.namespace))
        .forEach(k => localStorage.removeItem(k))
    }
  }
  ```

- [ ] 实现三层降级字典服务:
  ```js
  // services/dictService.js
  import axios from 'axios'
  import { LocalCache } from '@/utils/cache'

  const cache = new LocalCache('dict')

  export async function lookupWord(word, type = 'en') {
    // L1: 检查 localStorage 缓存
    const cached = cache.get(`${type}:${word}`)
    if (cached) {
      return { source: 'cache', data: cached }
    }

    try {
      // L2: 后端 ECDICT/UniHan
      const res = await axios.get(`/api/dict/${type}/${word}`, { timeout: 2000 })
      cache.set(`${type}:${word}`, res.data)
      return { source: 'local-dict', data: res.data }

    } catch (error) {
      if (type === 'en') {
        try {
          // L3: 在线 API (仅英语)
          const res = await axios.get(
            `https://api.dictionaryapi.dev/api/v2/entries/en/${word}`,
            { timeout: 1500 }
          )
          const data = transformOnlineDict(res.data[0])
          cache.set(`${type}:${word}`, data)
          return { source: 'online-api', data }
        } catch {
          // L4: 手动填写
          return { source: 'manual', data: null }
        }
      }

      return { source: 'manual', data: null }
    }
  }

  function transformOnlineDict(apiData) {
    return {
      word: apiData.word,
      ipa: apiData.phonetic || '',
      meaning_en: apiData.meanings[0]?.definitions[0]?.definition || '',
      examples: apiData.meanings[0]?.definitions.slice(0, 3).map(d => d.example || '') || []
    }
  }
  ```

- [ ] 添加缓存管理界面:
  ```vue
  <!-- views/Settings.vue -->
  <template>
    <div class="cache-settings">
      <p>缓存大小: {{ cacheSize }} MB</p>
      <button @click="clearCache">清空缓存</button>
    </div>
  </template>

  <script setup>
  const cacheSize = computed(() => {
    let total = 0
    for (let key in localStorage) {
      if (key.startsWith('rpd:')) {
        total += localStorage[key].length
      }
    }
    return (total / 1024 / 1024).toFixed(2)
  })

  function clearCache() {
    new LocalCache().clear()
    alert('缓存已清空')
  }
  </script>
  ```

- [ ] 编写降级逻辑测试:
  ```js
  test('三层降级策略', async () => {
    // Mock 后端失败
    mock.onGet('/api/dict/en/test').networkError()

    // Mock 在线 API 成功
    mock.onGet(/dictionaryapi/).reply(200, mockOnlineData)

    const result = await lookupWord('test', 'en')
    expect(result.source).toBe('online-api')
  })
  ```

**验收标准**:
- 三层降级策略按预期工作
- 在线 API 查询 P95 <1500ms
- 失败不影响核心使用
- 自动补全可用性 ≥98%
- localStorage 容量控制在 5MB 内

**依赖**: 2.1, M1.5
**风险**: dictionaryapi.dev 可能限流或下线

**应对方案**:
- 提供手动填写兜底
- 后端字典覆盖常用词 (优先级高)

---

### M2 总结

**总工时**: 48 小时 (相比 PWA 版减少 42h)
**关键路径**: 2.2 → 2.3 → 2.4
**里程碑交付**: 可用的 Web 应用，核心功能闭环
**技术债务**: 性能优化（代码分割、CDN）留待 M3

**简化项**:
- ❌ 移除 PWA 基础设施 (12h)
- ❌ 移除 IndexedDB (8h)
- ❌ 移除 Background Sync (15h)
- ✅ 使用 localStorage (2h)

---

## M3 里程碑: 优化与增强 (1.2 周 / 48 小时)

**目标**: 完成辅助功能、性能优化、多音字推断

### 3.1 统计面板开发 (10h)

- [ ] 实现今日面板:
  ```vue
  <template>
    <div class="today-stats">
      <div class="stat-card">
        <h3>今日完成</h3>
        <p class="value">{{ todayStats.completed }}</p>
      </div>
      <div class="stat-card">
        <h3>正确率</h3>
        <p class="value">{{ todayStats.accuracy }}%</p>
      </div>
      <div class="stat-card">
        <h3>平均耗时</h3>
        <p class="value">{{ todayStats.avgTime }}s</p>
      </div>
    </div>
  </template>
  ```

- [ ] 实现未来 7/30 天任务预测曲线 (Chart.js):
  ```bash
  npm install chart.js vue-chartjs
  ```

  ```vue
  <script setup>
  import { Line } from 'vue-chartjs'
  import { Chart as ChartJS, LineElement, PointElement, LinearScale, CategoryScale } from 'chart.js'

  ChartJS.register(LineElement, PointElement, LinearScale, CategoryScale)

  const forecastData = ref({
    labels: ['今天', '明天', '后天', ...],
    datasets: [{
      label: '预计复习数',
      data: [20, 35, 40, 30, ...]
    }]
  })
  </script>
  ```

- [ ] 实现连续打卡天数 (Streak):
  ```js
  async function calculateStreak() {
    const logs = await axios.get('/api/review/logs/', {
      params: { days: 365 }
    })

    let streak = 0
    let currentDate = new Date()

    for (let log of logs.data) {
      if (isSameDay(log.date, currentDate)) {
        streak++
        currentDate.setDate(currentDate.getDate() - 1)
      } else {
        break
      }
    }

    return streak
  }
  ```

- [ ] 实现难项排行榜:
  ```js
  async function getLeechCards() {
    const response = await axios.get('/api/cards/', {
      params: {
        ordering: '-lapses',
        lapses__gte: 3,
        limit: 10
      }
    })
    return response.data
  }
  ```

- [ ] 实现记忆稳定度趋势图

**验收标准**:
- 指标与日志一致
- 图表渲染流畅
- 桌面/平板响应式适配

**依赖**: M2 完成
**风险**: 无

---

### 3.2 内容管理功能 (10h)

- [ ] 实现高级检索:
  ```vue
  <template>
    <div class="filters">
      <select v-model="filters.deck">
        <option value="">全部卡组</option>
        <option v-for="d in decks" :value="d.id">{{ d.name }}</option>
      </select>

      <select v-model="filters.state">
        <option value="">全部状态</option>
        <option value="new">新学</option>
        <option value="learning">学习中</option>
        <option value="review">复习</option>
      </select>

      <input v-model="filters.search" placeholder="搜索..." />
    </div>
  </template>
  ```

- [ ] 实现批量操作:
  ```js
  const selectedCards = ref([])

  async function batchDelete() {
    await axios.post('/api/cards/batch-delete/', {
      ids: selectedCards.value
    })
    loadCards()
  }

  async function batchAddTag(tag) {
    await axios.post('/api/cards/batch-update/', {
      ids: selectedCards.value,
      tags: { add: [tag] }
    })
  }
  ```

- [ ] 实现重复检测:
  ```js
  import md5 from 'md5'

  function semanticHash(card) {
    const content = `${card.word}${card.metadata.meaning}${card.metadata.examples.join('')}`
    return md5(content.toLowerCase().replace(/\s+/g, ''))
  }

  async function findDuplicates() {
    const cards = await axios.get('/api/cards/')
    const hashes = {}
    const duplicates = []

    for (let card of cards.data) {
      const hash = semanticHash(card)
      if (hashes[hash]) {
        duplicates.push([hashes[hash], card])
      } else {
        hashes[hash] = card
      }
    }

    return duplicates
  }
  ```

- [ ] 实现历史记录可视化

- [ ] 添加分页:
  ```js
  const page = ref(1)
  const pageSize = 50

  async function loadCards() {
    const response = await axios.get('/api/cards/', {
      params: {
        page: page.value,
        page_size: pageSize,
        ...filters
      }
    })
    cards.value = response.data.results
    totalPages.value = Math.ceil(response.data.count / pageSize)
  }
  ```

**验收标准**:
- 500 条目列表 P95 <500ms
- 批量操作无卡顿
- 重复检测准确率 ≥95%
- 分页正常

**依赖**: M2 完成
**技术决策**: 网页版无需虚拟滚动（桌面性能足够）

---

### 3.3 性能优化 (12h) ⭐ P1 优化

- [ ] 代码分割 (按路由懒加载):
  ```js
  const routes = [
    {
      path: '/review',
      component: () => import('@/views/Review.vue')
    },
    {
      path: '/cards',
      component: () => import('@/views/Cards.vue')
    }
  ]
  ```

- [ ] 配置生产构建优化:
  ```js
  // vite.config.js
  export default {
    build: {
      rollupOptions: {
        output: {
          manualChunks: {
            'vendor': ['vue', 'vue-router', 'pinia'],
            'charts': ['chart.js', 'vue-chartjs']
          }
        }
      },
      chunkSizeWarningLimit: 1000
    }
  }
  ```

- [ ] 启用 Gzip/Brotli 压缩 (Nginx):
  ```nginx
  # nginx.conf
  gzip on;
  gzip_comp_level 6;
  gzip_types text/plain text/css application/json application/javascript text/xml application/xml;

  brotli on;
  brotli_types text/plain text/css application/json application/javascript;
  ```

- [ ] 优化 Django 缓存:
  ```python
  # settings.py
  CACHES = {
      'default': {
          'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
          'LOCATION': 'unique-snowflake',
      }
  }

  # views.py
  from django.views.decorators.cache import cache_page

  @cache_page(60 * 15)  # 15 分钟
  def lookup_english(request, word):
      ...
  ```

- [ ] 添加数据库查询优化:
  ```python
  # 使用 select_related 减少查询
  cards = Card.objects.select_related('deck', 'user').filter(...)

  # 添加缺失索引
  class Card(models.Model):
      class Meta:
          indexes = [
              models.Index(fields=['word']),
              models.Index(fields=['user', 'state', 'due_at']),
          ]
  ```

- [ ] 图片压缩和 WebP 转换:
  ```bash
  # 批量转换图片
  for img in assets/*.png; do
    cwebp "$img" -o "${img%.png}.webp"
  done
  ```

- [ ] 使用 Lighthouse 测试并优化:
  ```bash
  npm install -g @lhci/cli
  lhci autorun --collect.url=http://localhost:5173
  ```

**验收标准**:
- 首屏加载 P95 <1200ms (网页版放宽标准)
- Lighthouse 性能分数 ≥85
- API 响应 P99 <500ms
- JS Bundle 总大小 <500KB (gzip)

**依赖**: M2 完成
**技术决策**: 使用 Vite 自动代码分割

**应对方案**:
- M2 结束时提前进行 Lighthouse 测试
- 预留额外 3 小时调优时间
- 性能不达标时标记为技术债务

---

### 3.4 导入导出功能 (8h)

- [ ] 实现 CSV 导入:
  ```js
  async function importCSV(file) {
    const text = await file.text()
    const lines = text.split('\n')
    const headers = lines[0].split(',')

    const cards = lines.slice(1).map(line => {
      const values = line.split(',')
      return {
        word: values[0],
        meaning: values[1],
        tags: values[2]?.split('|') || []
      }
    })

    // 批量创建
    await axios.post('/api/cards/batch-create/', { cards })
  }
  ```

- [ ] 实现 Anki 格式兼容:
  ```js
  function parseAnkiCSV(text) {
    // Anki 格式: Front, Back, Tags
    const lines = text.split('\n')
    return lines.map(line => {
      const [front, back, tags] = line.split('\t')
      return {
        word: front,
        metadata: { meaning: back },
        tags: tags?.split(' ') || []
      }
    })
  }
  ```

- [ ] 实现语义指纹冲突检测:
  ```js
  async function detectConflicts(newCards) {
    const existing = await axios.get('/api/cards/')
    const existingHashes = new Set(existing.data.map(semanticHash))

    return newCards.filter(card => {
      const hash = semanticHash(card)
      if (existingHashes.has(hash)) {
        console.warn(`重复: ${card.word}`)
        return false
      }
      return true
    })
  }
  ```

- [ ] 实现导出功能:
  ```js
  async function exportCards(format = 'csv') {
    const cards = await axios.get('/api/cards/')

    if (format === 'csv') {
      const csv = [
        'word,meaning,tags',
        ...cards.data.map(c => `${c.word},${c.metadata.meaning},${c.tags.join('|')}`)
      ].join('\n')

      downloadFile(csv, 'cards.csv', 'text/csv')
    } else if (format === 'json') {
      downloadFile(JSON.stringify(cards.data, null, 2), 'cards.json', 'application/json')
    }
  }

  function downloadFile(content, filename, mimeType) {
    const blob = new Blob([content], { type: mimeType })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
  }
  ```

- [ ] 添加导入进度条:
  ```vue
  <template>
    <div v-if="importing" class="progress">
      <progress :value="importProgress" max="100"></progress>
      <p>{{ importProgress }}% ({{ importedCount }}/{{ totalCount }})</p>
    </div>
  </template>
  ```

**验收标准**:
- 导入 1000 行 ≤5s
- 冲突检测准确率 ≥95%
- 导出数据可复算
- 支持 CSV/JSON/Anki 格式

**依赖**: M2 完成, 3.2
**风险**: Anki 格式映射复杂

---

### 3.5 邮件提醒机制 (8h)

- [ ] 配置邮件后端:
  ```python
  # settings.py
  EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
  EMAIL_HOST = 'smtp.gmail.com'
  EMAIL_PORT = 587
  EMAIL_USE_TLS = True
  EMAIL_HOST_USER = os.getenv('EMAIL_USER')
  EMAIL_HOST_PASSWORD = os.getenv('EMAIL_PASSWORD')
  ```

- [ ] 实现提醒 Management Command:
  ```python
  # management/commands/send_review_reminders.py
  from django.core.mail import send_mail
  from django.utils import timezone

  class Command(BaseCommand):
      def handle(self, *args, **options):
          now = timezone.now()
          if not (20 <= now.hour < 22):  # 仅 20:00-22:00
              return

          # 查找有待复习卡片的用户
          users_with_due = Card.objects.filter(
              due_at__lte=now
          ).values_list('user__email', flat=True).distinct()

          for email in users_with_due:
              due_count = Card.objects.filter(
                  user__email=email,
                  due_at__lte=now
              ).count()

              send_mail(
                  subject='今日复习提醒',
                  message=f'您有 {due_count} 张卡片待复习',
                  from_email='noreply@rpd.example.com',
                  recipient_list=[email]
              )
  ```

- [ ] 添加用户偏好设置:
  ```python
  class UserProfile(models.Model):
      user = models.OneToOneField(User, on_delete=models.CASCADE)
      email_reminders = models.BooleanField(default=True)
      reminder_time = models.TimeField(default='20:00')
  ```

- [ ] 配置 cron:
  ```bash
  # 每天 20:00 检查
  0 20 * * * cd /app && python manage.py send_review_reminders
  ```

**验收标准**:
- 邮件正常发送
- 用户可完全禁用
- 时间窗口可配置

**依赖**: M1 完成
**风险**: SMTP 配置可能失败

**应对方案**:
- 使用 SendGrid/阿里云邮件 API
- 提供环境变量配置

---

### M3 总结

**总工时**: 48 小时 (相比 PWA 版减少 12h)
**关键路径**: 3.3 (性能优化)
**里程碑交付**: 功能完整的 v2.0 网页版
**技术债务**: FSRS 算法、Azure TTS 留待 M4

**简化项**:
- ❌ 移除 PWA 推送通知 (3h)
- ✅ 添加邮件提醒 (8h)
- 🔽 内容管理减少虚拟滚动 (-2h)
- 🔽 性能优化减少 SW 调优 (-3h)

---

## 测试策略

### 单元测试 (覆盖率目标 ≥80%)

**后端 (pytest + pytest-django):**
```bash
pip install pytest pytest-django pytest-cov
pytest --cov=. --cov-report=html
```

- 模型层: 测试 SM-2 算法逻辑、队列生成
- API 层: 测试所有端点的 CRUD 操作
- 服务层: 测试字典查询、备份逻辑

**前端 (Vitest + Vue Test Utils):**
```bash
npm install -D vitest @vue/test-utils
npm run test:coverage
```

- 组件测试: 闪卡、表单、统计图表
- 工具函数: 三层降级逻辑、语义指纹算法
- 状态管理: Pinia store 测试

### 集成测试

**E2E 测试 (Playwright):**
```bash
npm install -D @playwright/test
npx playwright test
```

- 关键用户流程: 注册 → 录入 → 复习 → 统计
- 字典降级场景: 后端失败 → 在线 API → 手动
- 键盘快捷键: 全流程键盘操作

### 性能测试

- **Lighthouse CI**: 每次构建运行，性能分数 <85 则失败
  ```bash
  lhci autorun
  ```

- **API 压测 (Locust)**: 模拟 10 并发用户，验证 P99 <500ms
  ```python
  from locust import HttpUser, task

  class ReviewUser(HttpUser):
      @task
      def get_queue(self):
          self.client.get("/api/review/queue/")
  ```

- **数据库查询分析**: 使用 Django Debug Toolbar 检测 N+1 查询

### 测试覆盖率门槛

- 后端: ≥80% (pytest-cov)
- 前端: ≥80% (Vitest coverage)
- E2E: 覆盖 10 个核心场景

---

## 部署流程

### 开发环境

```bash
# 后端
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
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
    command: gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 2
    volumes:
      - db_data:/app/db
      - ./data:/app/data  # 挂载汉字数据库
    environment:
      - DATABASE_URL=sqlite:////app/db/db.sqlite3
      - ALLOWED_HOSTS=localhost,rpd.example.com
      - SECRET_KEY=${SECRET_KEY}
      - S3_BACKUP_BUCKET=${S3_BACKUP_BUCKET}
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./frontend/dist:/usr/share/nginx/html:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - backend
    restart: unless-stopped

volumes:
  db_data:
```

**nginx.conf**:
```nginx
server {
    listen 80;
    server_name rpd.example.com;

    # Vue SPA 静态文件
    location / {
        root /usr/share/nginx/html;
        try_files $uri $uri/ /index.html;
    }

    # Django API
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # Django Admin
    location /admin/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
    }

    # 静态文件缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Gzip 压缩
    gzip on;
    gzip_comp_level 6;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;
}
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

# 6. 导入字典数据
docker-compose exec backend python manage.py import_ecdict

# 7. 配置 cron (备份 + 邮件提醒)
docker-compose exec backend crontab -e
# 添加:
# 0 2 * * * cd /app && python manage.py backup_db
# 0 20 * * * cd /app && python manage.py send_review_reminders
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
          pytest --cov --cov-fail-under=80

      - name: Frontend Tests
        run: |
          cd frontend
          npm install
          npm run test:coverage

      - name: Lighthouse CI
        run: |
          npm install -g @lhci/cli
          lhci autorun

  deploy:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Server
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SSH_KEY }}
          script: |
            cd /app/rpd
            git pull
            docker-compose up -d --build
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
- 性能不达标时使用 Django cache 或 Redis

**应急方案**:
- 降级为仅在线 API (L2)，牺牲离线能力
- 提供预处理好的 SQLite 文件下载

---

#### 风险 2: S3 备份配置复杂，上线延期

**概率**: 低 (20%)
**影响**: 中 (可暂时降级)

**缓解措施**:
- 优先使用 Backblaze B2 (S3 兼容 + 免费额度 10GB)
- 提前准备 MinIO 自托管方案

**应急方案**:
- 临时改为本地备份 + 手动上传

---

### 中风险项 (P1)

#### 风险 3: 性能优化未达 P95 <1200ms

**概率**: 中 (30%)
**影响**: 中 (不阻塞上线)

**缓解措施**:
- M2 结束时提前进行 Lighthouse 测试
- 预留 M3 额外 3 小时调优时间

**应急方案**:
- 放宽指标至 <1500ms，标记为技术债务

---

#### 风险 4: 多音字推断准确率不达标

**概率**: 低 (20%)，后端 jieba 性能优于前端 jieba-js
**影响**: 低 (可降级)

**缓解措施**:
- 使用更大的词-读音映射表
- 失败时自动降级为候选面板

**应急方案**:
- 完全依赖候选面板手动选择

---

## 网页版 vs PWA 版对比总结

| 维度 | PWA 版 | 网页版 | 改善 |
|------|--------|--------|------|
| **总工时** | 218h (5.5周) | **164h (4.1周)** | **-25%** |
| **前端工时** | 90h | **48h** | **-47%** |
| **离线支持** | ✅ 完全离线 | ❌ 需要网络 | - |
| **PWA 安装** | ✅ 可安装 | ❌ 不可安装 | - |
| **技术栈数量** | 12 项 | **8 项** | **-33%** |
| **浏览器兼容** | 复杂 (iOS 限制) | **简单** | ✅ |
| **调试复杂度** | 高 (SW 黑盒) | **低** | ✅ |
| **首屏性能** | P95 <900ms | **P95 <1200ms** | 放宽 33% |
| **字典查询** | P95 <300ms | **P95 <600ms** | 放宽 100% |
| **测试覆盖率** | ≥85% | **≥80%** | 放宽 5% |
| **风险项数量** | 5 个 | **2 个** | **-60%** |

**核心优势**:
- ✅ 开发效率提升 25%
- ✅ 架构简洁度提升 40%
- ✅ 维护成本降低
- ✅ 浏览器兼容性更好

**权衡取舍**:
- ❌ 无离线支持
- ❌ 不可安装到桌面
- ⚠️ 性能标准适度放宽

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

### 4.3 多标签页同步 (4h)

- [ ] 使用 Broadcast Channel API 同步状态:
  ```js
  const bc = new BroadcastChannel('rpd-sync')

  bc.postMessage({ type: 'review-completed', cardId: 123 })

  bc.onmessage = (event) => {
    if (event.data.type === 'review-completed') {
      store.removeFromQueue(event.data.cardId)
    }
  }
  ```

---

## 项目总结

### 总工时

**164 小时 (4.1 周 @ 40h/周)**

**相比 PWA 版节省**: 54 小时 (-25%)

### 关键路径 (影响交付时间)

```
M1.2 (数据模型) → M1.4 (SM-2 算法) → M1.5 (ECDICT)
    ↓
M2.2 (复习会话) → M2.3 (条目录入) → M2.4 (字典集成)
    ↓
M3.3 (性能优化)
```

### 优先级

- **P0 (必须)**: M1.4, M1.5, M1.6, M1.7, M2.2, M2.3
- **P1 (强烈建议)**: M2.4, M3.2, M3.3
- **P2 (可选)**: M3.1, M3.5

### 成功标准

- [ ] 核心功能验收清单全部通过
- [ ] 性能指标达标 (首屏 <1200ms, API <500ms)
- [ ] 字典查询可用性 ≥98%
- [ ] 测试覆盖率 ≥80%
- [ ] 浏览器兼容 (Chrome/Firefox/Safari 最新 2 版本)

### 下一步行动

1. **立即开始**: M1.1 环境搭建 (6h)
2. **第 3 天**: M1.5 ECDICT POC 验证
3. **每周五**: 里程碑回顾会议

---

**文档版本**: v2.0 (Web)
**生成时间**: 2025-01-19
**基于**: RPD v2.0 文档 (网页版优化)
**变更**: 移除 PWA 相关功能，简化为网页架构，总工时从 218h 减少至 164h
