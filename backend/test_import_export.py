#!/usr/bin/env python3
"""
导入导出功能测试脚本
测试 ImportExportService 的核心功能
"""
import os
import sys
import django

# 配置 Django 环境
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from cards.models import Deck, Card
from cards.services.import_export import ImportExportService


def test_generate_semantic_hash():
    """测试语义哈希生成"""
    print("=" * 60)
    print("测试 1: 语义哈希生成")
    print("=" * 60)

    # 测试相同内容生成相同哈希
    hash1 = ImportExportService.generate_semantic_hash("apple", "苹果")
    hash2 = ImportExportService.generate_semantic_hash("Apple", "苹果")
    hash3 = ImportExportService.generate_semantic_hash(" apple ", " 苹果 ")

    print(f"✓ hash1: {hash1}")
    print(f"✓ hash2: {hash2}")
    print(f"✓ hash3: {hash3}")

    assert hash1 == hash2 == hash3, "相同内容应生成相同哈希"
    print("✅ 语义哈希生成测试通过\n")


def test_parse_csv():
    """测试 CSV 解析"""
    print("=" * 60)
    print("测试 2: CSV 解析")
    print("=" * 60)

    csv_content = """Front,Back,Tags
apple,苹果,水果
banana,香蕉,"水果,热带"
"""

    rows, errors = ImportExportService.parse_csv(csv_content)

    print(f"✓ 解析行数: {len(rows)}")
    print(f"✓ 错误数: {len(errors)}")
    print(f"✓ 第一行: {rows[0]}")

    assert len(rows) == 2, "应解析出 2 行数据"
    assert len(errors) == 0, "不应有错误"
    assert rows[0]['Front'] == 'apple', "Front 字段应为 'apple'"
    print("✅ CSV 解析测试通过\n")


def test_parse_json():
    """测试 JSON 解析"""
    print("=" * 60)
    print("测试 3: JSON 解析")
    print("=" * 60)

    json_content = """{
        "cards": [
            {"Front": "hello", "Back": "你好", "Tags": "问候"},
            {"Front": "world", "Back": "世界", "Tags": "名词"}
        ]
    }"""

    rows, errors = ImportExportService.parse_json(json_content)

    print(f"✓ 解析行数: {len(rows)}")
    print(f"✓ 错误数: {len(errors)}")
    print(f"✓ 第一行: {rows[0]}")

    assert len(rows) == 2, "应解析出 2 行数据"
    assert len(errors) == 0, "不应有错误"
    print("✅ JSON 解析测试通过\n")


def test_convert_anki_to_card_data():
    """测试 Anki 格式转换"""
    print("=" * 60)
    print("测试 4: Anki 格式转换")
    print("=" * 60)

    # 创建测试用户和卡组
    user, _ = User.objects.get_or_create(username='test_user')
    deck, _ = Deck.objects.get_or_create(user=user, name='测试卡组')

    anki_row = {
        'Front': 'test',
        'Back': '测试',
        'Tags': 'tag1,tag2'
    }

    card_data = ImportExportService.convert_anki_to_card_data(
        anki_row, user, deck, card_type='en'
    )

    print(f"✓ word: {card_data['word']}")
    print(f"✓ card_type: {card_data['card_type']}")
    print(f"✓ tags: {card_data['tags']}")
    print(f"✓ semantic_hash: {card_data['semantic_hash']}")

    assert card_data['word'] == 'test', "word 字段应为 'test'"
    assert card_data['card_type'] == 'en', "card_type 应为 'en'"
    assert len(card_data['tags']) == 2, "应有 2 个标签"
    print("✅ Anki 格式转换测试通过\n")


