"""
卡片导入导出服务

提供 CSV/JSON 格式的卡片导入导出功能，支持 Anki 格式兼容。
"""
import csv
import json
import hashlib
from io import StringIO
from typing import List, Dict, Tuple, Optional
from django.contrib.auth.models import User
from ..models import Card, Deck


class ImportExportService:
    """导入导出服务类"""

    # Anki 字段映射（固定映射策略）
    ANKI_FIELD_MAPPING = {
        'Front': 'word',
        'Back': 'metadata',  # 存入 metadata.meaning
        'Tags': 'tags',
    }

    @staticmethod
    def generate_semantic_hash(word: str, meaning: str) -> str:
        """
        生成语义指纹哈希

        基于核心字段生成 MD5 哈希，用于检测重复卡片。
        忽略空格和大小写差异。

        Args:
            word: 单词/汉字
            meaning: 释义

        Returns:
            32位 MD5 哈希字符串
        """
        # 规范化文本
        normalized_word = word.strip().lower()
        normalized_meaning = meaning.strip().lower()

        # 生成哈希
        content = f"{normalized_word}|{normalized_meaning}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()

    @staticmethod
    def parse_csv(file_content: str) -> Tuple[List[Dict], List[str]]:
        """
        解析 CSV 文件内容

        Args:
            file_content: CSV 文件内容字符串

        Returns:
            (解析的数据列表, 错误列表)
        """
        rows = []
        errors = []

        try:
            # 使用 StringIO 包装内容
            csv_file = StringIO(file_content)
            reader = csv.DictReader(csv_file)

            for line_num, row in enumerate(reader, start=2):  # 从第2行开始（第1行是header）
                try:
                    # 验证必需字段
                    if not row.get('Front') or not row.get('Back'):
                        errors.append(f"第 {line_num} 行: 缺少 Front 或 Back 字段")
                        continue

                    rows.append(row)
                except Exception as e:
                    errors.append(f"第 {line_num} 行: {str(e)}")

        except Exception as e:
            errors.append(f"CSV 解析失败: {str(e)}")

        return rows, errors

    @staticmethod
    def parse_json(file_content: str) -> Tuple[List[Dict], List[str]]:
        """
        解析 JSON 文件内容

        Args:
            file_content: JSON 文件内容字符串

        Returns:
            (解析的数据列表, 错误列表)
        """
        errors = []

        try:
            data = json.loads(file_content)

            # 支持两种 JSON 格式
            # 1. 数组格式: [{}, {}, ...]
            # 2. 对象格式: {"cards": [{}, {}, ...]}
            if isinstance(data, dict) and 'cards' in data:
                rows = data['cards']
            elif isinstance(data, list):
                rows = data
            else:
                errors.append("JSON 格式错误: 需要数组或包含 'cards' 键的对象")
                return [], errors

            # 验证每一条记录
            validated_rows = []
            for idx, row in enumerate(rows, start=1):
                if not isinstance(row, dict):
                    errors.append(f"第 {idx} 条: 不是有效的对象")
                    continue

                if not row.get('Front') or not row.get('Back'):
                    errors.append(f"第 {idx} 条: 缺少 Front 或 Back 字段")
                    continue

                validated_rows.append(row)

            return validated_rows, errors

        except json.JSONDecodeError as e:
            errors.append(f"JSON 解析失败: {str(e)}")
            return [], errors
        except Exception as e:
            errors.append(f"处理失败: {str(e)}")
            return [], errors

    @staticmethod
    def convert_anki_to_card_data(row: Dict, user: User, deck: Deck, card_type: str = 'en') -> Dict:
        """
        将 Anki 格式数据转换为 Card 模型数据

        Args:
            row: Anki 格式的行数据
            user: 用户对象
            deck: 卡组对象
            card_type: 卡片类型 ('en' 或 'zh')

        Returns:
            Card 模型字段字典
        """
        # 基础字段
        word = row.get('Front', '').strip()
        meaning = row.get('Back', '').strip()

        # 标签处理
        tags_str = row.get('Tags', '')
        if isinstance(tags_str, str):
            tags = [tag.strip() for tag in tags_str.split(',') if tag.strip()]
        elif isinstance(tags_str, list):
            tags = tags_str
        else:
            tags = []

        # 元数据
        metadata = {
            'meaning_zh': meaning if card_type == 'en' else '',
            'meaning': meaning,
        }

        # 生成语义哈希
        semantic_hash = ImportExportService.generate_semantic_hash(word, meaning)

        return {
            'user': user,
            'deck': deck,
            'word': word,
            'card_type': card_type,
            'metadata': metadata,
            'tags': tags,
            'semantic_hash': semantic_hash,
        }

    @staticmethod
    def check_duplicates(card_data_list: List[Dict], user: User) -> Dict[str, List]:
        """
        检查重复卡片

        Args:
            card_data_list: 待导入的卡片数据列表
            user: 用户对象

        Returns:
            {
                'duplicates': [(index, existing_card), ...],
                'unique': [card_data, ...]
            }
        """
        duplicates = []
        unique = []

        # 提取所有哈希值
        hashes = [data['semantic_hash'] for data in card_data_list]

        # 批量查询数据库中已存在的卡片
        existing_cards = Card.objects.filter(
            user=user,
            semantic_hash__in=hashes
        ).only('id', 'word', 'semantic_hash', 'metadata', 'created_at')

        # 创建哈希 -> 卡片的映射
        hash_to_card = {card.semantic_hash: card for card in existing_cards}

        # 检查每条数据
        for idx, card_data in enumerate(card_data_list):
            semantic_hash = card_data['semantic_hash']
            if semantic_hash in hash_to_card:
                duplicates.append((idx, hash_to_card[semantic_hash]))
            else:
                unique.append(card_data)

        return {
            'duplicates': duplicates,
            'unique': unique,
        }

    @staticmethod
    def import_cards(
        file_content: str,
        file_format: str,
        user: User,
        deck: Deck,
        card_type: str = 'en',
        conflict_strategy: str = 'skip'
    ) -> Dict:
        """
        导入卡片

        Args:
            file_content: 文件内容字符串
            file_format: 文件格式 ('csv' 或 'json')
            user: 用户对象
            deck: 卡组对象
            card_type: 卡片类型 ('en' 或 'zh')
            conflict_strategy: 冲突处理策略 ('skip', 'overwrite', 'merge')

        Returns:
            {
                'total': 总数,
                'imported': 导入成功数,
                'skipped': 跳过数,
                'failed': 失败数,
                'errors': 错误列表,
                'duplicates': 重复项详情
            }
        """
        # 解析文件
        if file_format == 'csv':
            rows, parse_errors = ImportExportService.parse_csv(file_content)
        elif file_format == 'json':
            rows, parse_errors = ImportExportService.parse_json(file_content)
        else:
            return {
                'total': 0,
                'imported': 0,
                'skipped': 0,
                'failed': 0,
                'errors': [f"不支持的格式: {file_format}"],
                'duplicates': [],
            }

        if parse_errors:
            return {
                'total': len(rows),
                'imported': 0,
                'skipped': 0,
                'failed': len(rows),
                'errors': parse_errors,
                'duplicates': [],
            }

        # 转换为 Card 数据格式
        card_data_list = [
            ImportExportService.convert_anki_to_card_data(row, user, deck, card_type)
            for row in rows
        ]

        # 检查重复
        duplicate_check = ImportExportService.check_duplicates(card_data_list, user)
        duplicates = duplicate_check['duplicates']
        unique_cards = duplicate_check['unique']

        imported_count = 0
        skipped_count = 0
        failed_count = 0
        errors = []
        duplicate_details = []

        # 处理重复卡片
        if conflict_strategy == 'skip':
            # 跳过所有重复
            skipped_count = len(duplicates)
            duplicate_details = [
                {
                    'index': idx,
                    'word': card_data_list[idx]['word'],
                    'existing_id': existing_card.id,
                    'reason': '重复卡片'
                }
                for idx, existing_card in duplicates
            ]

        elif conflict_strategy == 'overwrite':
            # 覆盖重复卡片
            for idx, existing_card in duplicates:
                card_data = card_data_list[idx]
                try:
                    # 更新现有卡片
                    for key, value in card_data.items():
                        if key not in ['user', 'semantic_hash']:
                            setattr(existing_card, key, value)
                    existing_card.save()
                    imported_count += 1
                except Exception as e:
                    failed_count += 1
                    errors.append(f"第 {idx + 1} 条覆盖失败: {str(e)}")

        elif conflict_strategy == 'merge':
            # 合并元数据（保留两者）
            for idx, existing_card in duplicates:
                card_data = card_data_list[idx]
                try:
                    # 合并标签
                    existing_tags = set(existing_card.tags)
                    new_tags = set(card_data['tags'])
                    existing_card.tags = list(existing_tags | new_tags)

                    # 合并元数据
                    existing_card.metadata.update(card_data['metadata'])
                    existing_card.save()
                    imported_count += 1
                except Exception as e:
                    failed_count += 1
                    errors.append(f"第 {idx + 1} 条合并失败: {str(e)}")

        # 批量创建新卡片
        try:
            new_cards = [Card(**data) for data in unique_cards]
            Card.objects.bulk_create(new_cards)
            imported_count += len(new_cards)
        except Exception as e:
            failed_count += len(unique_cards)
            errors.append(f"批量创建失败: {str(e)}")

        return {
            'total': len(rows),
            'imported': imported_count,
            'skipped': skipped_count,
            'failed': failed_count,
            'errors': errors,
            'duplicates': duplicate_details,
        }

    @staticmethod
    def export_cards_to_csv(cards) -> str:
        """
        导出卡片到 CSV 格式

        Args:
            cards: Card QuerySet

        Returns:
            CSV 内容字符串
        """
        output = StringIO()
        fieldnames = ['Front', 'Back', 'Tags', 'State', 'Interval', 'EF', 'Created']
        writer = csv.DictWriter(output, fieldnames=fieldnames)

        writer.writeheader()
        for card in cards:
            # 提取释义
            meaning = card.metadata.get('meaning', '') or card.metadata.get('meaning_zh', '')

            writer.writerow({
                'Front': card.word,
                'Back': meaning,
                'Tags': ','.join(card.tags),
                'State': card.get_state_display(),
                'Interval': card.interval,
                'EF': round(card.ef, 2),
                'Created': card.created_at.strftime('%Y-%m-%d'),
            })

        return output.getvalue()

    @staticmethod
    def export_cards_to_json(cards) -> str:
        """
        导出卡片到 JSON 格式

        Args:
            cards: Card QuerySet

        Returns:
            JSON 内容字符串
        """
        cards_data = []
        for card in cards:
            # 提取释义
            meaning = card.metadata.get('meaning', '') or card.metadata.get('meaning_zh', '')

            cards_data.append({
                'Front': card.word,
                'Back': meaning,
                'Tags': card.tags,
                'State': card.state,
                'Interval': card.interval,
                'EF': card.ef,
                'Metadata': card.metadata,
                'Created': card.created_at.isoformat(),
            })

        return json.dumps({'cards': cards_data}, ensure_ascii=False, indent=2)
