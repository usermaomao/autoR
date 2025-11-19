"""
ECDICT 字典数据导入命令

用法:
    python manage.py import_ecdict /path/to/stardict.csv
"""
import csv
import time
from django.core.management.base import BaseCommand
from cards.models import ECDict


class Command(BaseCommand):
    help = '导入 ECDICT 字典数据到数据库'

    def add_arguments(self, parser):
        parser.add_argument(
            'csv_file',
            type=str,
            help='ECDICT CSV 文件路径 (stardict.csv)'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=1000,
            help='批量导入大小 (默认 1000)'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='限制导入数量 (用于测试)'
        )

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        batch_size = options['batch_size']
        limit = options['limit']

        self.stdout.write(self.style.SUCCESS(f'开始导入 ECDICT 数据: {csv_file}'))
        start_time = time.time()

        # 清空现有数据
        self.stdout.write('清空现有数据...')
        ECDict.objects.all().delete()

        # 读取 CSV 文件
        batch = []
        total = 0
        skipped = 0

        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                # ECDICT CSV 格式:
                # word,phonetic,definition,translation,pos,collins,oxford,tag,bnc,frq,exchange,detail,audio
                reader = csv.DictReader(f)

                for row in reader:
                    if limit and total >= limit:
                        break

                    word = row.get('word', '').strip()
                    if not word:
                        skipped += 1
                        continue

                    # 创建字典对象
                    entry = ECDict(
                        word=word,
                        phonetic=row.get('phonetic', '').strip(),
                        definition=row.get('definition', '').strip(),
                        translation=row.get('translation', '').strip(),
                        pos=row.get('pos', '').strip(),
                        collins=int(row.get('collins', 0) or 0),
                        oxford=row.get('oxford', '').strip().lower() in ['1', 'true', 'yes'],
                        tag=row.get('tag', '').strip(),
                        bnc=int(row.get('bnc') or 0) if row.get('bnc', '').strip() else None,
                        frq=int(row.get('frq') or 0) if row.get('frq', '').strip() else None,
                        exchange=row.get('exchange', '').strip(),
                        detail=row.get('detail', '').strip(),
                        audio=row.get('audio', '').strip(),
                    )

                    batch.append(entry)
                    total += 1

                    # 批量插入
                    if len(batch) >= batch_size:
                        ECDict.objects.bulk_create(batch, ignore_conflicts=True)
                        batch = []
                        self.stdout.write(f'已导入 {total} 条记录...')

                # 插入剩余数据
                if batch:
                    ECDict.objects.bulk_create(batch, ignore_conflicts=True)

            elapsed = time.time() - start_time
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n导入完成！\\n'
                    f'总计: {total} 条\\n'
                    f'跳过: {skipped} 条\\n'
                    f'耗时: {elapsed:.2f} 秒'
                )
            )

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'文件不存在: {csv_file}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'导入失败: {str(e)}'))
