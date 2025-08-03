from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator, FileExtensionValidator
from django.utils import timezone
from django.db import connection
from django.utils.translation import gettext_lazy as _
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from datetime import datetime
from django.utils.html import format_html
from django.utils.safestring import mark_safe
import os
from django.conf import settings
class Service(models.Model):
    """Модель услуги барбершопа с расширенными возможностями"""
    
    class ServiceCategory(models.TextChoices):
        HAIRCUT = 'HC', _('Стрижка')
        BEARD = 'BD', _('Борода')
        COMPLEX = 'CX', _('Комплекс')
        OTHER = 'OT', _('Другое')
        COLORING = 'CL', _('Окрашивание')  # Добавлена новая категория
        HAIR_CARE = 'HR', _('Уход за волосами') 

    name = models.CharField(
        max_length=200,
        verbose_name=_("Название услуги"),
        help_text=_("Полное название услуги для отображения клиентам"),
        unique=True  # Уникальное имя услуги
    )
    
    description = models.TextField(
        verbose_name=_("Описание"),
        blank=True,
        help_text=_("Подробное описание услуги")
    )
    
    price = models.DecimalField(
        verbose_name=_("Цена"),
        max_digits=7,
        decimal_places=2,
        validators=[MinValueValidator(100)],
        help_text=_("Цена в рублях")
    )
    
    duration = models.PositiveIntegerField(
        verbose_name=_("Длительность"),
        default=30,
        help_text=_("Продолжительность в минутах (от 15 до 240)"),
        validators=[MinValueValidator(15), MaxValueValidator(240)]  # Добавлены ограничения
    )
    
    category = models.CharField(
        verbose_name=_("Категория"),
        max_length=2,
        choices=ServiceCategory.choices,
        default=ServiceCategory.HAIRCUT
    )
    
    is_popular = models.BooleanField(
        verbose_name=_("Популярная услуга"),
        default=False,
        help_text=_("Отображать в списке популярных услуг")
    )
    
    is_active = models.BooleanField(
        verbose_name=_("Активна"),
        default=True,
        help_text=_("Отображать ли услугу клиентам")
    )
    
    image = models.ImageField(
        verbose_name=_("Изображение"),
        upload_to='services/%Y/%m/%d/',  # Более структурированное хранение
        blank=True,
        null=True,
        help_text=_("Изображение для карточки услуги (рекомендуемый размер 800x600px)"),
        validators=[FileExtensionValidator(['jpg', 'jpeg', 'png'])]  # Проверка формата
    )
    
    created_at = models.DateTimeField(
        verbose_name=_("Дата создания"),
        auto_now_add=True
    )
    
    updated_at = models.DateTimeField(
        verbose_name=_("Дата обновления"),
        auto_now=True
    )

    def __str__(self):
        return f"{self.name} ({self.get_category_display()}) - {self.price}₽"

    def clean(self):
        """Дополнительная валидация"""
        if self.price < 100 and self.category != self.OTHER:
            raise ValidationError(
                {'price': _('Цена не может быть меньше 100 рублей для данной категории')}
            )

    def save(self, *args, **kwargs):
        """Автоматическая обработка при сохранении"""
        self.full_clean()  # Вызов полной валидации
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Удаление связанного файла изображения"""
        if self.image:
            if os.path.isfile(self.image.path):
                os.remove(self.image.path)
        super().delete(*args, **kwargs)

    class Meta:
        verbose_name = _("Услуга")
        verbose_name_plural = _("Услуги")
        ordering = ['category', 'name']
        indexes = [
            models.Index(fields=['is_active', 'is_popular']),
            models.Index(fields=['category']),
            models.Index(fields=['price']),  # Добавлен индекс для цены
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'category'],
                name='unique_service_name_per_category'
            )
        ]

    @property
    def duration_display(self):
        """Форматированное отображение длительности"""
        hours = self.duration // 60
        minutes = self.duration % 60
        if hours > 0:
            return f"{hours} ч {minutes} мин"
        return f"{minutes} мин"
    
    @property
    def image_preview(self):
        """Превью изображения для админки"""
        if self.image:
            return format_html(
                '<img src="{}" style="max-height: 100px;" />', 
                self.image.url
            )
        return _("Нет изображения")
    
class Master(models.Model):
    """Модель мастера барбершопа"""
    name = models.CharField(max_length=150, verbose_name="Имя")
    photo = models.ImageField(
        upload_to='masters/',
        verbose_name="Фотография",
        blank=True,  # Добавил blank=True
        null=True    # Добавил null=True
    )
    phone = models.CharField(
        max_length=20, 
        verbose_name="Телефон",
        validators=[RegexValidator(r'^\+?1?\d{9,15}$')]  # Добавил валидатор
    )
    email = models.EmailField(
        verbose_name="Email", 
        blank=True, 
        null=True
    )
    description = models.TextField(
        verbose_name="Описание", 
        blank=True
    )
    instagram = models.CharField(
        max_length=50,
        verbose_name="Instagram",
        blank=True
    )
    experience = models.PositiveIntegerField(
        verbose_name="Стаж (лет)",
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]  # Добавил валидаторы
    )
    services = models.ManyToManyField(
        'Service',  # Используем строку вместо прямого обращения к классу
        related_name='masters',
        verbose_name="Услуги",
        blank=True
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Активен"
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Мастер"
        verbose_name_plural = "Мастера"
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['is_active']),
        ]

class Order(models.Model):
    STATUS_NEW = 'new'
    STATUS_CONFIRMED = 'confirmed'
    STATUS_COMPLETED = 'completed'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_NEW, 'Новая'),
        (STATUS_CONFIRMED, 'Подтвержденная'),
        (STATUS_COMPLETED, 'Выполненная'),
        (STATUS_CANCELLED, 'Отмененная'),
    ]

    client_name = models.CharField(max_length=100, verbose_name="Имя клиента")
    phone = models.CharField(
        max_length=20, 
        verbose_name="Телефон",
        validators=[RegexValidator(r'^\+?1?\d{9,15}$')]
    )
    email = models.EmailField(verbose_name="Email", blank=True, null=True)
    comment = models.TextField(verbose_name="Комментарий", blank=True)
    date = models.DateField(
        verbose_name="Дата записи",
        validators=[MinValueValidator(timezone.now().date())]
    )
    time = models.TimeField(verbose_name="Время записи")
    master = models.ForeignKey(
        Master,
        on_delete=models.CASCADE,
        verbose_name="Мастер"
    )
    services = models.ManyToManyField(
        Service,
        verbose_name="Услуги"
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=STATUS_NEW,
        verbose_name="Статус"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        verbose_name="Пользователь",
        related_name='orders',
        null=True,  # Разрешаем NULL для анонимных пользователей
        blank=True  # Разрешаем пустое значение в формах
    )

    def clean(self):
        super().clean()
        if self.date and self.date < timezone.now().date():
            raise ValidationError({'date': 'Дата записи не может быть в прошлом'})
        if self.date and self.time:
            booking_time = timezone.make_aware(datetime.combine(self.date, self.time))
            if booking_time < timezone.now():
                raise ValidationError('Выбранное время уже прошло')

    def get_total_price(self):
        return sum(service.price for service in self.services.all())

    @property
    def datetime(self):
        """Объединенная дата и время"""
        return timezone.make_aware(datetime.combine(self.date, self.time))

    @property
    def display_number(self):
        """Форматированный номер заказа"""
        return f"{self.id:05d}"

    def __str__(self):
        return f"Запись #{self.display_number} - {self.client_name} ({self.date})"
    
    class Meta:
        verbose_name = "Запись"
        verbose_name_plural = "Записи"
        ordering = ['-date', '-time']
        indexes = [
            models.Index(fields=['status', 'date']),
            models.Index(fields=['master', 'date']),
            models.Index(fields=['user']),
        ]

class Review(models.Model):
    """Модель отзыва о мастере"""
    RATING_CHOICES = [
        (1, '1 - Ужасно'),
        (2, '2 - Плохо'),
        (3, '3 - Удовлетворительно'),
        (4, '4 - Хорошо'),
        (5, '5 - Отлично'),
    ]
    AI_STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved by AI'),
        ('rejected', 'Rejected by AI'),
        ('manual', 'Manual Review Required'),
    ]
    text = models.TextField(verbose_name="Текст отзыва")
    client_name = models.CharField(
        max_length=100,
        verbose_name="Имя клиента"
    )
    master = models.ForeignKey(
        Master,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name="Мастер"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Пользователь"
    )
    photo = models.ImageField(
        upload_to='reviews/',
        blank=True,
        null=True,
        verbose_name="Фотография"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )
    rating = models.PositiveSmallIntegerField(
        choices=RATING_CHOICES,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Оценка"
    )
    is_published = models.BooleanField(
        default=True,
        verbose_name="Опубликован"
    )

    ai_checked_status = models.CharField(
        max_length=20,
        choices=AI_STATUS_CHOICES,
        default='pending',
        verbose_name="AI Check Status"
    )
    def toggle_publish(self):
        """Переключает статус публикации"""
        self.is_published = not self.is_published
        self.save()
        return self.is_published

    def __str__(self):
        return f"Отзыв #{self.id} на {self.master.name} ({self.rating}/5)"

    def ai_status_badge(self):
        classes = {
            "ai_checked_true": "bg-success",
            "ai_cancelled": "bg-danger",
            "ai_checked_in_progress": "bg-info",
            "ai_checked_false": "bg-secondary"
        }
        return format_html(
            '<span class="badge {}">{}</span>',
            classes.get(self.ai_checked_status, "bg-secondary"),
            self.get_ai_checked_status_display()
        )
    ai_status_badge.short_description = "Статус проверки"
    ai_status_badge.admin_order_field = 'ai_checked_status'





    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"
        ordering = ['-created_at']
        permissions = [
            ("can_moderate", "Может модерировать отзывы"),
        ]
                                        