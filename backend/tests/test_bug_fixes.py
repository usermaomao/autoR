#!/usr/bin/env python
"""
Bug 修复验证脚本
测试：
1. Bug 1: 新卡片的 due_at 是否设置为未来日期
2. Bug 2: 多音字拼音是否正确保存为数组
"""
import os
import sys
import django
from datetime import datetime

# 设置Django环境
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.utils import timezone
from cards.models import Card, Deck
from django.contrib.auth.models import User


def test_bug1_new_card_due_date():
    """测试 Bug 1: 新卡片的 due_at 应该是未来日期，不会立即显示为逾期"""
    print("=" * 60)
    print("测试 Bug 1: 新卡片 due_at 默认值")
    print("=" * 60)

    # 获取或创建测试用户和卡组
    user, _ = User.objects.get_or_create(username='test_user')
    deck, _ = Deck.objects.get_or_create(
        user=user,
        name='测试卡组',
        defaults={'daily_new_limit': 20, 'daily_review_limit': 200}
    )

    # 创建新卡片
    card = Card.objects.create(
        user=user,
        deck=deck,
        word='test_word',
        card_type='en',
        metadata={'meaning_zh': '测试释义', 'examples': ['测试例句']},
    )

    print(f"\n新创建的卡片信息:")
    print(f"  单词: {card.word}")
    print(f"  状态: {card.state}")
    print(f"  due_at: {card.due_at}")
    print(f"  当前时间: {timezone.now()}")

    # 验证 due_at 是否在未来
    now = timezone.now()
    is_future = card.due_at > now

    print(f"\n验证结果:")
    if is_future:
        days_in_future = (card.due_at - now).days
        print(f"  ✓ PASS: due_at 在未来（{days_in_future} 天后）")
        print(f"  ✓ 新卡片不会立即显示为逾期")
    else:
        print(f"  ✗ FAIL: due_at 不在未来")
        print(f"  ✗ 新卡片会立即显示为逾期（Bug 未修复）")

    # 清理测试数据
    card.delete()
    print(f"\n测试数据已清理")

    return is_future


def test_bug2_pinyin_array():
    """测试 Bug 2: 多音字拼音应该保存为数组"""
    print("\n" + "=" * 60)
    print("测试 Bug 2: 多音字拼音数组保存")
    print("=" * 60)

    # 获取或创建测试用户和卡组
    user, _ = User.objects.get_or_create(username='test_user')
    deck, _ = Deck.objects.get_or_create(
        user=user,
        name='测试卡组',
        defaults={'daily_new_limit': 20, 'daily_review_limit': 200}
    )

    # 创建包含多音字的卡片（模拟前端保存）
    test_cases = [
        {
            'word': '长',
            'pinyin': ['cháng', 'zhǎng'],  # 应该保存为数组
            'meaning': '1. 长度 2. 生长'
        },
        {
            'word': '行',
            'pinyin': ['háng', 'xíng'],
            'meaning': '1. 行业 2. 行走'
        }
    ]

    print("\n创建测试卡片并验证拼音存储格式:")
    all_passed = True

    for test_case in test_cases:
        card = Card.objects.create(
            user=user,
            deck=deck,
            word=test_case['word'],
            card_type='zh',
            metadata={
                'pinyin': test_case['pinyin'],
                'meaning_zh': test_case['meaning']
            }
        )

        # 重新从数据库读取
        card.refresh_from_db()
        saved_pinyin = card.metadata.get('pinyin')

        print(f"\n  字: {card.word}")
        print(f"    预期拼音: {test_case['pinyin']}")
        print(f"    实际保存: {saved_pinyin}")
        print(f"    类型: {type(saved_pinyin)}")

        # 验证是否是数组
        is_array = isinstance(saved_pinyin, list)
        has_multiple = len(saved_pinyin) > 1 if is_array else False

        if is_array and has_multiple:
            print(f"    ✓ PASS: 拼音保存为数组，支持多音字")
            # 模拟前端显示
            display = ', '.join(saved_pinyin) if isinstance(saved_pinyin, list) else str(saved_pinyin)
            print(f"    ✓ 前端显示效果: {display}")
        else:
            print(f"    ✗ FAIL: 拼音未正确保存为数组")
            all_passed = False

        # 清理测试数据
        card.delete()

    return all_passed


if __name__ == '__main__':
    print("\n🔍 开始验证 Bug 修复...\n")

    try:
        # 测试 Bug 1
        bug1_fixed = test_bug1_new_card_due_date()

        # 测试 Bug 2
        bug2_fixed = test_bug2_pinyin_array()

        # 总结
        print("\n" + "=" * 60)
        print("修复验证总结")
        print("=" * 60)
        print(f"  Bug 1 (新卡片逾期): {'✓ 已修复' if bug1_fixed else '✗ 未修复'}")
        print(f"  Bug 2 (多音字显示): {'✓ 已修复' if bug2_fixed else '✗ 未修复'}")

        if bug1_fixed and bug2_fixed:
            print("\n🎉 所有 Bug 均已修复！")
        else:
            print("\n⚠️  仍有 Bug 未完全修复，请检查代码")

        # 清理测试用户和卡组
        try:
            user = User.objects.get(username='test_user')
            user.decks.all().delete()
            user.delete()
            print("\n测试用户和卡组已清理")
        except User.DoesNotExist:
            pass

    except Exception as e:
        print(f"\n✗ 测试过程中出错: {e}")
        import traceback
        traceback.print_exc()
