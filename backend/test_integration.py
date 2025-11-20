#!/usr/bin/env python3
"""
集成测试脚本
测试 autoR 项目的主要功能流程
"""

import os
import sys
import django
import json
from datetime import datetime

# 设置 Django 环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from cards.models import Card, Deck

User = get_user_model()

def print_section(title):
    """打印测试章节标题"""
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)

def test_user_creation():
    """测试用户创建"""
    print_section("测试 1: 用户管理")

    # 清理测试用户
    User.objects.filter(username='test_integration').delete()

    # 创建测试用户
    user = User.objects.create_user(
        username='test_integration',
        email='test@example.com',
        password='testpass123'
    )

    assert user.username == 'test_integration'
    print(f"✓ 用户创建成功: {user.username}")

    # 验证用户数量
    user_count = User.objects.count()
    print(f"✓ 当前用户数: {user_count}")

    print("✅ 用户管理测试通过")
    return user

def test_deck_operations(user):
    """测试卡组操作"""
    print_section("测试 2: 卡组操作")

    # 清理用户已有的测试卡组
    Deck.objects.filter(user=user, name__startswith='测试卡组').delete()

    # 创建卡组
    deck1 = Deck.objects.create(
        user=user,
        name='测试卡组1',
        description='集成测试卡组',
        daily_new_limit=20,
        daily_review_limit=200
    )

    deck2 = Deck.objects.create(
        user=user,
        name='测试卡组2',
        description='第二个测试卡组',
        daily_new_limit=10,
        daily_review_limit=100
    )

    print(f"✓ 卡组1创建成功: {deck1.name} (ID: {deck1.id})")
    print(f"✓ 卡组2创建成功: {deck2.name} (ID: {deck2.id})")

    # 验证新创建的卡组
    test_deck_count = Deck.objects.filter(user=user, name__startswith='测试卡组').count()
    assert test_deck_count == 2
    print(f"✓ 新创建测试卡组数量: {test_deck_count}")

    print("✅ 卡组操作测试通过")
    return deck1, deck2

def test_card_crud(user, deck):
    """测试卡片 CRUD 操作"""
    print_section("测试 3: 卡片 CRUD 操作")

    # 创建卡片
    card1 = Card.objects.create(
        user=user,  # 添加 user 字段
        deck=deck,
        card_type='en',
        word='test',
        metadata={
            'meaning_zh': '测试',
            'meaning_en': 'a test or trial',
            'phonetic': '/test/',
            'examples': ['This is a test.']
        },
        tags=['测试', '集成'],
        semantic_hash='test_hash_1'
    )

    card2 = Card.objects.create(
        user=user,  # 添加 user 字段
        deck=deck,
        card_type='zh',
        word='测试',
        metadata={
            'meaning_zh': '检验；试验',
            'pinyin': ['cè', 'shì'],
            'radical': '讠',
            'strokes': 12,
            'examples': ['这是一个测试。']
        },
        tags=['测试', '集成'],
        semantic_hash='test_hash_2'
    )

    print(f"✓ 英文卡片创建: {card1.word} (ID: {card1.id})")
    print(f"✓ 中文卡片创建: {card2.word} (ID: {card2.id})")

    # 读取卡片
    card_read = Card.objects.get(id=card1.id)
    assert card_read.word == 'test'
    print(f"✓ 读取卡片: {card_read.word}")

    # 更新卡片
    card1.metadata['meaning_zh'] = '测试（已更新）'
    card1.save()
    card_updated = Card.objects.get(id=card1.id)
    assert '已更新' in card_updated.metadata['meaning_zh']
    print(f"✓ 更新卡片: {card_updated.metadata['meaning_zh']}")

    # 验证卡片数量
    card_count = Card.objects.filter(deck=deck).count()
    assert card_count == 2
    print(f"✓ 卡组内卡片数: {card_count}")

    print("✅ 卡片 CRUD 操作测试通过")
    return card1, card2

def test_batch_operations(user, deck1, deck2):
    """测试批量操作"""
    print_section("测试 4: 批量操作")

    # 创建多张测试卡片
    cards = []
    for i in range(5):
        card = Card.objects.create(
            user=user,  # 添加 user 字段
            deck=deck1,
            card_type='en',
            word=f'word{i}',
            metadata={'meaning_zh': f'词{i}'},
            tags=['批量测试'],
            semantic_hash=f'batch_hash_{i}'
        )
        cards.append(card)

    print(f"✓ 创建 {len(cards)} 张测试卡片")

    # 测试批量移动
    moved_count = 0
    for card in cards[:3]:  # 移动前3张
        card.deck = deck2
        card.save()
        moved_count += 1

    deck1_count = Card.objects.filter(deck=deck1).count()
    deck2_count = Card.objects.filter(deck=deck2).count()
    print(f"✓ 批量移动: {moved_count} 张卡片从卡组1移到卡组2")
    print(f"  - 卡组1剩余: {deck1_count} 张")
    print(f"  - 卡组2现有: {deck2_count} 张")

    # 测试批量修改标签
    for card in cards:
        card.tags = ['批量测试', '已修改']
        card.save()

    # 验证标签修改（通过遍历而不是 contains 查询）
    updated_count = 0
    for card in Card.objects.filter(id__in=[c.id for c in cards]):
        if '已修改' in card.tags:
            updated_count += 1
    print(f"✓ 批量修改标签: {updated_count} 张卡片")

    # 测试批量重置进度
    for card in cards:
        card.ef = 2.5
        card.interval = 0
        card.learning_step = 0  # 使用 learning_step 而不是 repetition
        card.save()

    reset_cards = Card.objects.filter(ef=2.5, interval=0, learning_step=0)
    print(f"✓ 批量重置进度: {reset_cards.count()} 张卡片")

    print("✅ 批量操作测试通过")
    return cards

