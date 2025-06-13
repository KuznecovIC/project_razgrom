from django.shortcuts import render

masters = [
    {"id": 1, "name": "Эльдар 'Бритва' Рязанов"},
    {"id": 2, "name": "Зоя 'Ножницы' Космодемьянская"},
    {"id": 3, "name": "Борис 'Фен' Пастернак"},
    {"id": 4, "name": "Иннокентий 'Лак' Смоктуновский"},
    {"id": 5, "name": "Раиса 'Бигуди' Горбачёва"},
]

services = [
    "Стрижка под 'Горшок'",
    "Укладка 'Взрыв на макаронной фабрике'",
    "Королевское бритье опасной бритвой",
    "Окрашивание 'Жизнь в розовом цвете'",
    "Мытье головы 'Душ впечатлений'",
    "Стрижка бороды 'Боярин'",
    "Массаж головы 'Озарение'",
    "Укладка 'Ветер в голове'",
    "Плетение косичек 'Викинг'",
    "Полировка лысины до блеска"
]

STATUS_NEW = 'новая'
STATUS_CONFIRMED = 'подтвержденная'
STATUS_CANCELLED = 'отмененная'
STATUS_COMPLETED = 'выполненная'

orders = [
    {
        "id": 1,
        "client_name": "Пётр 'Безголовый' Головин",
        "phone": "+7 (123) 456-7890",
        "services": ["Стрижка под 'Горшок'", "Полировка лысины до блеска"],
        "master_id": 1,
        "date": "2025-03-20",
        "status": STATUS_NEW,
        "total_price": 2500
    },
]
def landing(request):
    context = {
        'masters': masters,
        'services': services
    }
    return render(request, 'landing.html', context)

def thanks(request):
    return render(request, 'core/thanks.html')

def orders_list(request):
    context = {
        'orders': orders
    }
    return render(request, 'core/orders_list.html', context)

def order_detail(request, order_id):
    order = next((order for order in orders if order['id'] == order_id), None)
    master = next((master for master in masters if master['id'] == order['master_id']), None)
    
    context = {
        'order': order,
        'master': master
    }
    return render(request, 'core/order_detail.html', context)
