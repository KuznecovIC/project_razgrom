from django.db import migrations

def create_initial_data(apps, schema_editor):
    Service = apps.get_model('core', 'Service')
    Master = apps.get_model('core', 'Master')
    
    # Создаем услуги
    services = [
        {"name": "Мужская стрижка", "price": 1200, "is_popular": True, "category": "HC", "duration": 60, "is_active": True},
        {"name": "Детская стрижка", "price": 800, "is_popular": False, "category": "HC", "duration": 45, "is_active": True},
        {"name": "Стрижка машинкой", "price": 700, "is_popular": False, "category": "HC", "duration": 30, "is_active": True},
        {"name": "Оформление бороды", "price": 600, "is_popular": True, "category": "BD", "duration": 30, "is_active": True},
        {"name": "Королевское бритьё", "price": 900, "is_popular": False, "category": "BD", "duration": 45, "is_active": True},
        {"name": "Комплекс (стрижка+борода)", "price": 1500, "is_popular": True, "category": "CX", "duration": 90, "is_active": True},
        {"name": "Камуфляж седины", "price": 500, "is_popular": False, "category": "OT", "duration": 20, "is_active": True},
        {"name": "Укладка", "price": 300, "is_popular": False, "category": "OT", "duration": 15, "is_active": True},
    ]
    
    created_services = []
    for service_data in services:
        service = Service.objects.create(**service_data)
        created_services.append(service)
    
    # Создаем мастеров
    masters = [
        {
            "name": "Алексей 'Бритва' Петров",
            "photo": "masters/master1.jpg",
            "phone": "+79160000001",
            "description": "Специалист по классическим и современным стрижкам. Стаж 8 лет.",
            "instagram": "@barber_alex",
            "experience": 8,
            "is_active": True
        },
        {
            "name": "Дмитрий 'Стиль' Иванов",
            "photo": "masters/master2.jpg",
            "phone": "+79160000002",
            "description": "Эксперт по бородам и уходу за ними. Любит сложные формы.",
            "instagram": "@beard_master",
            "experience": 5,
            "is_active": True
        },
        {
            "name": "Сергей 'Точность' Смирнов",
            "photo": "masters/master3.jpg",
            "phone": "+79160000003",
            "description": "Мастер детализации. Идеальные линии и четкие контуры.",
            "instagram": "@sharp_lines",
            "experience": 6,
            "is_active": True
        }
    ]
    
    for master_data in masters:
        master = Master.objects.create(**master_data)
        # Назначаем все услуги мастеру (или можно выбрать определенные)
        master.services.set(created_services)

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),  # Зависит от вашей первой миграции
    ]

    operations = [
        migrations.RunPython(create_initial_data),
    ]