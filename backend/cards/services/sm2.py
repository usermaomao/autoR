"""
SM-2 间隔重复算法实现
基于 SuperMemo 2 算法
"""
from datetime import timedelta
from django.utils import timezone
from typing import Tuple


# 学习小步（分钟）
LEARNING_STEPS = [10, 1440]  # 10分钟, 1天


def calculate_ef(current_ef: float, quality: int) -> float:
    """
    计算新的易忘因子 (Easiness Factor)

    Args:
        current_ef: 当前易忘因子 (默认2.5)
        quality: 评分 (0=Again, 2=Hard, 4=Good, 5=Easy)

    Returns:
        新的易忘因子 (最小值1.3)
    """
    # SM-2 公式: EF' = EF + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
    new_ef = current_ef + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))

    # 易忘因子最小值为1.3
    return max(1.3, new_ef)


def calculate_interval(current_interval: int, ef: float, quality: int) -> int:
    """
    计算新的复习间隔（天数）

    Args:
        current_interval: 当前间隔天数
        ef: 易忘因子
        quality: 评分

    Returns:
        新的间隔天数
    """
    # 如果评分低于3 (Again/Hard)，重置到学习阶段
    if quality < 3:
        return 0

    # SM-2 间隔计算
    if current_interval == 0:
        return 1  # 第一次复习: 1天
    elif current_interval == 1:
        return 6  # 第二次复习: 6天
    else:
        # 后续复习: interval * EF
        return int(current_interval * ef)


def get_next_learning_step(card, quality: int) -> Tuple[timedelta, str]:
    """
    获取学习阶段的下一个小步

    Args:
        card: Card 对象
        quality: 评分

    Returns:
        (时间增量, 新状态)
    """
    if quality == 0:  # Again - 重新开始
        card.learning_step = 0
        return timedelta(minutes=LEARNING_STEPS[0]), 'learning'

    # 进入下一个学习小步
    card.learning_step += 1

    if card.learning_step >= len(LEARNING_STEPS):
        # 完成学习阶段，进入复习阶段
        interval = calculate_interval(0, card.ef, quality)
        return timedelta(days=interval), 'review'

    # 继续学习阶段
    return timedelta(minutes=LEARNING_STEPS[card.learning_step]), 'learning'


def generate_review_queue(user, limit: int = 50):
    """生成复习队列

    优先级: 到期卡片 > 难项 > 新卡

    Args:
        user: User 对象
        limit: 队列大小限制

    Returns:
        dict: {
            'cards': Card 对象列表,
            'stats': {
                'due_count': 到期卡片数,
                'leech_count': 难项卡片数,
                'new_count': 新卡片数,
                'total_new': 总新卡数,
                'session_limit': 本次会话最大卡片数,
                'returned_count': 实际返回卡片数,
                'message': 提示信息
            }
        }
    """
    from cards.models import Card, Deck

    now = timezone.now()

    # 1. 到期的复习卡片（按到期时间和错误次数排序）
    due_cards = Card.objects.filter(
        user=user,
        state__in=['learning', 'review'],
        due_at__lte=now,
    ).order_by('due_at', '-lapses')[:limit]

    due_card_ids = list(due_cards.values_list('id', flat=True))
    due_count = len(due_card_ids)

    # 2. 难项优先（lapses >= 3）
    leech_cards = Card.objects.filter(
        user=user,
        lapses__gte=3,
    ).exclude(id__in=due_card_ids).order_by('-lapses')[:10]

    leech_card_ids = list(leech_cards.values_list('id', flat=True))
    leech_count = len(leech_card_ids)

    # 3. 新卡（根据配置的每日新卡限制）
    try:
        default_deck = Deck.objects.filter(user=user).first()
        daily_new_limit = default_deck.daily_new_limit if default_deck else 20
    except Exception:
        daily_new_limit = 20

    # 统计总新卡数
    total_new_cards = Card.objects.filter(user=user, state='new').count()

    new_cards = (
        Card.objects.filter(user=user, state='new')
        .exclude(id__in=due_card_ids + leech_card_ids)
        .order_by('created_at')[:daily_new_limit]
    )

    new_count = new_cards.count()

    # 合并所有卡片（保持优先级顺序）
    all_card_ids = (
        list(due_cards.values_list('id', flat=True))
        + list(leech_cards.values_list('id', flat=True))
        + list(new_cards.values_list('id', flat=True))
    )

    # 使用 in_bulk 保持顺序
    cards = Card.objects.filter(id__in=all_card_ids).select_related('deck', 'user')

    # 按原始顺序排序
    card_dict = {card.id: card for card in cards}
    ordered_cards = [card_dict[card_id] for card_id in all_card_ids if card_id in card_dict]

    # 最终返回的卡片列表（再次受 limit 约束）
    final_cards = ordered_cards[:limit]

    # 生成提示信息
    message = ''
    if not final_cards:
        if total_new_cards == 0:
            message = '恭喜!你已经完成了所有复习,且没有新卡片需要学习。'
        else:
            message = f'今日复习已完成!还有 {total_new_cards} 张新卡片待学习。'
    else:
        parts = []
        if due_count > 0:
            parts.append(f'{due_count} 张到期')
        if leech_count > 0:
            parts.append(f'{leech_count} 张难项')
        if new_count > 0:
            parts.append(f'{new_count} 张新卡')
        message = f'本次复习: {", ".join(parts)}'

    return {
        'cards': final_cards,
        'stats': {
            'due_count': due_count,
            'leech_count': leech_count,
            'new_count': new_count,
            'total_new': total_new_cards,
            'session_limit': limit,
            'returned_count': len(final_cards),
            'message': message,
        },
    }


