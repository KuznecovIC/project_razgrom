from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    phone = models.CharField(
        max_length=20, 
        blank=True,
        verbose_name=_("Телефон")
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        verbose_name=_("Аватар")
    )
    
    class Meta:
        verbose_name = _('Пользователь')
        verbose_name_plural = _('Пользователи')
        ordering = ['username']