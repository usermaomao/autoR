from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Deck(models.Model):
    """卡组模型"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='decks')
    name = models.CharField(max_length=200, verbose_name='卡组名称')
    description = models.TextField(blank=True, verbose_name='描述')

    # 配置字段
    daily_new_limit = models.IntegerField(default=20, verbose_name='每日新卡上限')
    daily_review_limit = models.IntegerField(default=200, verbose_name='每日复习上限')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '卡组'
        verbose_name_plural = '卡组'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.name}"


class Card(models.Model):
    """卡片模型"""

    CARD_TYPE_CHOICES = [
        ('en', '英语'),
        ('zh', '汉字'),
    ]

    STATE_CHOICES = [
        ('new', '新学'),
        ('learning', '学习中'),
        ('review', '复习'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cards')
    deck = models.ForeignKey(Deck, on_delete=models.CASCADE, related_name='cards')

    # 通用字段
    word = models.CharField(max_length=200, verbose_name='单词/汉字')
    card_type = models.CharField(max_length=2, choices=CARD_TYPE_CHOICES, verbose_name='卡片类型')
    state = models.CharField(max_length=10, choices=STATE_CHOICES, default='new', verbose_name='状态')

    # SM-2 算法字段
    ef = models.FloatField(default=2.5, verbose_name='易忘因子')  # Easiness Factor
    interval = models.IntegerField(default=0, verbose_name='间隔天数')
    difficulty = models.FloatField(default=0, verbose_name='难度')
    stability = models.FloatField(default=0, verbose_name='稳定度')
    lapses = models.IntegerField(default=0, verbose_name='错误次数')
    due_at = models.DateTimeField(default=timezone.now, verbose_name='下次复习时间')

    # 学习阶段字段
    learning_step = models.IntegerField(default=0, verbose_name='学习步骤')

    # 语言特定字段 (JSON)
    # 英语: {ipa, pos, meaning_en, meaning_zh, examples, frequency, cefr}
    # 汉字: {pinyin, radical, strokes, simplified, traditional, frequency, meaning_zh, examples}
    metadata = models.JSONField(default=dict, verbose_name='元数据')

    # 用户自定义
    tags = models.JSONField(default=list, verbose_name='标签')
    notes = models.TextField(blank=True, verbose_name='备注')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '卡片'
        verbose_name_plural = '卡片'
        ordering = ['due_at']
        indexes = [
            models.Index(fields=['user', 'due_at']),
            models.Index(fields=['user', 'deck']),
            models.Index(fields=['word']),
            models.Index(fields=['user', 'state', 'due_at']),
            models.Index(fields=['-lapses']),  # 难项排序
        ]

    def __str__(self):
        return f"{self.word} ({self.get_card_type_display()})"


class ReviewLog(models.Model):
    """复习记录模型"""

    QUALITY_CHOICES = [
        (0, 'Again'),
        (2, 'Hard'),
        (4, 'Good'),
        (5, 'Easy'),
    ]

    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name='review_logs')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='review_logs')

    # 复习数据
    quality = models.IntegerField(choices=QUALITY_CHOICES, verbose_name='评分')
    time_taken = models.IntegerField(verbose_name='耗时(毫秒)')  # milliseconds

    # 复习前的卡片状态（用于撤销）
    before_state = models.CharField(max_length=10, verbose_name='复习前状态')
    before_ef = models.FloatField(verbose_name='复习前EF')
    before_interval = models.IntegerField(verbose_name='复习前间隔')
    before_due_at = models.DateTimeField(verbose_name='复习前到期时间')

    # 复习后的卡片状态
    after_state = models.CharField(max_length=10, verbose_name='复习后状态')
    after_ef = models.FloatField(verbose_name='复习后EF')
    after_interval = models.IntegerField(verbose_name='复习后间隔')
    after_due_at = models.DateTimeField(verbose_name='复习后到期时间')

    reviewed_at = models.DateTimeField(auto_now_add=True, verbose_name='复习时间')

    class Meta:
        verbose_name = '复习记录'
        verbose_name_plural = '复习记录'
        ordering = ['-reviewed_at']
        indexes = [
            models.Index(fields=['user', '-reviewed_at']),
            models.Index(fields=['card', '-reviewed_at']),
        ]

    def __str__(self):
        return f"{self.card.word} - {self.get_quality_display()} - {self.reviewed_at.strftime('%Y-%m-%d %H:%M')}"


class ECDict(models.Model):
    """ECDICT 英语字典模型 (只读数据)"""

    word = models.CharField(max_length=200, unique=True, db_index=True, verbose_name='单词')
    phonetic = models.CharField(max_length=200, blank=True, verbose_name='音标')
    definition = models.TextField(blank=True, verbose_name='释义')
    translation = models.TextField(blank=True, verbose_name='中文翻译')
    pos = models.CharField(max_length=200, blank=True, verbose_name='词性')  # part of speech
    collins = models.IntegerField(default=0, verbose_name='柯林斯星级')  # 1-5
    oxford = models.BooleanField(default=False, verbose_name='牛津3000')
    tag = models.CharField(max_length=200, blank=True, verbose_name='标签')  # zk/gk/cet4/cet6/ielts/toefl/gre
    bnc = models.IntegerField(null=True, blank=True, verbose_name='BNC词频')  # British National Corpus
    frq = models.IntegerField(null=True, blank=True, verbose_name='当代语料库词频')  # Contemporary Corpus
    exchange = models.TextField(blank=True, verbose_name='词形变化')  # 时态/复数/比较级等
    detail = models.TextField(blank=True, verbose_name='详细释义')
    audio = models.CharField(max_length=200, blank=True, verbose_name='读音音频URL')

    class Meta:
        verbose_name = 'ECDICT词典'
        verbose_name_plural = 'ECDICT词典'
        db_table = 'ecdict'  # 单独的表名
        ordering = ['word']
        indexes = [
            models.Index(fields=['word']),
            models.Index(fields=['collins']),
            models.Index(fields=['oxford']),
        ]

    def __str__(self):
        return self.word