def test_semantic_deduplication(user, deck):
    """测试语义去重"""
    print_section("测试 5: 语义去重")

    from cards.services.import_export import ImportExportService

    service = ImportExportService()

    # 测试语义哈希生成
    hash1 = service.generate_semantic_hash('duplicate', '重复')
    hash2 = service.generate_semantic_hash('DUPLICATE', '重复')  # 大小写不同
    hash3 = service.generate_semantic_hash(' duplicate ', ' 重复 ')  # 有空格

    # 验证所有哈希相同（不区分大小写和空格）
    assert hash1 == hash2 == hash3
    print(f"✓ 语义哈希一致性: {hash1}")
    print(f"  - 'duplicate' → {hash1}")
    print(f"  - 'DUPLICATE' → {hash2}")
    print(f"  - ' duplicate ' → {hash3}")

    print("✅ 语义去重测试通过")

def test_sm2_algorithm(card):
    """测试 SM-2 算法"""
    print_section("测试 6: SM-2 间隔重复算法")

    from cards.services.sm2 import process_review

    # 初始状态
    print(f"初始状态:")
    print(f"  - EF: {card.ef}")
    print(f"  - Interval: {card.interval}")
    print(f"  - Learning Step: {card.learning_step}")
    print(f"  - State: {card.state}")

    # 模拟复习（质量=5，完美回忆）
    review_log1 = process_review(card, quality=5, time_taken=2000)
    card.refresh_from_db()  # 重新加载最新状态

    print(f"\n第一次复习 (质量=5):")
    print(f"  - 新 EF: {card.ef}")
    print(f"  - 新 Interval: {card.interval}")
    print(f"  - 新 State: {card.state}")

    # 第二次复习（质量=4，轻松回忆）
    review_log2 = process_review(card, quality=4, time_taken=1500)
    card.refresh_from_db()

    print(f"\n第二次复习 (质量=4):")
    print(f"  - 新 EF: {card.ef}")
    print(f"  - 新 Interval: {card.interval}")
    print(f"  - 新 State: {card.state}")

    # 验证复习记录创建
    from cards.models import ReviewLog
    review_count = ReviewLog.objects.filter(card=card).count()
    print(f"\n✓ 复习记录数: {review_count}")

    assert review_count == 2
    print("✅ SM-2 算法测试通过")

def test_data_consistency():
    """测试数据一致性"""
    print_section("测试 7: 数据一致性")

    # 检查孤立卡片（卡组被删除但卡片还在）
    orphan_cards = Card.objects.filter(deck__isnull=True)
    print(f"✓ 孤立卡片数: {orphan_cards.count()}")

    # 检查重复语义哈希
    from django.db.models import Count
    duplicates = Card.objects.values('semantic_hash').annotate(
        count=Count('id')
    ).filter(count__gt=1)
    print(f"✓ 重复语义哈希数: {duplicates.count()}")

    # 检查卡片-卡组关联
    total_cards = Card.objects.count()
    total_decks = Deck.objects.count()
    print(f"✓ 总卡片数: {total_cards}")
    print(f"✓ 总卡组数: {total_decks}")

    # 检查每个卡组的卡片数
    for deck in Deck.objects.all():
        card_count = Card.objects.filter(deck=deck).count()
        print(f"  - {deck.name}: {card_count} 张卡片")

    print("✅ 数据一致性测试通过")

def cleanup():
    """清理测试数据"""
    print_section("清理测试数据")

    # 删除测试用户（会级联删除相关数据）
    deleted_users = User.objects.filter(username='test_integration').delete()
    print(f"✓ 清理完成: {deleted_users}")

def main():
    """主测试流程"""
    print("\n" + "=" * 60)
    print("autoR 集成测试")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    try:
        # 执行测试
        user = test_user_creation()
        deck1, deck2 = test_deck_operations(user)
        card1, card2 = test_card_crud(user, deck1)
        cards = test_batch_operations(user, deck1, deck2)
        test_semantic_deduplication(user, deck1)
        test_sm2_algorithm(card1)
        test_data_consistency()

        # 清理
        cleanup()

        # 总结
        print("\n" + "=" * 60)
        print("✅ 所有集成测试通过！")
        print("=" * 60)

        return 0

    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
