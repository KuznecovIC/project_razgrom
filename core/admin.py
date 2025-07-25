from .models import Master 
from django.contrib import admin
from django.utils.html import format_html
from .models import Service, Order, Review
from django.utils.translation import gettext_lazy as _

@admin.register(Master)
class MasterAdmin(admin.ModelAdmin):
    list_display = ('name', 'photo_preview', 'experience', 'is_active')
    list_filter = ('is_active', 'services')
    search_fields = ('name', 'phone')
    readonly_fields = ('photo_preview',)
    filter_horizontal = ('services',)  # Это правильно, если в Master есть services как M2M
    
    fieldsets = (
        (None, {
            'fields': ('name', 'photo', 'photo_preview', 'experience', 'description')
        }),
        (_('Контакты'), {
            'fields': ('phone', 'email', 'instagram')
        }),
        (_('Настройки'), {
            'fields': ('is_active', 'services')
        }),
    )

    def photo_preview(self, obj):
        if obj.photo:
            return format_html('<img src="{}" style="max-height: 100px;" />', obj.photo.url)
        return _("Нет фото")
    photo_preview.short_description = _('Фото')

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'duration_display', 'is_active', 'is_popular')
    list_filter = ('category', 'is_active', 'is_popular')
    search_fields = ('name', 'description')
    list_editable = ('is_active', 'is_popular')
    readonly_fields = ('created_at', 'updated_at')
    # Убрал filter_horizontal для masters, так как это должно быть в MasterAdmin
    
    fieldsets = (
        (None, {
            'fields': ('name', 'category', 'description', 'price', 'duration')
        }),
        (_('Изображение'), {
            'fields': ('image',)
        }),
        (_('Настройки'), {
            'fields': ('is_active', 'is_popular')
        }),
    )

    def duration_display(self, obj):
        hours = obj.duration // 60
        minutes = obj.duration % 60
        if hours > 0:
            return f"{hours}ч {minutes}мин"
        return f"{minutes}мин"
    duration_display.short_description = _('Длительность')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'client_name', 'phone', 'master', 'created_at', 'status', 'total_price_display')
    list_filter = ('status', 'master', 'created_at')
    search_fields = ('client_name', 'phone', 'email')
    filter_horizontal = ('services',)  # Это правильно, если Order.services - M2M
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'user')
    
    fieldsets = (
        (_('Информация о клиенте'), {
            'fields': ('client_name', 'phone', 'email', 'comment')
        }),
        (_('Детали заказа'), {
            'fields': ('master', 'services', 'date', 'time', 'status', 'created_at')
        }),
        (_('Системная информация'), {
            'fields': ('user',)
        }),
    )

    def total_price_display(self, obj):
        return f"{obj.total_price()} ₽"
    total_price_display.short_description = _('Общая сумма')

    def save_model(self, request, obj, form, change):
        if not obj.user_id:
            obj.user = request.user
        super().save_model(request, obj, form, change)

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'master', 'client_name', 'rating_stars', 'is_published', 'created_at','ai_status_badge')
    list_filter = ('rating', 'is_published', 'master')
    search_fields = ('client_name', 'text')
    readonly_fields = ('created_at', 'photo_preview')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (None, {
            'fields': ('master', 'client_name', 'text', 'rating', 'user')
        }),
        (_('Медиа'), {
            'fields': ('photo', 'photo_preview')
        }),
        (_('Публикация'), {
            'fields': ('is_published', 'created_at')
        }),
    )

    def rating_stars(self, obj):
        return format_html(
            '<span style="color: gold;">{}</span>',
            '★' * obj.rating + '☆' * (5 - obj.rating)
        )
    rating_stars.short_description = _('Рейтинг')
    rating_stars.admin_order_field = 'rating'

    def photo_preview(self, obj):
        if obj.photo:
            return format_html('<img src="{}" style="max-height: 200px;" />', obj.photo.url)
        return _("Нет фото")
    photo_preview.short_description = _('Превью фото')