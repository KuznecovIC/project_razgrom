import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'barbershop.settings')
django.setup()

from core.models import Master, Service, Order, Review
from django.contrib.auth.models import User
from datetime import datetime, timedelta

def create_test_data():
    # Создаем суперпользователя (с проверкой существования)
    if not User.objects.filter(username='admin2').exists():
        User.objects.create_superuser('admin2', 'admin@example.com', 'admin123')
    else:
        print("Суперпользователь 'admin' уже существует")
    
    # Создаем услуги
    services = [
        Service.objects.create(name="Мужская стрижка", price=1200, duration=60),
        Service.objects.create(name="Детская стрижка", price=800, duration=45, is_popular=True),
        Service.objects.create(name="Королевское бритьё", price=900, duration=30),
        Service.objects.create(name="Оформление бороды", price=600, duration=30, is_popular=True),
        Service.objects.create(name="Комплекс (стрижка+борода)", price=1500, duration=90)
    ]
    
    # Создаем мастеров
    masters = [
        Master.objects.create(
            name="Алексей 'Бритва' Петров",
            photo="masters/master1.jpg",
            phone="+79161234567",
            experience=8,
            is_active=True
        ),
        Master.objects.create(
            name="Дмитрий 'Стиль' Иванов",
            photo="masters/master2.jpg",
            phone="+79167654321",
            experience=5,
            is_active=True
        ),
        Master.objects.create(
            name="Сергей 'Точность' Смирнов",
            photo="masters/master3.jpg",
            phone="+79165557777",
            experience=6,
            is_active=True
        )
    ]
    
    # Назначаем услуги мастерам
    masters[0].services.set(services[:3])
    masters[1].services.set(services[2:])
    masters[2].services.set(services[1:4])
    
    # Создаем записи
    orders = []
    for i in range(5):
        order = Order.objects.create(
            client_name=f"Клиент {i+1}",
            phone=f"+7916000000{i}",
            date=datetime.now() + timedelta(days=i+1),
            master=masters[i % len(masters)],
            status='new' if i < 2 else 'confirmed'
        )
        order.services.set(services[i % len(services):(i % len(services))+2])
        orders.append(order)
    
    # Создаем отзывы
    reviews = []
    for i, master in enumerate(masters):
        for j in range(3):
            review = Review.objects.create(
                master=master,
                client_name=f"Посетитель {i*3 + j + 1}",
                text=f"Отличный мастер! {['', 'Очень доволен!', 'Супер!'][j]}",
                rating=5-j,
                is_published=True
            )
            reviews.append(review)
    
    print("Тестовые данные успешно созданы!")

if __name__ == '__main__':
    create_test_data()