from django.apps import AppConfig


class CardsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'cards'

    def ready(self):
        """应用启动时导入信号处理器"""
        import cards.signals
