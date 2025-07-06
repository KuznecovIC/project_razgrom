from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def status_color(value):
    """Возвращает цвет Bootstrap в зависимости от статуса"""
    colors = {
        'new': 'primary',
        'confirmed': 'success',
        'completed': 'secondary',
        'cancelled': 'danger',
    }
    return colors.get(value, 'dark')

@register.filter
def subtract(value, arg):
    """Вычитает arg из value"""
    try:
        return int(value) - int(arg)
    except (ValueError, TypeError):
        return 0

@register.filter(name='stars')
def stars(value):
    """Генерирует HTML для отображения звезд рейтинга"""
    full_stars = range(value)
    empty_stars = range(5 - value)
    html = ''.join(['<i class="bi bi-star-fill text-warning"></i>' for _ in full_stars])
    html += ''.join(['<i class="bi bi-star text-warning"></i>' for _ in empty_stars])
    return mark_safe(html)