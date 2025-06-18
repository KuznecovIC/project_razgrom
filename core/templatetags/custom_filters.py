from django import template

register = template.Library()

@register.filter
def status_color(value):
    colors = {
        'new': 'primary',
        'confirmed': 'success',
        'completed': 'secondary',
        'cancelled': 'danger',
    }
    return colors.get(value, 'dark')
