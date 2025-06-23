# Барбершоп "Острый угол"

Проект для управления записями в барбершопе.

## Установка

1. Клонировать репозиторий:
```bash
git clone https://github.com/yourusername/project_razgrom.git
cd project_razgrom
```

2. Создать и активировать виртуальное окружение:
```bash
python -m venv venv
source venv/bin/activate  # Linux/MacOS
venv\Scripts\activate     # Windows
```

3. Установить зависимости:
```bash
pip install -r requirements.txt
```

4. Применить миграции:
```bash
python manage.py migrate
```

5. Создать суперпользователя:
```bash
python manage.py createsuperuser
```

6. Запустить сервер:
```bash
python manage.py runserver
```

## Использование

- Админка: http://localhost:8000/admin
- Главная страница: http://localhost:8000

## Shell Plus

Для работы с данными через shell plus:
```bash
python manage.py shell_plus
```

Пример создания тестовых данных:
```python
# Создание услуг
services = [
    Service.objects.create(name="Мужская стрижка", price=1200, duration=60),
    Service.objects.create(name="Детская стрижка", price=800, duration=45),
    Service.objects.create(name="Королевское бритьё", price=900, duration=30, is_popular=True)
]

# Создание мастера
master = Master.objects.create(
    name="Алексей Петров",
    photo="masters/master1.jpg",
    phone="+79161234567",
    experience=5
)
master.services.set(services[:2])

# Создание отзыва
Review.objects.create(
    master=master,
    client_name="Иван Иванов",
    text="Отличная стрижка!",
    rating=5
)
```

![Shell Plus Screenshot](shell_plus_screenshot.png)