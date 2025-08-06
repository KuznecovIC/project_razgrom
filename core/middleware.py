from .models import Service, Master
from django.db.utils import OperationalError
import logging

logger = logging.getLogger(__name__)

class InitDataMiddleware:
    """
    Промежуточное ПО (Middleware) для инициализации начальных данных.

    Этот класс предназначен для автоматического создания базовых данных (услуг
    и мастеров) при первом запуске приложения, если они отсутствуют в базе
    данных. Это позволяет избежать ошибок, связанных с пустыми таблицами,
    особенно при первом развертывании проекта.

    Атрибуты:
        get_response (callable): Следующее промежуточное ПО или представление
                                 в цепочке обработки запроса.

    Методы:
        __init__(self, get_response): Конструктор класса.
        __call__(self, request): Метод, вызываемый при каждом HTTP-запросе.
    """
    def __init__(self, get_response):
        """
        Инициализирует Middleware.

        Args:
            get_response (callable): Следующее промежуточное ПО или
                                     представление.
        """
        self.get_response = get_response
        self.initialized = False

    def __call__(self, request):
        """
        Обрабатывает HTTP-запрос.

        Выполняет проверку и создание начальных данных только один раз за
        жизненный цикл сервера.
        
        Args:
            request (HttpRequest): Объект HTTP-запроса.

        Returns:
            HttpResponse: Объект HTTP-ответа от следующего звена в цепочке.
        """
        # Проверяем и создаем данные при первом запросе
        if not self.initialized:
            try:
                if not Service.objects.exists():
                    logger.info("Создание начальных услуг...")
                    Service.objects.bulk_create([
                        Service(name="Мужская стрижка", price=1200, is_popular=True),
                        # ... остальные услуги
                    ])
                    logger.info("Начальные услуги успешно созданы.")
                
                if not Master.objects.exists():
                    logger.info("Создание начальных мастеров...")
                    Master.objects.bulk_create([
                        # ... ваши мастера
                    ])
                    logger.info("Начальные мастера успешно созданы.")
                
                self.initialized = True
            except OperationalError as e:
                # Это может произойти, если база данных еще не готова (миграции не применены).
                # Игнорируем ошибку и позволяем приложению продолжить,
                # чтобы Django мог выполнить миграции.
                logger.warning(f"Ошибка базы данных при инициализации данных: {e}")
            except Exception as e:
                logger.error(f"Непредвиденная ошибка при инициализации данных: {e}")
        
        return self.get_response(request)