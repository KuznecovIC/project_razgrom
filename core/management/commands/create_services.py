# core/management/commands/create_services.py
from django.core.management.base import BaseCommand
from core.models import Service

class Command(BaseCommand):
    help = 'Creates initial barbershop services in database'

    def handle(self, *args, **options):
        services_data = [
            {
                'name': 'Мужская стрижка',
                'description': 'Профессиональная стрижка с учетом особенностей волос и формы лица',
                'price': 1500,
                'duration': 60,
                'is_popular': True
            },
            {
                'name': 'Детская стрижка',
                'description': 'Стрижка для мальчиков с игровым подходом',
                'price': 1200,
                'duration': 45,
                'is_popular': True
            },
            {
                'name': 'Бритье головы',
                'description': 'Полное бритье головы с профессиональной подготовкой',
                'price': 1800,
                'duration': 45,
                'is_popular': False
            },
            {
                'name': 'Королевское бритье',
                'description': 'Традиционное бритье опасной бритвой с горячим полотенцем',
                'price': 2500,
                'duration': 60,
                'is_popular': True
            },
            {
                'name': 'Стрижка бороды',
                'description': 'Коррекция формы бороды и усов',
                'price': 1000,
                'duration': 30,
                'is_popular': True
            },
            {
                'name': 'Комплекс "Барбер"',
                'description': 'Стрижка + оформление бороды + королевское бритье',
                'price': 3500,
                'duration': 90,
                'is_popular': True
            },
            {
                'name': 'Камуфляж седины',
                'description': 'Естественное затемнение седины без полного окрашивания',
                'price': 2000,
                'duration': 45,
                'is_popular': False
            },
            {
                'name': 'Уход за бородой',
                'description': 'Очищение, питание и укладка бороды',
                'price': 1500,
                'duration': 30,
                'is_popular': False
            }
        ]

        created_count = 0
        existing_count = 0

        for service_data in services_data:
            _, created = Service.objects.get_or_create(
                name=service_data['name'],
                defaults={
                    'description': service_data['description'],
                    'price': service_data['price'],
                    'duration': service_data['duration'],
                    'is_popular': service_data['is_popular']
                }
            )
            if created:
                created_count += 1
                self.stdout.write(f'Создана услуга: {service_data["name"]}')
            else:
                existing_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'\nУспешно завершено!\n'
                f'Создано новых услуг: {created_count}\n'
                f'Уже существовало: {existing_count}\n'
                f'Всего услуг в базе: {Service.objects.count()}'
            )
        )