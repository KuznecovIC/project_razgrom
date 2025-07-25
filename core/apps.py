# core/apps.py
from django.apps import AppConfig

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'Барбершоп'

    def ready(self):
        # Импорт только после полной загрузки приложения
        import core.signals
        from core.telegram_bot import test_send
        test_send()