def get_lowest_mastery_cards(user, limit: int = 10):
    """
    获取掌握度最低的卡片（用于无待复习卡片时的练习）

    掌握度评估标准：
    1. 优先选择错误次数多的卡片（lapses）
    2. 其次选择易忘因子低的卡片（ef 值低）
    3. 排除完全未学习的新卡（state='new'）

    Args:
        user: User 对象
        limit: 返回卡片数量限制

    Returns:
        Card 对象列表
    """
    from cards.models import Card

    # 查询已学习过的卡片（排除 state='new'）
    # 按错误次数降序、易忘因子升序排序
    cards = Card.objects.filter(
        user=user,
        state__in=['learning', 'review']  # 只包括已学习的卡片
    ).order_by(
        '-lapses',  # 错误次数多的排前面
        'ef',       # 易忘因子低的排前面
        '-interval' # 间隔短的排前面（说明掌握不牢固）
    ).select_related('deck', 'user')[:limit]

    return list(cards)


def mark_leech(card) -> bool:
    """
    标记难项卡片

    Args:
        card: Card 对象

    Returns:
        是否为难项
    """
    if card.lapses >= 3:
        if 'leech' not in card.tags:
            card.tags.append('leech')
            card.save(update_fields=['tags'])
        return True
    return False


def process_review(card, quality: int, time_taken: int):
    """
    处理复习评分，更新卡片状态

    Args:
        card: Card 对象
        quality: 评分 (0=Again, 2=Hard, 4=Good, 5=Easy)
        time_taken: 耗时（毫秒）

    Returns:
        ReviewLog 对象
    """
    from cards.models import ReviewLog

    # 保存复习前的状态（用于撤销）
    before_state = card.state
    before_ef = card.ef
    before_interval = card.interval
    before_due_at = card.due_at

    # 根据当前状态处理
    if card.state == 'new':
        # 新卡进入学习阶段
        card.state = 'learning'
        card.learning_step = 0
        delta, new_state = get_next_learning_step(card, quality)
        card.due_at = timezone.now() + delta
        card.state = new_state

        if new_state == 'review':
            card.interval = calculate_interval(0, card.ef, quality)

    elif card.state == 'learning':
        # 学习阶段
        delta, new_state = get_next_learning_step(card, quality)
        card.due_at = timezone.now() + delta
        card.state = new_state

        if new_state == 'review':
            # 从学习阶段毕业,interval 从 0 开始计算
            card.interval = calculate_interval(0, card.ef, quality)

    elif card.state == 'review':
        # 复习阶段
        if quality < 3:
            # Again/Hard: 回到学习阶段
            card.state = 'learning'
            card.learning_step = 0
            card.lapses += 1
            delta = timedelta(minutes=LEARNING_STEPS[0])
            card.due_at = timezone.now() + delta
        else:
            # Good/Easy: 继续复习
            card.ef = calculate_ef(card.ef, quality)
            card.interval = calculate_interval(card.interval, card.ef, quality)
            card.due_at = timezone.now() + timedelta(days=card.interval)

    # 标记难项
    mark_leech(card)

    # 保存卡片
    card.save()

    # 创建复习记录
    review_log = ReviewLog.objects.create(
        card=card,
        user=card.user,
        quality=quality,
        time_taken=time_taken,
        before_state=before_state,
        before_ef=before_ef,
        before_interval=before_interval,
        before_due_at=before_due_at,
        after_state=card.state,
        after_ef=card.ef,
        after_interval=card.interval,
        after_due_at=card.due_at
    )

    return review_log


def undo_review(review_log):
    """
    撤销上一次复习

    Args:
        review_log: ReviewLog 对象
    """
    card = review_log.card

    # 恢复卡片状态
    card.state = review_log.before_state
    card.ef = review_log.before_ef
    card.interval = review_log.before_interval
    card.due_at = review_log.before_due_at

    # 如果是从复习阶段失败(quality < 3)撤销，需要减少 lapses
    # 因为在 process_review 中,复习阶段 quality < 3 会增加 lapses
    if review_log.before_state == 'review' and review_log.quality < 3 and card.lapses > 0:
        card.lapses -= 1

    card.save()

    # 删除复习记录
    review_log.delete()
