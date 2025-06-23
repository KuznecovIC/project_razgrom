from django.contrib import admin
from .models import Master, Service, Order, Review
from django.utils.html import format_html

@admin.register(Master)
class MasterAdmin(admin.ModelAdmin):
    list_display = ('name', 'photo_preview', 'experience', 'is_active')
    list_filter = ('is_active', 'services')
    search_fields = ('name', 'phone')
    readonly_fields = ('photo_preview',)
    filter_horizontal = ('services',)

    def photo_preview(self, obj):
        return format_html(
            '<img src="{}" style="max-height: 100px;" />',
            obj.photo.url if obj.photo else ''
        )
    photo_preview.short_description = 'Фото'

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'duration', 'is_popular')
    list_filter = ('is_popular',)
    search_fields = ('name',)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'client_name', 'master', 'date', 'status', 'total_price')
    list_filter = ('status', 'master', 'date')
    search_fields = ('client_name', 'phone')
    filter_horizontal = ('services',)
    date_hierarchy = 'date'

    def total_price(self, obj):
        return obj.total_price()
    total_price.short_description = 'Сумма'

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'master', 'client_name', 'rating', 'is_published', 'created_at')
    list_filter = ('rating', 'is_published', 'master')
    search_fields = ('client_name', 'text')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'