def test_check_duplicates():
    """测试重复检测"""
    print("=" * 60)
    print("测试 5: 重复检测")
    print("=" * 60)

    # 创建测试用户和卡组
    user, _ = User.objects.get_or_create(username='test_user')
    deck, _ = Deck.objects.get_or_create(user=user, name='测试卡组')

    # 创建一张已存在的卡片
    semantic_hash = ImportExportService.generate_semantic_hash("duplicate", "重复")
    Card.objects.filter(user=user, word='duplicate').delete()  # 先清理
    existing_card = Card.objects.create(
        user=user,
        deck=deck,
        word='duplicate',
        card_type='en',
        semantic_hash=semantic_hash,
        metadata={'meaning': '重复'}
    )

    # 准备导入数据（包含重复项）
    card_data_list = [
        {
            'user': user,
            'deck': deck,
            'word': 'duplicate',
            'card_type': 'en',
            'semantic_hash': semantic_hash,
            'metadata': {'meaning': '重复'},
            'tags': []
        },
        {
            'user': user,
            'deck': deck,
            'word': 'new_card',
            'card_type': 'en',
            'semantic_hash': ImportExportService.generate_semantic_hash("new_card", "新卡片"),
            'metadata': {'meaning': '新卡片'},
            'tags': []
        }
    ]

    result = ImportExportService.check_duplicates(card_data_list, user)

    print(f"✓ 重复项数: {len(result['duplicates'])}")
    print(f"✓ 唯一项数: {len(result['unique'])}")

    assert len(result['duplicates']) == 1, "应检测到 1 个重复项"
    assert len(result['unique']) == 1, "应有 1 个唯一项"
    print("✅ 重复检测测试通过\n")


def test_full_import():
    """测试完整导入流程"""
    print("=" * 60)
    print("测试 6: 完整导入流程")
    print("=" * 60)

    # 创建测试用户和卡组
    user, _ = User.objects.get_or_create(username='test_user')
    deck, _ = Deck.objects.get_or_create(user=user, name='测试卡组')

    # 清理之前的测试数据
    Card.objects.filter(user=user, word__in=['import1', 'import2']).delete()

    csv_content = """Front,Back,Tags
import1,导入1,测试
import2,导入2,测试
"""

    result = ImportExportService.import_cards(
        file_content=csv_content,
        file_format='csv',
        user=user,
        deck=deck,
        card_type='en',
        conflict_strategy='skip'
    )

    print(f"✓ 总数: {result['total']}")
    print(f"✓ 导入成功: {result['imported']}")
    print(f"✓ 跳过: {result['skipped']}")
    print(f"✓ 失败: {result['failed']}")

    assert result['total'] == 2, "总数应为 2"
    assert result['imported'] == 2, "应成功导入 2 张卡片"
    assert result['failed'] == 0, "不应有失败"

    # 验证数据库中的卡片
    card1 = Card.objects.get(user=user, word='import1')
    assert card1.semantic_hash != '', "semantic_hash 不应为空"

    print("✅ 完整导入流程测试通过\n")


def test_export():
    """测试导出功能"""
    print("=" * 60)
    print("测试 7: 导出功能")
    print("=" * 60)

    # 创建测试数据
    user, _ = User.objects.get_or_create(username='test_user')
    deck, _ = Deck.objects.get_or_create(user=user, name='测试卡组')

    cards = Card.objects.filter(user=user, word__in=['import1', 'import2'])

    # 测试 CSV 导出
    csv_content = ImportExportService.export_cards_to_csv(cards)
    print(f"✓ CSV 内容长度: {len(csv_content)} 字节")
    assert 'Front,Back,Tags' in csv_content, "CSV 应包含标题行"

    # 测试 JSON 导出
    json_content = ImportExportService.export_cards_to_json(cards)
    print(f"✓ JSON 内容长度: {len(json_content)} 字节")
    assert '"cards"' in json_content, "JSON 应包含 cards 字段"

    print("✅ 导出功能测试通过\n")


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("开始导入导出功能测试")
    print("=" * 60 + "\n")

    try:
        test_generate_semantic_hash()
        test_parse_csv()
        test_parse_json()
        test_convert_anki_to_card_data()
        test_check_duplicates()
        test_full_import()
        test_export()

        print("=" * 60)
        print("✅ 所有测试通过！")
        print("=" * 60)

    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
