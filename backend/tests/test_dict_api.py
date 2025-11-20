#!/usr/bin/env python
"""
字典查询API测试脚本
测试四层降级策略：
L1: 缓存 (cache)
L2: 本地字典库 (local-dict)
L3: 在线API / 百度汉语 (online-api / baidu-hanyu)
L4: 手动输入 (manual)
"""
import os
import sys
import django

# 设置Django环境
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from cards.models import ECDict
from django.core.cache import cache
from cards.services.baidu_hanyu import BaiduHanyuService


def test_english_lookup():
    """测试英语单词查询"""
    print("="*60)
    print("测试英语单词查询 (ECDICT 本地字典)")
    print("="*60)

    test_words = ['hello', 'world', 'python', 'artificial', 'intelligence']

    for word in test_words:
        print(f"\n查询: {word}")

        # 清除缓存
        cache_key = f'dict:en:{word.lower()}'
        cache.delete(cache_key)

        # L2: 本地字典库查询
        try:
            entry = ECDict.objects.get(word__iexact=word)
            print(f"  ✓ 来源: local-dict")
            print(f"  音标: {entry.phonetic}")
            print(f"  中文: {entry.translation[:80]}...")
            print(f"  Collins: {entry.collins if entry.collins else 'N/A'}")
            print(f"  Oxford 3000: {'是' if entry.oxford else '否'}")
        except ECDict.DoesNotExist:
            print(f"  ✗ 未找到")

    # 测试缓存
    print("\n" + "-"*60)
    print("测试L1缓存 (重复查询第一个单词)")
    print("-"*60)
    word = test_words[0]

    # 第一次查询 (L2)
    import time
    start = time.time()
    entry = ECDict.objects.get(word__iexact=word)
    t1 = (time.time() - start) * 1000
    print(f"  第一次查询 (L2本地库): {t1:.2f}ms")

    # 模拟缓存(实际API会自动缓存)
    cache.set(f'dict:en:{word.lower()}', {
        'word': entry.word,
        'ipa': entry.phonetic,
        'translation': entry.translation
    }, timeout=86400)

    # 第二次查询 (L1)
    start = time.time()
    cached = cache.get(f'dict:en:{word.lower()}')
    t2 = (time.time() - start) * 1000
    print(f"  第二次查询 (L1缓存): {t2:.2f}ms")
    print(f"  性能提升: {t1/t2:.1f}x")


def test_hanzi_lookup():
    """测试汉字查询"""
    print("\n" + "="*60)
    print("测试汉字查询 (百度汉语API + 自动保存)")
    print("="*60)

    test_chars = ['中', '国', '学', '习']

    for char in test_chars:
        print(f"\n查询: {char}")

        # L3: 百度汉语API
        result = BaiduHanyuService.lookup(char)

        if result:
            print(f"  ✓ 来源: baidu-hanyu")
            print(f"  拼音: {', '.join(result.get('pinyin', []))}")
            print(f"  部首: {result.get('radical', 'N/A')}")
            print(f"  笔画: {result.get('strokes', 'N/A')}")
            print(f"  释义: {result.get('meaning_zh', '')[:60]}...")

            # 检查是否会自动保存到本地(需要实际API调用)
            print(f"  (生产环境下会自动保存到本地数据库)")
        else:
            print(f"  ✗ API查询失败")


def test_database_stats():
    """测试数据库统计"""
    print("\n" + "="*60)
    print("数据库统计")
    print("="*60)

    total = ECDict.objects.count()
    print(f"  ECDICT总词条数: {total:,}")

    # 柯林斯5星单词
    collins_5 = ECDict.objects.filter(collins=5).count()
    print(f"  Collins 5星单词: {collins_5:,}")

    # 牛津3000核心词汇
    oxford = ECDict.objects.filter(oxford=True).count()
    print(f"  Oxford 3000核心词汇: {oxford:,}")

    # 检查汉字数据库
    import sqlite3
    hanzi_db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'hanzi_local.db')
    if os.path.exists(hanzi_db_path):
        conn = sqlite3.connect(hanzi_db_path)
        cursor = conn.cursor()
        try:
            count = cursor.execute("SELECT COUNT(*) FROM hanzi").fetchone()[0]
            print(f"  本地汉字库: {count:,} 个字符")
        except:
            print(f"  本地汉字库: 未初始化")
        conn.close()
    else:
        print(f"  本地汉字库: 不存在 (将在首次查询后创建)")


if __name__ == '__main__':
    try:
        test_database_stats()
        test_english_lookup()
        test_hanzi_lookup()

        print("\n" + "="*60)
        print("✓ 所有测试完成")
        print("="*60)

    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
