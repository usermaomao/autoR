from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

from .models import Deck, Card, ReviewLog
from .serializers import (
    UserSerializer, UserRegistrationSerializer,
    DeckSerializer, CardSerializer, CardListSerializer,
    ReviewLogSerializer
)


# 认证相关视图
@api_view(['POST'])
@permission_classes([AllowAny])
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
        serializer.save(user=self.request.user)

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
    """获取复习队列"""
    from .services.sm2 import generate_review_queue

    limit = int(request.query_params.get('limit', 50))
    cards = generate_review_queue(request.user, limit)

    serializer = CardListSerializer(cards, many=True)
    return Response({
        'count': len(cards),
        'cards': serializer.data
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

            # 查询汉字（表结构: char, pinyin, radical, strokes, frequency, meaning, examples）
            cursor.execute(
                "SELECT * FROM hanzi WHERE char = ?",
                (char,)
            )
            row = cursor.fetchone()
            conn.close()

            if row:
                # 解析数据
                local_result = {
                    'char': row[0],
                    'pinyin': row[1].split(',') if row[1] else [],  # 多音字数组
                    'radical': row[2] if len(row) > 2 else '',
                    'strokes': row[3] if len(row) > 3 else 0,
                    'frequency': row[4] if len(row) > 4 else 0,
                    'meaning_zh': row[5] if len(row) > 5 else '',
                    'examples': row[6].split('|') if len(row) > 6 and row[6] else [],
                    'source': 'local-dict'
                }

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


