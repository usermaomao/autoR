from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.utils import timezone

from .models import Deck, Card, ReviewLog


class AuthAPITestCase(APITestCase):
    """认证 API 测试"""

    def test_register(self):
        """测试用户注册"""
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'password_confirm': 'testpass123'
        }
        response = self.client.post('/api/auth/register/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['username'], 'testuser')

    def test_register_password_mismatch(self):
        """测试注册密码不匹配"""
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'password_confirm': 'wrongpass'
        }
        response = self.client.post('/api/auth/register/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login(self):
        """测试用户登录"""
        # 先创建用户
        User.objects.create_user(username='testuser', password='testpass123')

        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        response = self.client.post('/api/auth/login/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('user', response.data)

    def test_login_invalid_credentials(self):
        """测试登录错误凭证"""
        data = {
            'username': 'nonexistent',
            'password': 'wrongpass'
        }
        response = self.client.post('/api/auth/login/', data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class DeckAPITestCase(APITestCase):
    """卡组 API 测试"""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client.force_authenticate(user=self.user)

    def test_create_deck(self):
        """测试创建卡组"""
        data = {
            'name': 'Test Deck',
            'description': 'Test description',
            'daily_new_limit': 20,
            'daily_review_limit': 200
        }
        response = self.client.post('/api/decks/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Test Deck')
        self.assertEqual(Deck.objects.count(), 1)

    def test_list_decks(self):
        """测试获取卡组列表"""
        Deck.objects.create(user=self.user, name='Deck 1')
        Deck.objects.create(user=self.user, name='Deck 2')

        response = self.client.get('/api/decks/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # DRF 返回分页结果
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 2)

    def test_update_deck(self):
        """测试更新卡组"""
        deck = Deck.objects.create(user=self.user, name='Old Name')

        data = {'name': 'New Name'}
        response = self.client.patch(f'/api/decks/{deck.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        deck.refresh_from_db()
        self.assertEqual(deck.name, 'New Name')

    def test_delete_deck(self):
        """测试删除卡组"""
        deck = Deck.objects.create(user=self.user, name='Test Deck')

        response = self.client.delete(f'/api/decks/{deck.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Deck.objects.count(), 0)


class CardAPITestCase(APITestCase):
    """卡片 API 测试"""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client.force_authenticate(user=self.user)
        self.deck = Deck.objects.create(user=self.user, name='Test Deck')

    def test_create_card(self):
        """测试创建卡片"""
        data = {
            'deck': self.deck.id,
            'word': 'hello',
            'card_type': 'en',
            'metadata': {
                'ipa': '/həˈləʊ/',
                'meaning_en': 'a greeting',
                'meaning_zh': '你好'
            }
        }
        response = self.client.post('/api/cards/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['word'], 'hello')
        self.assertEqual(Card.objects.count(), 1)

    def test_list_cards(self):
        """测试获取卡片列表"""
        Card.objects.create(user=self.user, deck=self.deck, word='hello', card_type='en')
        Card.objects.create(user=self.user, deck=self.deck, word='你好', card_type='zh')

        response = self.client.get('/api/cards/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # DRF 返回分页结果
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 2)

    def test_filter_cards_by_type(self):
        """测试按类型过滤卡片"""
        Card.objects.create(user=self.user, deck=self.deck, word='hello', card_type='en')
        Card.objects.create(user=self.user, deck=self.deck, word='你好', card_type='zh')

        response = self.client.get('/api/cards/?card_type=en')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # DRF 返回分页结果
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['card_type'], 'en')

    def test_get_due_cards(self):
        """测试获取到期卡片"""
        # 创建一个到期的卡片
        Card.objects.create(
            user=self.user,
            deck=self.deck,
            word='overdue',
            card_type='en',
            state='review',
            due_at=timezone.now() - timezone.timedelta(days=1)
        )

        # 创建一个未到期的卡片
        Card.objects.create(
            user=self.user,
            deck=self.deck,
            word='future',
            card_type='en',
            state='review',
            due_at=timezone.now() + timezone.timedelta(days=1)
        )

        response = self.client.get('/api/cards/due_today/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['word'], 'overdue')

    def test_get_leech_cards(self):
        """测试获取难项卡片"""
        Card.objects.create(
            user=self.user,
            deck=self.deck,
            word='difficult',
            card_type='en',
            lapses=5
        )
        Card.objects.create(
            user=self.user,
            deck=self.deck,
            word='easy',
            card_type='en',
            lapses=1
        )

        response = self.client.get('/api/cards/leeches/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['word'], 'difficult')


class ModelTestCase(TestCase):
    """模型测试"""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.deck = Deck.objects.create(user=self.user, name='Test Deck')

    def test_deck_str(self):
        """测试 Deck __str__ 方法"""
        self.assertEqual(str(self.deck), 'testuser - Test Deck')

    def test_card_str(self):
        """测试 Card __str__ 方法"""
        card = Card.objects.create(
            user=self.user,
            deck=self.deck,
            word='hello',
            card_type='en'
        )
        self.assertEqual(str(card), 'hello (英语)')

    def test_card_defaults(self):
        """测试 Card 默认值"""
        card = Card.objects.create(
            user=self.user,
            deck=self.deck,
            word='test',
            card_type='en'
        )
        self.assertEqual(card.ef, 2.5)
        self.assertEqual(card.interval, 0)
        self.assertEqual(card.state, 'new')
        self.assertEqual(card.lapses, 0)


class SM2AlgorithmTestCase(TestCase):
    """SM-2 算法测试"""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.deck = Deck.objects.create(user=self.user, name='Test Deck')

    def test_calculate_ef(self):
        """测试 EF 计算"""
        from cards.services.sm2 import calculate_ef

        # 测试 Easy (5)
        ef = calculate_ef(2.5, 5)
        self.assertEqual(ef, 2.6)

        # 测试 Again (0)
        ef = calculate_ef(2.5, 0)
        self.assertGreaterEqual(ef, 1.3)  # 最小值 1.3

        # 测试边界情况
        ef = calculate_ef(1.3, 0)
        self.assertEqual(ef, 1.3)  # 不应小于 1.3

    def test_calculate_interval(self):
        """测试间隔计算"""
        from cards.services.sm2 import calculate_interval

        # 第一次复习
        interval = calculate_interval(0, 2.5, 4)
        self.assertEqual(interval, 1)

        # 第二次复习
        interval = calculate_interval(1, 2.5, 4)
        self.assertEqual(interval, 6)

        # 后续复习
        interval = calculate_interval(6, 2.5, 4)
        self.assertEqual(interval, 15)  # 6 * 2.5 = 15

        # Again - 重置
        interval = calculate_interval(6, 2.5, 0)
        self.assertEqual(interval, 0)

    def test_process_review_new_card(self):
        """测试新卡复习流程"""
        from cards.services.sm2 import process_review

        card = Card.objects.create(
            user=self.user,
            deck=self.deck,
            word='test',
            card_type='en',
            state='new'
        )

        # 第一次复习 Good
        review_log = process_review(card, quality=4, time_taken=5000)

        card.refresh_from_db()
        self.assertIn(card.state, ['learning', 'review'])
        self.assertIsNotNone(review_log)

    def test_process_review_again(self):
        """测试 Again 评分"""
        from cards.services.sm2 import process_review

        card = Card.objects.create(
            user=self.user,
            deck=self.deck,
            word='difficult',
            card_type='en',
            state='review',
            interval=10
        )

        initial_lapses = card.lapses

        # 评分 Again
        process_review(card, quality=0, time_taken=10000)

        card.refresh_from_db()
        self.assertEqual(card.state, 'learning')
        self.assertEqual(card.lapses, initial_lapses + 1)

    def test_mark_leech(self):
        """测试难项标记"""
        from cards.services.sm2 import mark_leech

        card = Card.objects.create(
            user=self.user,
            deck=self.deck,
            word='very_difficult',
            card_type='en',
            lapses=3
        )

        is_leech = mark_leech(card)

        card.refresh_from_db()
        self.assertTrue(is_leech)
        self.assertIn('leech', card.tags)

    def test_generate_review_queue(self):
        """测试复习队列生成"""
        from cards.services.sm2 import generate_review_queue

        # 创建到期卡片
        Card.objects.create(
            user=self.user,
            deck=self.deck,
            word='overdue',
            card_type='en',
            state='review',
            due_at=timezone.now() - timezone.timedelta(days=1)
        )

        # 创建难项
        Card.objects.create(
            user=self.user,
            deck=self.deck,
            word='leech',
            card_type='en',
            lapses=5
        )

        # 创建新卡
        Card.objects.create(
            user=self.user,
            deck=self.deck,
            word='new_card',
            card_type='en',
            state='new'
        )

        queue = generate_review_queue(self.user, limit=20)

        self.assertGreater(len(queue), 0)
        self.assertLessEqual(len(queue), 20)

    def test_undo_review(self):
        """测试撤销复习"""
        from cards.services.sm2 import process_review, undo_review

        card = Card.objects.create(
            user=self.user,
            deck=self.deck,
            word='test',
            card_type='en',
            state='new'
        )

        # 记录初始状态
        initial_state = card.state
        initial_ef = card.ef

        # 进行复习
        review_log = process_review(card, quality=4, time_taken=5000)
        card.refresh_from_db()

        # 撤销复习
        undo_review(review_log)
        card.refresh_from_db()

        # 验证恢复到初始状态
        self.assertEqual(card.state, initial_state)
        self.assertEqual(card.ef, initial_ef)


class ReviewAPITestCase(APITestCase):
    """复习 API 测试"""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client.force_authenticate(user=self.user)
        self.deck = Deck.objects.create(user=self.user, name='Test Deck')

    def test_get_review_queue(self):
        """测试获取复习队列"""
        # 创建一些卡片
        Card.objects.create(
            user=self.user,
            deck=self.deck,
            word='test1',
            card_type='en',
            state='review',
            due_at=timezone.now() - timezone.timedelta(days=1)
        )

        response = self.client.get('/api/review/queue/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('cards', response.data)
        self.assertIn('count', response.data)

    def test_submit_review(self):
        """测试提交复习"""
        card = Card.objects.create(
            user=self.user,
            deck=self.deck,
            word='test',
            card_type='en',
            state='new'
        )

        data = {
            'card_id': card.id,
            'quality': 4,
            'time_taken': 5000
        }

        response = self.client.post('/api/review/submit/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('card', response.data)
        self.assertIn('review_log', response.data)

    def test_undo_review(self):
        """测试撤销复习 API"""
        card = Card.objects.create(
            user=self.user,
            deck=self.deck,
            word='test',
            card_type='en',
            state='new'
        )

        # 先进行一次复习
        self.client.post('/api/review/submit/', {
            'card_id': card.id,
            'quality': 4,
            'time_taken': 5000
        })

        # 撤销复习
        response = self.client.post('/api/review/undo/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('card', response.data)


