"""
SM-2 算法测试
"""
import pytest
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.models import User
from cards.models import Deck, Card, ReviewLog
from cards.services.sm2 import (
    calculate_ef,
    calculate_interval,
    get_next_learning_step,
    generate_review_queue,
    mark_leech,
    process_review,
    undo_review
)


@pytest.fixture
def user(db):
    """创建测试用户"""
    return User.objects.create_user(
        username='testuser',
        password='testpass123'
    )


@pytest.fixture
def deck(user):
    """创建测试卡组"""
    return Deck.objects.create(
        user=user,
        name='Test Deck',
        daily_new_limit=20
    )


@pytest.fixture
def card(user, deck):
    """创建测试卡片"""
    return Card.objects.create(
        user=user,
        deck=deck,
        word='test',
        card_type='en',
        state='new',
        ef=2.5,
        interval=0,
        due_at=timezone.now()
    )


class TestCalculateEF:
    """测试易忘因子计算"""

    def test_ef_increases_on_easy(self):
        """测试 Easy (5) 会增加 EF"""
        ef = calculate_ef(2.5, 5)
        assert ef == 2.6

    def test_ef_decreases_on_again(self):
        """测试 Again (0) 会减少 EF"""
        ef = calculate_ef(2.5, 0)
        assert ef < 2.5

    def test_ef_minimum_is_1_3(self):
        """测试 EF 最小值为 1.3"""
        ef = calculate_ef(1.3, 0)
        assert ef >= 1.3

    def test_ef_hard_slightly_decreases(self):
        """测试 Hard (2) 会略微减少 EF"""
        ef = calculate_ef(2.5, 2)
        assert ef < 2.5  # Hard 应该减少 EF
        assert ef >= 1.3  # 但不低于最小值


class TestCalculateInterval:
    """测试间隔计算"""

    def test_again_resets_interval(self):
        """测试 Again (0) 重置间隔"""
        interval = calculate_interval(10, 2.5, 0)
        assert interval == 0

    def test_hard_resets_interval(self):
        """测试 Hard (2) 重置间隔"""
        interval = calculate_interval(10, 2.5, 2)
        assert interval == 0

    def test_first_good_is_1_day(self):
        """测试首次 Good 间隔为 1 天"""
        interval = calculate_interval(0, 2.5, 4)
        assert interval == 1

    def test_second_good_is_6_days(self):
        """测试第二次 Good 间隔为 6 天"""
        interval = calculate_interval(1, 2.5, 4)
        assert interval == 6

    def test_interval_multiplies_by_ef(self):
        """测试间隔按 EF 倍增"""
        interval = calculate_interval(6, 2.5, 4)
        assert interval == int(6 * 2.5)  # 15


class TestQueueGeneration:
    """测试队列生成"""

    def test_generates_queue_for_user(self, user, deck):
        """测试为用户生成复习队列，并返回统计信息"""
        # 创建一些卡片
        for i in range(5):
            Card.objects.create(
                user=user,
                deck=deck,
                word=f'word{i}',
                card_type='en',
                state='new',
            )

        result = generate_review_queue(user, limit=10)

        # 基本结构
        assert 'cards' in result
        assert 'stats' in result

        cards = result['cards']
        stats = result['stats']

        assert len(cards) <= 10
        assert all(c.user == user for c in cards)

        # 新增的 session 统计字段
        assert stats['session_limit'] == 10
        assert stats['returned_count'] == len(cards)

    def test_prioritizes_due_cards(self, user, deck):
        """测试优先返回到期卡片"""
        # 创建到期卡片
        due_card = Card.objects.create(
            user=user,
            deck=deck,
            word='due',
            card_type='en',
            state='review',
            due_at=timezone.now() - timedelta(days=1),
        )

        # 创建新卡
        Card.objects.create(
            user=user,
            deck=deck,
            word='new',
            card_type='en',
            state='new',
        )

        result = generate_review_queue(user, limit=10)
        cards = result['cards']

        assert cards  # 至少有一张卡片
        assert cards[0].id == due_card.id  # 到期卡片在前


class TestMarkLeech:
    """测试难项标记"""

    def test_marks_leech_when_lapses_ge_3(self, card):
        """测试错误次数 >= 3 时标记为难项"""
        card.lapses = 3
        card.save()

        result = mark_leech(card)
        assert result is True
        card.refresh_from_db()
        assert 'leech' in card.tags

    def test_does_not_mark_when_lapses_lt_3(self, card):
        """测试错误次数 < 3 时不标记"""
        card.lapses = 2
        card.save()

        result = mark_leech(card)
        assert result is False


class TestProcessReview:
    """测试复习处理"""

    def test_new_card_enters_learning(self, card):
        """测试新卡进入学习阶段"""
        review_log = process_review(card, quality=4, time_taken=5000)

        card.refresh_from_db()
        assert card.state in ['learning', 'review']
        assert review_log.quality == 4

    def test_again_increases_lapses(self, card):
        """测试 Again 增加错误次数"""
        card.state = 'review'
        card.save()

        initial_lapses = card.lapses
        process_review(card, quality=0, time_taken=5000)

        card.refresh_from_db()
        assert card.lapses == initial_lapses + 1

    def test_creates_review_log(self, card):
        """测试创建复习记录"""
        review_log = process_review(card, quality=4, time_taken=5000)

        assert review_log.card == card
        assert review_log.user == card.user
        assert review_log.quality == 4
        assert review_log.time_taken == 5000


class TestUndoReview:
    """测试撤销复习"""

    def test_undo_restores_card_state(self, card):
        """测试撤销恢复卡片状态"""
        # 记录原始状态
        original_state = card.state
        original_ef = card.ef
        original_interval = card.interval

        # 执行复习
        review_log = process_review(card, quality=4, time_taken=5000)

        # 撤销复习
        undo_review(review_log)

        # 验证状态恢复
        card.refresh_from_db()
        assert card.state == original_state
        assert card.ef == original_ef
        assert card.interval == original_interval

    def test_undo_deletes_review_log(self, card):
        """测试撤销删除复习记录"""
        review_log = process_review(card, quality=4, time_taken=5000)
        log_id = review_log.id

        undo_review(review_log)

        assert not ReviewLog.objects.filter(id=log_id).exists()
