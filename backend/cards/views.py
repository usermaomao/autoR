from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes, throttle_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.throttling import AnonRateThrottle
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

from .models import Deck, Card, ReviewLog, AIConfig
from .serializers import (
    UserSerializer, UserRegistrationSerializer,
    DeckSerializer, CardSerializer, CardListSerializer,
    ReviewLogSerializer, AIConfigSerializer, AISummarizeRequestSerializer
)


# 自定义速率限制类
class LoginRateThrottle(AnonRateThrottle):
    rate = '10/hour'


class RegisterRateThrottle(AnonRateThrottle):
    rate = '5/hour'


# 认证相关视图
@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([RegisterRateThrottle])
def register_view(request):
    """用户注册"""
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response({
            'user': UserSerializer(user).data,
            'message': '注册成功'
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([LoginRateThrottle])
def login_view(request):
    """用户登录"""
    username = request.data.get('username')
    password = request.data.get('password')

    if not username or not password:
        return Response({
            'error': '用户名和密码不能为空'
        }, status=status.HTTP_400_BAD_REQUEST)

    user = authenticate(request, username=username, password=password)

    if user is not None:
        login(request, user)
        return Response({
            'user': UserSerializer(user).data,
            'message': '登录成功'
        })
    else:
        return Response({
            'error': '用户名或密码错误'
        }, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """用户登出"""
    logout(request)
    return Response({'message': '登出成功'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user_view(request):
    """获取当前用户信息"""
    return Response(UserSerializer(request.user).data)


# ViewSet
class DeckViewSet(viewsets.ModelViewSet):
    """卡组 ViewSet"""
    serializer_class = DeckSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'name']
    ordering = ['-created_at']

    def get_queryset(self):
        return Deck.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CardViewSet(viewsets.ModelViewSet):
    """卡片 ViewSet"""
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['deck', 'card_type', 'state']
    search_fields = ['word', 'notes']
    ordering_fields = ['created_at', 'due_at', 'lapses']
    ordering = ['due_at']

    def get_queryset(self):
        return Card.objects.filter(user=self.request.user).select_related('deck', 'user')

    def get_serializer_class(self):
        if self.action == 'list':
            return CardListSerializer
        return CardSerializer

    def perform_create(self, serializer):
        from django.utils import timezone
        from datetime import timedelta
        from .services.sm2 import LEARNING_STEPS

        # 保存卡片
        card = serializer.save(user=self.request.user)

        # 新卡片设置初始复习时间为10分钟后（学习步骤的第一步）
        if card.state == 'new':
            card.due_at = timezone.now() + timedelta(minutes=LEARNING_STEPS[0])
            card.save(update_fields=['due_at'])

    @action(detail=False, methods=['get'])
    def due_today(self, request):
        """获取今日到期卡片"""
        from django.utils import timezone
        cards = self.get_queryset().filter(
            due_at__lte=timezone.now(),
            state__in=['learning', 'review']
        )
        serializer = self.get_serializer(cards, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def leeches(self, request):
        """获取难项卡片（错误次数>=3）"""
        cards = self.get_queryset().filter(lapses__gte=3).order_by('-lapses')
        serializer = self.get_serializer(cards, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """获取用户卡片统计信息"""
        from django.utils import timezone
        from django.db.models import Count
        from datetime import timedelta

        user_cards = self.get_queryset()
        today = timezone.now().date()

        # 今日待复习数量
        due_today = user_cards.filter(
            due_at__date__lte=today,
            state__in=['learning', 'review']
        ).count()

        # 新卡片数量
        new_cards = user_cards.filter(state='new').count()

        # 总卡片数
        total_cards = user_cards.count()

        # 计算连续打卡天数
        review_logs = ReviewLog.objects.filter(user=request.user).values('reviewed_at__date').distinct().order_by('-reviewed_at__date')
        streak = 0
        check_date = today

        for log in review_logs:
            log_date = log['reviewed_at__date']
            if log_date == check_date:
                streak += 1
                check_date -= timedelta(days=1)
            elif log_date < check_date:
                break

        return Response({
            'due_today': due_today,
            'new_cards': new_cards,
            'total_cards': total_cards,
            'streak': streak
        })

    @action(detail=False, methods=['post'])
    def preview_svg(self, request):
        """预览 SVG 卡片（不保存到数据库）"""
        from .services.svg_generator import generate_svg_card

        # 提取请求数据
        word = request.data.get('word')
        card_type = request.data.get('card_type')
        metadata = request.data.get('metadata', {})

        # 验证必填字段
        if not word or not card_type:
            return Response({
                'error': '缺少必填字段: word 或 card_type'
            }, status=status.HTTP_400_BAD_REQUEST)

        if card_type not in ['en', 'zh']:
            return Response({
                'error': 'card_type 必须是 "en" 或 "zh"'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # 生成 SVG
            svg_front, svg_back = generate_svg_card(
                word=word,
                card_type=card_type,
                metadata=metadata
            )

            return Response({
                'svg_front': svg_front,
                'svg_back': svg_back,
                'word': word,
                'card_type': card_type
            })

        except Exception as e:
            return Response({
                'error': f'SVG 生成失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ReviewLogViewSet(viewsets.ReadOnlyModelViewSet):
    """复习记录 ViewSet（只读）"""
    serializer_class = ReviewLogSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['card', 'quality']
    ordering_fields = ['reviewed_at']
    ordering = ['-reviewed_at']

    def get_queryset(self):
        return ReviewLog.objects.filter(user=self.request.user).select_related('card', 'user')


# 复习相关 API
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_review_queue(request):
    """
    获取复习队列

    如果有待复习卡片，返回正常的复习队列
    如果没有待复习卡片，返回掌握度最低的 10 张卡片用于巩固练习
    """
    from .services.sm2 import generate_review_queue, get_lowest_mastery_cards

    limit = int(request.query_params.get('limit', 50))
    result = generate_review_queue(request.user, limit)

    # 如果没有待复习卡片，返回掌握度最低的卡片
    if not result['cards']:
        lowest_mastery_cards = get_lowest_mastery_cards(request.user, limit=10)

        serializer = CardListSerializer(lowest_mastery_cards, many=True)
        return Response({
            'count': len(lowest_mastery_cards),
            'cards': serializer.data,
            'stats': {
                'due_count': 0,
                'leech_count': 0,
                'new_count': 0,
                'total_new': result['stats']['total_new'],
                'session_limit': limit,
                'returned_count': len(lowest_mastery_cards),
                'message': '今日复习已完成！以下是掌握度最低的卡片，建议加强练习。',
                'is_practice_mode': True,  # 标记为练习模式
            },
        })

    serializer = CardListSerializer(result['cards'], many=True)
    return Response({
        'count': len(result['cards']),
        'cards': serializer.data,
        'stats': {
            **result['stats'],
            'is_practice_mode': False,  # 标记为正常复习模式
        },
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_review(request):
    """提交复习评分"""
    from .services.sm2 import process_review

    card_id = request.data.get('card_id')
    quality = request.data.get('quality')
    time_taken = request.data.get('time_taken', 0)

    if not card_id or quality is None:
        return Response({
            'error': '缺少必需参数'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        card = Card.objects.get(id=card_id, user=request.user)
    except Card.DoesNotExist:
        return Response({
            'error': '卡片不存在'
        }, status=status.HTTP_404_NOT_FOUND)

    # 处理复习
    review_log = process_review(card, quality, time_taken)

    return Response({
        'card': CardSerializer(card).data,
        'review_log': ReviewLogSerializer(review_log).data,
        'message': '复习已提交'
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def undo_review(request):
    """撤销上一次复习"""
    from .services.sm2 import undo_review as undo_review_func

    # 获取用户最近的一条复习记录
    try:
        review_log = ReviewLog.objects.filter(
            user=request.user
        ).order_by('-reviewed_at').first()

        if not review_log:
            return Response({
                'error': '没有可撤销的复习记录'
            }, status=status.HTTP_404_NOT_FOUND)

        # 撤销复习
        card = review_log.card
        undo_review_func(review_log)

        return Response({
            'card': CardSerializer(card).data,
            'message': '复习已撤销'
        })

    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# 字典查询 API
@api_view(['GET'])
@permission_classes([AllowAny])
def lookup_english(request, word):
    """查询英语单词"""
    from .models import ECDict
    from django.core.cache import cache

    # 尝试从缓存获取
    cache_key = f'dict:en:{word.lower()}'
    cached_result = cache.get(cache_key)
    if cached_result:
        cached_result['source'] = 'cache'
        return Response(cached_result)

    # 从数据库查询
    try:
        entry = ECDict.objects.get(word__iexact=word)

        # 提取 CEFR 等级 (从 tag 字段)
        cefr = None
        if entry.tag:
            tags = entry.tag.lower().split()
            cefr_levels = ['a1', 'a2', 'b1', 'b2', 'c1', 'c2']
            for tag in tags:
                if tag in cefr_levels:
                    cefr = tag.upper()
                    break

        result = {
            'word': entry.word,
            'ipa': entry.phonetic,
            'pos': entry.pos,
            'meaning_en': entry.definition,
            'meaning_zh': entry.translation,
            'frequency': entry.frq,
            'cefr': cefr,
            'examples': [],  # ECDICT 无例句
            'collins': entry.collins,
            'oxford': entry.oxford,
            'source': 'local-dict'
        }

        # 缓存结果（1天）
        cache.set(cache_key, result, timeout=86400)

        return Response(result)

    except ECDict.DoesNotExist:
        return Response({
            'error': 'Word not found',
            'source': 'manual'
        }, status=status.HTTP_404_NOT_FOUND)


def _save_hanzi_to_local(char: str, result: dict, db_path: str):
    """
    将百度汉语查询结果保存到本地数据库
    使用单独的 hanzi_baidu 表避免与原有 hanzi 表冲突

    Args:
        char: 汉字
        result: 百度汉语返回的结果字典
        db_path: 数据库路径
    """
    import sqlite3
    import os
    import logging

    logger = logging.getLogger(__name__)

    try:
        # 确保数据库目录存在
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 创建专用表 hanzi_baidu（如果不存在）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hanzi_baidu (
                char TEXT PRIMARY KEY,
                pinyin TEXT,
                radical TEXT,
                strokes INTEGER,
                frequency INTEGER DEFAULT 0,
                meaning TEXT,
                examples TEXT,
                traditional TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 插入或更新数据
        cursor.execute("""
            INSERT OR REPLACE INTO hanzi_baidu
            (char, pinyin, radical, strokes, frequency, meaning, examples, traditional, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            char,
            ','.join(result.get('pinyin', [])) if isinstance(result.get('pinyin'), list) else str(result.get('pinyin', '')),
            result.get('radical', ''),
            result.get('strokes', 0),
            result.get('frequency', 0),
            result.get('meaning_zh', ''),
            '|'.join(result.get('examples', [])) if isinstance(result.get('examples'), list) else '',
            result.get('traditional', '')
        ))

        conn.commit()
        conn.close()

        logger.info(f"汉字 '{char}' 已保存到本地数据库 (hanzi_baidu 表)")

    except Exception as e:
        logger.error(f"保存汉字到本地数据库失败: {e}")


@api_view(['GET'])
@permission_classes([AllowAny])
def lookup_hanzi(request, char):
    """
    查询汉字 - 四层降级策略
    L1: 缓存 (cache)
    L2: 本地字典库 (local-dict)
    L3: 百度汉语API (baidu-hanyu)
    L4: 手动输入 (manual)
    """
    import sqlite3
    from django.conf import settings
    from django.core.cache import cache
    import os
    from .services.baidu_hanyu import BaiduHanyuService

    # L1: 尝试从缓存获取
    cache_key = f'dict:zh:{char}'
    cached_result = cache.get(cache_key)
    if cached_result:
        cached_result['source'] = 'cache'
        return Response(cached_result)

    # L2: 从本地汉字数据库查询
    hanzi_db_path = os.path.join(settings.BASE_DIR.parent, 'data', 'hanzi_local.db')

    local_result = None
    if os.path.exists(hanzi_db_path):
        try:
            conn = sqlite3.connect(hanzi_db_path)
            cursor = conn.cursor()

            # 先查询 hanzi_baidu 表（百度API缓存）
            cursor.execute(
                "SELECT char, pinyin, radical, strokes, frequency, meaning, examples, traditional FROM hanzi_baidu WHERE char = ?",
                (char,)
            )
            row = cursor.fetchone()

            # 如果 hanzi_baidu 没有，再查询原有的 hanzi 表
            if not row:
                cursor.execute(
                    "SELECT * FROM hanzi WHERE character = ?",
                    (char,)
                )
                row = cursor.fetchone()

                # 旧表结构兼容处理
                if row and len(row) > 5:
                    # 旧结构: id, character, decomposition, rationality_score, pinyin, traditional, ...
                    local_result = {
                        'char': row[1],  # character
                        'pinyin': row[4].split(',') if row[4] else [],  # pinyin
                        'traditional': row[5] if len(row) > 5 else '',  # traditional
                        'source': 'local-dict'
                    }
            else:
                # 新表结构 hanzi_baidu
                local_result = {
                    'char': row[0],
                    'pinyin': row[1].split(',') if row[1] else [],
                    'radical': row[2] or '',
                    'strokes': row[3] or 0,
                    'frequency': row[4] or 0,
                    'meaning_zh': row[5] or '',
                    'examples': row[6].split('|') if row[6] else [],
                    'traditional': row[7] or '',
                    'source': 'local-dict'
                }

            conn.close()

            if local_result:
                # 缓存结果（1天）
                cache.set(cache_key, local_result, timeout=86400)
                return Response(local_result)

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"本地汉字数据库查询失败: {e}")

    # L3: 本地未找到,调用百度汉语API
    try:
        baidu_result = BaiduHanyuService.lookup(char)

        if baidu_result:
            # 缓存结果（1天）
            cache.set(cache_key, baidu_result, timeout=86400)

            # 自动保存到本地数据库
            _save_hanzi_to_local(char, baidu_result, hanzi_db_path)

            return Response(baidu_result)

    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"百度汉语查询失败: {e}")

    # L4: 所有数据源均失败,返回手动输入提示
    return Response({
        'error': 'Character not found in any data source',
        'source': 'manual',
        'message': '未找到该字的字典信息,请手动输入释义'
    }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([AllowAny])
def infer_pinyin(request):
    """基于语境推断多音字读音"""
    import jieba
    from pypinyin import lazy_pinyin, Style

    char = request.data.get('char')
    context = request.data.get('context', '')

    if not char:
        return Response({
            'error': '缺少必需参数: char'
        }, status=status.HTTP_400_BAD_REQUEST)

    if not context:
        # 无语境，返回所有候选
        return Response({
            'char': char,
            'pinyin': None,
            'confidence': 0,
            'alternatives': lazy_pinyin(char, style=Style.TONE)
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
                'alternatives': lazy_pinyin(char, style=Style.TONE)
            })

    # 降级：使用字符级推断
    pinyin = lazy_pinyin(char, style=Style.TONE)[0]
    return Response({
        'char': char,
        'pinyin': pinyin,
        'confidence': 0.6,  # 中等置信度
        'alternatives': lazy_pinyin(char, style=Style.TONE)
    })


# ==================== 导入导出功能 ====================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def import_cards(request):
    """
    导入卡片

    POST /api/cards/import/
    Content-Type: multipart/form-data

    参数:
    - file: 文件对象 (CSV 或 JSON)
    - format: 文件格式 ('csv' 或 'json')
    - deck_id: 目标卡组ID
    - card_type: 卡片类型 ('en' 或 'zh')，默认 'en'
    - conflict_strategy: 冲突处理策略 ('skip', 'overwrite', 'merge')，默认 'skip'

    返回:
    {
        "total": 1000,
        "imported": 850,
        "skipped": 100,
        "failed": 50,
        "errors": ["错误信息1", ...],
        "duplicates": [{"index": 1, "word": "apple", ...}, ...]
    }
    """
    from .services.import_export import ImportExportService

    serializer = CardImportSerializer(data=request.data, context={'request': request})
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # 获取参数
    uploaded_file = serializer.validated_data['file']
    file_format = serializer.validated_data['format']
    deck_id = serializer.validated_data['deck_id']
    card_type = serializer.validated_data['card_type']
    conflict_strategy = serializer.validated_data['conflict_strategy']

    try:
        # 读取文件内容
        file_content = uploaded_file.read().decode('utf-8')

        # 获取卡组
        deck = Deck.objects.get(id=deck_id, user=request.user)

        # 执行导入
        result = ImportExportService.import_cards(
            file_content=file_content,
            file_format=file_format,
            user=request.user,
            deck=deck,
            card_type=card_type,
            conflict_strategy=conflict_strategy
        )

        return Response(result, status=status.HTTP_200_OK)

    except UnicodeDecodeError:
        return Response(
            {'error': '文件编码错误，请使用 UTF-8 编码'},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {'error': f'导入失败: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_cards(request):
    """
    导出卡片

    GET /api/cards/export/?format=csv&deck_id=1

    参数:
    - format: 导出格式 ('csv' 或 'json')，默认 'csv'
    - deck_id: 卡组ID（可选），不指定则导出所有卡片

    返回:
    文件下载（CSV 或 JSON）
    """
    from .services.import_export import ImportExportService
    from django.http import HttpResponse

    serializer = CardExportSerializer(data=request.query_params)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    file_format = serializer.validated_data['format']
    deck_id = serializer.validated_data.get('deck_id')

    try:
        # 查询卡片
        cards = Card.objects.filter(user=request.user).select_related('deck')
        if deck_id:
            cards = cards.filter(deck_id=deck_id)

        # 导出
        if file_format == 'csv':
            content = ImportExportService.export_cards_to_csv(cards)
            content_type = 'text/csv'
            filename = f'cards_export_{timezone.now().strftime("%Y%m%d")}.csv'
        else:  # json
            content = ImportExportService.export_cards_to_json(cards)
            content_type = 'application/json'
            filename = f'cards_export_{timezone.now().strftime("%Y%m%d")}.json'

        # 创建响应
        response = HttpResponse(content, content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    except Exception as e:
        return Response(
            {'error': f'导出失败: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# AI配置相关视图
class AIConfigViewSet(viewsets.ModelViewSet):
    """AI配置 ViewSet"""
    serializer_class = AIConfigSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'put', 'patch']  # 不允许删除

    def get_queryset(self):
        # 每个用户只有一个配置
        return AIConfig.objects.filter(user=self.request.user)

    def get_object(self):
        # 获取或创建用户的AI配置
        config, created = AIConfig.objects.get_or_create(
            user=self.request.user,
            defaults={
                'provider': 'openai',
                'base_url': 'https://api.openai.com/v1',
                'model_name': 'gpt-3.5-turbo',
                'enabled': False
            }
        )
        return config

    def list(self, request, *args, **kwargs):
        # 直接返回当前用户的配置（单个对象，不是列表）
        config = self.get_object()
        serializer = self.get_serializer(config)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        # 如果已存在配置，则更新而非创建
        try:
            config = AIConfig.objects.get(user=request.user)
            serializer = self.get_serializer(config, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        except AIConfig.DoesNotExist:
            return super().create(request, *args, **kwargs)

    @action(detail=False, methods=['post'])
    def test_connection(self, request):
        """测试AI连接"""
        config = self.get_object()

        if not config.enabled:
            return Response(
                {'error': 'AI功能未启用'},
                status=status.HTTP_400_BAD_REQUEST
            )

        api_key = config.get_api_key()
        if not api_key:
            return Response(
                {'error': '未配置API Key'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # 测试连接
            from .services.ai_service import AIService
            ai_service = AIService(config)
            result = ai_service.test_connection()

            return Response({
                'success': True,
                'message': '连接测试成功',
                'model': config.model_name
            })
        except Exception as e:
            return Response(
                {'error': f'连接测试失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'], url_path='test-chinese-prompt')
    def test_chinese_prompt(self, request):
        """测试汉字提示词生成"""
        import time

        config = self.get_object()

        if not config.enabled:
            return Response(
                {'error': 'AI功能未启用，请先在配置中启用AI功能'},
                status=status.HTTP_400_BAD_REQUEST
            )

        api_key = config.get_api_key()
        if not api_key:
            return Response(
                {'error': '未配置API Key，请先在配置中填写API Key'},
                status=status.HTTP_400_BAD_REQUEST
            )

        char = request.data.get('char', '').strip()
        if not char or len(char) != 1:
            return Response(
                {'error': '请输入一个汉字'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            from .services.ai_service import AIService

            ai_service = AIService(config)

            # 调用AI生成汉字学习卡片
            start_time = time.time()
            result = ai_service.summarize_word(char, 'zh', context='')
            duration = int((time.time() - start_time) * 1000)

            # 获取发送的提示词
            prompt = ai_service._build_chinese_prompt(char, '')

            # 解析AI返回的内容
            parsed = self._parse_chinese_content(result)

            return Response({
                'success': True,
                'char': char,
                'prompt': prompt,
                'response': result,
                'parsed': parsed,
                'model': config.model_name,
                'temperature': config.temperature,
                'max_tokens': config.max_tokens,
                'duration': duration
            })

        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()

            return Response(
                {
                    'error': f'AI生成失败: {str(e)}',
                    'detail': error_detail
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _parse_chinese_content(self, content):
        """解析汉字AI返回内容（与前端逻辑一致）"""
        import re

        result = {
            'pinyin': [],
            'meaning': '',
            'radical': '',
            'strokes': '',
            'structure': '',
            'examples': [],
            'memoryTips': '',
            'confusion': '',
            'exercises': '',
            'keyPoints': '',
            'writingTips': '',
            'memoryScript': '',
            'summary': ''
        }

        if not content:
            return result

        try:
            # 1. 解析关键要点
            key_points_match = re.search(r'\*\*1\.\s*关键要点\*\*[\s\S]*?([\s\S]*?)(?=\n\*\*2\.|$)', content, re.IGNORECASE)
            if key_points_match:
                lines = [line.strip() for line in key_points_match.group(1).strip().split('\n')]
                result['keyPoints'] = '\n'.join([line.replace('- ', '', 1) for line in lines if line.startswith('-')])

            # 2. 解析核心卡片
            core_card_match = re.search(r'\*\*2\.\s*核心卡片\*\*[\s\S]*?([\s\S]*?)(?=\n\*\*3\.|$)', content, re.IGNORECASE)
            if core_card_match:
                core_text = core_card_match.group(1)

                # 提取拼音
                pinyin_match = re.search(r'拼音[与和]?声调[：:]\s*(.+?)(?:\n|$)', core_text, re.IGNORECASE)
                if pinyin_match:
                    pinyin_text = re.sub(r'[（）\(\)\[\]【】]', '', pinyin_match.group(1).strip())
                    result['pinyin'] = [p.strip() for p in re.split(r'[,，、；;]', pinyin_text) if p.strip()]

                # 提取部首/结构/笔画
                radical_match = re.search(r'部首[/\s]*结构[/\s]*笔画[：:]\s*(.+?)(?:\n|$)', core_text, re.IGNORECASE)
                if radical_match:
                    parts = [p.strip() for p in re.split(r'[；;，,]', radical_match.group(1))]
                    if len(parts) > 0:
                        result['radical'] = parts[0]
                    if len(parts) > 1:
                        result['structure'] = parts[1]
                    if len(parts) > 2:
                        result['strokes'] = re.sub(r'[^0-9]', '', parts[2])

                # 提取高频义项
                meaning_match = re.search(r'高频义项[^：:]*[：:]\s*(.+?)(?:\n|$)', core_text, re.IGNORECASE)
                if meaning_match:
                    result['meaning'] = meaning_match.group(1).strip()

                # 提取常见词
                words_match = re.search(r'常见词[^：:]*[：:]\s*(.+?)(?:\n|$)', core_text, re.IGNORECASE)
                if words_match:
                    result['examples'] = [w.strip() for w in re.split(r'[、，,]', words_match.group(1)) if w.strip()]

            # 3-4. 解析构形拆解、读音记忆
            structure_match = re.search(r'\*\*3\.\s*构形拆解[与和]?联想\*\*[\s\S]*?([\s\S]*?)(?=\n\*\*4\.|$)', content, re.IGNORECASE)
            pronunciation_match = re.search(r'\*\*4\.\s*读音记忆\*\*[\s\S]*?([\s\S]*?)(?=\n\*\*5\.|$)', content, re.IGNORECASE)

            memory_parts = []
            if structure_match:
                lines = [line.strip() for line in structure_match.group(1).strip().split('\n')]
                structure_text = '\n'.join([line.replace('- ', '', 1) for line in lines if line.startswith('-')])
                if structure_text:
                    memory_parts.append('**构形记忆**:\n' + structure_text)

            if pronunciation_match:
                lines = [line.strip() for line in pronunciation_match.group(1).strip().split('\n')]
                pron_text = '\n'.join([line.replace('- ', '', 1) for line in lines if line.startswith('-')])
                if pron_text:
                    memory_parts.append('**读音记忆**:\n' + pron_text)

            result['memoryTips'] = '\n\n'.join(memory_parts)

            # 5. 解析书写与笔顺
            writing_match = re.search(r'\*\*5\.\s*书写[与和]?笔顺\*\*[\s\S]*?([\s\S]*?)(?=\n\*\*6\.|$)', content, re.IGNORECASE)
            if writing_match:
                lines = [line.strip() for line in writing_match.group(1).strip().split('\n')]
                result['writingTips'] = '\n'.join([line.replace('- ', '', 1) for line in lines if line.startswith('-')])

            # 6. 解析易混辨析
            confusion_match = re.search(r'\*\*6\.\s*易混辨析\*\*[\s\S]*?([\s\S]*?)(?=\n\*\*7\.|$)', content, re.IGNORECASE)
            if confusion_match:
                lines = [line.strip() for line in confusion_match.group(1).strip().split('\n')]
                result['confusion'] = '\n'.join([re.sub(r'^-\s*与?\s*', '', line) for line in lines if line.startswith('-')])

            # 7. 解析语境与搭配
            context_match = re.search(r'\*\*7\.\s*语境[与和]?搭配\*\*[\s\S]*?([\s\S]*?)(?=\n\*\*8\.|$)', content, re.IGNORECASE)
            if context_match:
                context_text = context_match.group(1)
                examples_match2 = re.search(r'高频搭配[^：:]*[：:]\s*(.+?)(?:\n|$)', context_text, re.IGNORECASE)
                sentence_match = re.search(r'造句[^：:]*[：:]\s*(.+?)(?:\n|$)', context_text, re.IGNORECASE)

                if examples_match2 and not result['examples']:
                    result['examples'] = [w.strip() for w in re.split(r'[、，,]', examples_match2.group(1)) if w.strip()]
                if sentence_match:
                    result['examples'].append(sentence_match.group(1).strip())

            # 8. 解析记忆方案设计
            memory_script_match = re.search(r'\*\*8\.\s*记忆方案设计\*\*[\s\S]*?([\s\S]*?)(?=\n\*\*9\.|$)', content, re.IGNORECASE)
            if memory_script_match:
                lines = [line.strip() for line in memory_script_match.group(1).strip().split('\n')]
                result['memoryScript'] = '\n'.join([line.replace('- ', '', 1) for line in lines if line.startswith('-')])

            # 9. 解析一句话总结
            summary_match = re.search(r'\*\*9\.\s*一句话总结\*\*[\s\S]*?-\s*(.+?)(?:\n|$)', content, re.IGNORECASE)
            if summary_match:
                result['summary'] = summary_match.group(1).strip()

        except Exception as e:
            print(f"解析错误: {e}")

        return result

    @action(detail=False, methods=['get'], url_path='default-prompt')
    def get_default_prompt(self, request):
        """获取默认的汉字提示词模板"""
        from .services.ai_service import AIService

        default_prompt = AIService.get_default_chinese_prompt()

        return Response({
            'prompt': default_prompt,
            'description': '默认汉字学习卡片生成提示词。使用{char}作为汉字占位符，使用{context}作为额外信息占位符。'
        })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ai_summarize_view(request):
    """AI总结词汇"""
    serializer = AISummarizeRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # 获取用户的AI配置
    try:
        config = AIConfig.objects.get(user=request.user)
    except AIConfig.DoesNotExist:
        return Response(
            {'error': '请先配置AI设置'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not config.enabled:
        return Response(
            {'error': 'AI功能未启用'},
            status=status.HTTP_400_BAD_REQUEST
        )

    api_key = config.get_api_key()
    if not api_key:
        return Response(
            {'error': '未配置API Key'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        from .services.ai_service import AIService
        ai_service = AIService(config)

        word = serializer.validated_data['word']
        card_type = serializer.validated_data['card_type']
        context = serializer.validated_data.get('context', '')

        summary = ai_service.summarize_word(word, card_type, context)

        return Response({
            'word': word,
            'summary': summary,
            'model': config.model_name
        })
    except Exception as e:
        return Response(
            {'error': f'AI总结失败: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

