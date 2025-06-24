def nav_links(request):
    return {
        'nav_links': [
            {'url': '#about', 'name': 'О нас'},
            {'url': '#services', 'name': 'Услуги'},
            {'url': '#masters', 'name': 'Мастера'},
            {'url': '#booking', 'name': 'Запись'},
        ],
        'staff_links': [
            {'url': '/orders/', 'name': 'Записи'},
        ]
    }