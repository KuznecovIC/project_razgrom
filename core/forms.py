from django import forms
from django.forms.widgets import CheckboxSelectMultiple, DateInput, TimeInput
from django.utils import timezone
from datetime import date, timedelta
import re
from .models import Order, Master, Service, Review


class OrderForm(forms.ModelForm):
    services = forms.ModelMultipleChoiceField(
        queryset=Service.objects.none(),  # Будет переопределено в __init__
        widget=CheckboxSelectMultiple(attrs={
            'class': 'form-check-input service-checkbox'
        }),
        required=True,
        label="Услуги"
    )
    
    date = forms.DateField(
        widget=DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
            'id': 'order-date',
            'min': (date.today() + timedelta(days=1)).isoformat()
        }),
        label="Дата записи"
    )
    
    time = forms.TimeField(
        widget=TimeInput(attrs={
            'type': 'time',
            'class': 'form-control',
            'id': 'order-time'
        }),
        label="Время записи"
    )

    class Meta:
        model = Order
        fields = ['client_name', 'phone', 'email', 'date', 'time', 'master', 'services', 'comment']
        widgets = {
            'client_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Иван Иванов'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+7 (999) 123-45-67'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'example@mail.ru'
            }),
            'master': forms.Select(attrs={
                'class': 'form-select',
                'id': 'master-select'
            }),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Ваши пожелания...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['master'].queryset = Master.objects.filter(is_active=True)
        self.fields['services'].queryset = Service.objects.filter(is_active=True)
        
        # Обновляем минимальную дату
        tomorrow = date.today() + timedelta(days=1)
        self.fields['date'].widget.attrs['min'] = tomorrow.isoformat()

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '')
        # Более гибкая валидация номера
        phone = ''.join(filter(str.isdigit, phone))
        if len(phone) not in (10, 11):
            raise forms.ValidationError('Введите корректный номер телефона (10 или 11 цифр)')
        return phone

    def clean(self):
        cleaned_data = super().clean()
        date_val = cleaned_data.get('date')
        time_val = cleaned_data.get('time')
        
        # Мягкая проверка даты
        if date_val and date_val < date.today():
            self.add_error('date', 'Нельзя выбрать прошедшую дату')
            
        if date_val and time_val:
            booking_time = timezone.make_aware(
                timezone.datetime.combine(date_val, time_val)
            )
            if booking_time < timezone.now():
                self.add_error('time', 'Выбранное время уже прошло')
        
        return cleaned_data

    def save(self, commit=True):
        # Сохраняем модель, но не коммитим, чтобы добавить пользователя
        instance = super().save(commit=False)
        
        # Добавляем текущего пользователя
        if hasattr(self, 'request_user'):
            instance.user = self.request_user
        
        if commit:
            instance.save()
            self.save_m2m()  # Важно для ManyToMany полей
        
        return instance

class OrderSearchForm(forms.Form):
    SEARCH_FIELD_CHOICES = [
        ('client_name', 'По имени клиента'),
        ('phone', 'По телефону'),
        ('comment', 'По комментарию'),
    ]
    
    search_query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите запрос...'
        })
    )
    
    search_fields = forms.MultipleChoiceField(
        choices=SEARCH_FIELD_CHOICES,
        initial=['client_name'],
        widget=CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        }),
        required=False
    )


class ReviewForm(forms.ModelForm):
    RATING_CHOICES = [
        (1, '1 - Плохо'),
        (2, '2 - Удовлетворительно'),
        (3, '3 - Нормально'),
        (4, '4 - Хорошо'),
        (5, '5 - Отлично')
    ]
    
    rating = forms.ChoiceField(
        choices=RATING_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Оценка'
    )

    class Meta:
        model = Review
        fields = ['client_name', 'text', 'rating', 'photo', 'master']
        widgets = {
            'client_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ваше имя'
            }),
            'text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Ваш отзыв...'
            }),
            'photo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'master': forms.Select(attrs={
                'class': 'form-select'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['master'].queryset = Master.objects.filter(is_active=True)
        self.fields['master'].label_from_instance = lambda obj: f"{obj.name} ({obj.experience} лет опыта)"