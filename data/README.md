# 汉字本地数据库说明

## 数据来源

- **源文件**: `ChineseCharacterMap.csv`
- **数据提供**: 汉字理解型学习研究团队 (www.learnm.org)
- **授权**: 知识共享署名-相同方式共享 4.0 国际许可协议
- **字符数**: 4217 个汉字（包含完整的常用字和次常用字）

## 数据库文件

### 1. `hanzi_local.db` (644 KB)
**完整版数据库 - 后端使用**

- **字符数**: 4217 个汉字
- **字段**:
  - `character`: 汉字
  - `decomposition`: 构件拆分
  - `rationality_score`: 理据打分
  - `pinyin`: 拼音（含多音字）
  - `traditional`: 繁体字
  - `network_level`: 网络层次（1-5 层）
  - `frequency_1` / `frequency_2`: 字频
  - `frequency_order_1` / `frequency_order_2`: 字频排序
  - `learning_order_1` / `learning_order_2`: 学习顺序

- **用途**: Django 后端服务端共享缓存（L2 层）

### 2. `hanzi_compact.db` (288 KB)
**精简版数据库 - 前端使用**

- **字符数**: 3500 个常用字
- **字段**（精简）:
  - `character`: 汉字
  - `pinyin`: 拼音
  - `decomposition`: 构件
  - `traditional`: 繁体
  - `frequency`: 字频
  - `learning_order`: 学习顺序

- **用途**: 前端 WebAssembly (sql.js) 本地字典（L1 层）

### 3. `hanzi_compact.db.gz` (136 KB)
**压缩版精简数据库 - 前端下载**

- **压缩率**: 52.9%
- **下载大小**: 仅 136 KB
- **用途**: 前端首次加载，解压后存入 IndexedDB

## 使用方法

### 后端使用（Django）

```python
import sqlite3

# 连接数据库
conn = sqlite3.connect('data/hanzi_local.db')
cursor = conn.cursor()

# 查询汉字
cursor.execute("SELECT * FROM hanzi WHERE character = ?", ('学',))
result = cursor.fetchone()

# 拼音搜索
cursor.execute("""
    SELECT character, pinyin, frequency_1
    FROM hanzi
    WHERE pinyin LIKE ?
    ORDER BY frequency_order_1 ASC
    LIMIT 20
""", ('%xue%',))

conn.close()
```

### 前端使用（Vue + sql.js）

```javascript
import initSqlJs from 'sql.js';
import { openDB } from 'idb';
import pako from 'pako';

// 1. 下载并解压
async function loadHanziDB() {
  const idb = await openDB('RPDDatabase', 2);
  let dbData = await idb.get('system', 'hanzi_dict');

  if (!dbData) {
    // 首次下载
    const response = await fetch('/static/dicts/hanzi_compact.db.gz');
    const compressed = await response.arrayBuffer();

    // 解压
    dbData = pako.inflate(new Uint8Array(compressed));

    // 缓存到 IndexedDB
    await idb.put('system', { key: 'hanzi_dict', data: dbData });
  }

  // 2. 加载到 sql.js
  const SQL = await initSqlJs({
    locateFile: file => `/wasm/${file}`
  });

  const db = new SQL.Database(new Uint8Array(dbData));

  return db;
}

// 3. 查询
async function lookupHanzi(char) {
  const db = await loadHanziDB();

  const result = db.exec(
    `SELECT * FROM hanzi WHERE character = ?`,
    [char]
  );

  if (result.length > 0) {
    const row = result[0].values[0];
    return {
      character: row[0],
      pinyin: row[1],
      decomposition: row[2],
      traditional: row[3],
      frequency: row[4]
    };
  }

  return null;
}
```

## 数据统计

### 完整版 (hanzi_local.db)

- **总汉字数**: 4217
- **有拼音**: 4215 (100.0%)
- **有构件**: 4217 (100.0%)
- **网络层级分布**:
  - 第 1 层: 367 个字（最基础）
  - 第 2 层: 1397 个字
  - 第 3 层: 1669 个字
  - 第 4 层: 674 个字
  - 第 5 层: 107 个字

### 精简版 (hanzi_compact.db)

- **总汉字数**: 3500（教育部通用规范汉字表一级字）
- **覆盖率**: 约 95% 的日常汉语文本
- **学习顺序**: 按照科学的学习顺序排列（基于网络层次和字频）

### 前 20 个高频字

| 排序 | 汉字 | 拼音 | 字频 |
|------|-----|------|------|
| 1 | 的 | dí dì de | 4.8867 |
| 2 | 一 | yī | 1.4062 |
| 3 | 是 | shì | 1.3155 |
| 4 | 不 | bù fǒu fōu | 1.0707 |
| 5 | 了 | liǎo le | 0.9517 |
| 6 | 在 | zài | 0.9258 |
| 7 | 有 | yǒu yòu | 0.9082 |
| 8 | 人 | rén | 0.7822 |
| 9 | 这 | zhè yàn zhèi | 0.7619 |
| 10 | 上 | shàng shǎng | 0.6031 |
| 11 | 大 | dà dài tài | 0.5842 |
| 12 | 来 | lái lài | 0.5776 |
| 13 | 和 | hé hè huó huò hú | 0.5765 |
| 14 | 我 | wǒ | 0.5760 |
| 15 | 个 | gè gě | 0.5724 |
| 16 | 中 | zhōng zhòng | 0.5460 |
| 17 | 地 | dì de | 0.5375 |
| 18 | 为 | wéi wèi | 0.5351 |
| 19 | 他 | tā | 0.4916 |
| 20 | 生 | shēng | 0.4905 |

## 维护脚本

### 1. 导入数据
```bash
python3 scripts/import_hanzi_to_db.py
```
从 `ChineseCharacterMap.csv` 导入数据到 `hanzi_local.db`

### 2. 查询示例
```bash
python3 scripts/query_hanzi_db.py
```
演示各种查询操作

### 3. 生成精简版
```bash
python3 scripts/create_compact_hanzi_db.py
```
生成前端用的精简版数据库和压缩包

## 数据引用

如果使用本数据，请引用：

> Xiaoyong Yan, Ying Fan, Zengru Di, Shlomo Havlin, Jinshan Wu. Efficient learning strategy of Chinese characters based on network approach. *PloS ONE*, 8, e69745 (2013). DOI: 10.1371/journal.pone.0069745

或引用汉字理解型学习网站: www.learnm.org

## 联系方式

- jinshanw@bnu.edu.cn
- yanxy@bjtu.edu.cn
- syk0126@126.com

---

**最后更新**: 2025-01-18
**数据版本**: 2020.1.2
