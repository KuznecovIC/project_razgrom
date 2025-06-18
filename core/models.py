from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.db import models
from django.db import connection


class Master(models.Model):
    name = models.CharField(max_length=100, verbose_name="Имя мастера")
    photo = models.ImageField(upload_to='images/masters/')
    description = models.TextField(verbose_name="Описание", blank=True)
    instagram = models.CharField(max_length=50, verbose_name="Instagram", blank=True)
    experience = models.PositiveIntegerField(verbose_name="Стаж (лет)", default=0)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Мастер"
        verbose_name_plural = "Мастера"


class Service(models.Model):
    name = models.CharField(max_length=200, verbose_name="Название услуги")
    price = models.DecimalField(
        max_digits=7, 
        decimal_places=2,
        validators=[MinValueValidator(100)],
        verbose_name="Цена"
    )

    def __str__(self):
        return f"{self.name} - {self.price}₽"

    class Meta:
        verbose_name = "Услуга"
        verbose_name_plural = "Услуги"


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
    phone = models.CharField(max_length=20, verbose_name="Телефон", blank=True, null=True)
    date = models.DateTimeField(verbose_name="Дата и время записи")
    master = models.ForeignKey(
        Master,
        on_delete=models.CASCADE,
        verbose_name="Мастер"
    )
    services = models.ManyToManyField(Service, verbose_name="Услуги")
    status = models.CharField(
        max_length=10, 
        choices=STATUS_CHOICES, 
        default=STATUS_NEW,
        verbose_name="Статус"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    def total_price(self):
        return sum(service.price for service in self.services.all())

    def __str__(self):
        return f"Запись #{self.id} - {self.client_name} ({self.get_status_display()})"
    def delete(self, *args, **kwargs):
        # Сбрасываем автоинкремент при удалении
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