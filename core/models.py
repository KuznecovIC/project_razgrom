from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.db import connection

class Service(models.Model):
    """Модель услуги барбершопа"""
    name = models.CharField(max_length=200, verbose_name="Название")
    description = models.TextField(blank=True, verbose_name="Описание")
    price = models.DecimalField(
        max_digits=7, 
        decimal_places=2,
        validators=[MinValueValidator(100)],
        verbose_name="Цена"
    )
    duration = models.PositiveIntegerField(
        verbose_name="Длительность (мин)",
        default=30
    )
    is_popular = models.BooleanField(
        default=False,
        verbose_name="Популярная услуга"
    )
    image = models.ImageField(
        upload_to='services/',
        blank=True,
        null=True,
        verbose_name="Изображение"
    )

    def __str__(self):
        return f"{self.name} - {self.price}₽"

    class Meta:
        verbose_name = "Услуга"
        verbose_name_plural = "Услуги"
        ordering = ['name']

class Master(models.Model):
    """Модель мастера барбершопа"""
    name = models.CharField(max_length=150, verbose_name="Имя")
    photo = models.ImageField(
        upload_to='masters/',
        verbose_name="Фотография"
    )
    phone = models.CharField(max_length=20, verbose_name="Телефон")
    description = models.TextField(verbose_name="Описание", blank=True)
    instagram = models.CharField(
        max_length=50,
        verbose_name="Instagram",
        blank=True
    )
    experience = models.PositiveIntegerField(
        verbose_name="Стаж (лет)",
        default=0
    )
    services = models.ManyToManyField(
        Service,
        related_name='masters',
        verbose_name="Услуги"
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

class Order(models.Model):
    """Модель заказа в барбершопе"""
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

    client_name = models.CharField(
        max_length=100,
        verbose_name="Имя клиента"
    )
    phone = models.CharField(
        max_length=20,
        verbose_name="Телефон",
        blank=True,
        null=True
    )
    date = models.DateTimeField(verbose_name="Дата и время записи")
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

    def total_price(self):
        """Возвращает общую стоимость заказа"""
        return sum(service.price for service in self.services.all())

    def __str__(self):
        return f"Запись #{self.id} - {self.client_name}"

    def delete(self, *args, **kwargs):
        """Переопределение удаления для сброса автоинкремента в SQLite"""
        super().delete(*args, **kwargs)
        if connection.vendor == 'sqlite':
            cursor = connection.cursor()
            cursor.execute("""
                UPDATE SQLITE_SEQUENCE 
                SET SEQ=0 
                WHERE NAME='core_order'
            """)

    class Meta:
        verbose_name = "Запись"
        verbose_name_plural = "Записи"
        ordering = ['-date']

class Review(models.Model):
    """Модель отзыва о мастере"""
    RATING_CHOICES = [
        (1, '1 - Ужасно'),
        (2, '2 - Плохо'),
        (3, '3 - Удовлетворительно'),
        (4, '4 - Хорошо'),
        (5, '5 - Отлично'),
    ]

    text = models.TextField(verbose_name="Текст отзыва")
    client_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Имя клиента"
    )
    master = models.ForeignKey(
        Master,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name="Мастер"
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

    def __str__(self):
        return f"Отзыв #{self.id} на {self.master.name}"

    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"
        ordering = ['-created_at']