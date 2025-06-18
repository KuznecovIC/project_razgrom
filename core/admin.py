from django.contrib import admin
from .models import Master

@admin.register(Master)
class MasterAdmin(admin.ModelAdmin):
    list_display = ('name', 'photo_preview')
    readonly_fields = ('photo_preview',)

    def photo_preview(self, obj):
        return obj.photo and f'<img src="{obj.photo.url}" style="max-height: 100px;" />'
    photo_preview.allow_tags = True
