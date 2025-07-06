# core/middleware.py
from .models import Service, Master

class InitDataMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Проверяем и создаем данные при первом запросе
        if not Service.objects.exists():
            Service.objects.bulk_create([
                Service(name="Мужская стрижка", price=1200, is_popular=True),
                # ... остальные услуги
            ])
        
        if not Master.objects.exists():
            Master.objects.bulk_create([
                # ... ваши мастера
            ])
        
        return self.get_response(request)