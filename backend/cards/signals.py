"""
Django信号处理器
用于在用户注册时自动创建默认卡组
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Deck


@receiver(post_save, sender=User)
def create_default_deck(sender, instance, created, **kwargs):
    """
    用户创建时自动创建默认卡组

    Args:
        sender: 发送信号的模型类(User)
        instance: 刚创建的用户实例
        created: 是否是新创建的(True)还是更新(False)
        **kwargs: 其他参数
    """
    if created:
        # 只在用户首次创建时执行
        Deck.objects.create(
            user=instance,
            name='默认卡组',
            description='系统自动创建的默认卡组，您可以随时修改或删除',
            daily_new_limit=20,
            daily_review_limit=200
        )
