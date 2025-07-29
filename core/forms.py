from django import forms
from django.forms.widgets import CheckboxSelectMultiple, DateInput, TimeInput, FileInput
from django.utils import timezone
from datetime import date, timedelta
import re
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model
from .models import Order, Master, Service, Review
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from django.contrib.auth.forms import (
    PasswordResetForm, 
    SetPasswordForm,
    PasswordChangeForm,
)

User = get_user_model()

class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'example@mail.com'
        })
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Логин'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Пароль'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Подтверждение пароля'
        })

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user
    
class LoginForm(AuthenticationForm):
    remember_me = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Логин'
        })
        self.fields['password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Пароль'
        })

class OrderForm(forms.ModelForm):
    services = forms.ModelMultipleChoiceField(
        queryset=Service.objects.none(),
        widget=CheckboxSelectMultiple(attrs={
            'class': 'form-check-input service-checkbox',
            'id': 'services-select'
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
        self.request_user = kwargs.pop('request_user', None)
        super().__init__(*args, **kwargs)
        self.fields['master'].queryset = Master.objects.filter(is_active=True)
        
        if 'master' in self.data:
            try:
                master_id = int(self.data.get('master'))
                master = Master.objects.get(id=master_id)
                self.fields['services'].queryset = master.services.filter(is_active=True)
            except (ValueError, Master.DoesNotExist):
                self.fields['services'].queryset = Service.objects.none()
        elif self.instance and self.instance.pk and self.instance.master:
            self.fields['services'].queryset = self.instance.master.services.filter(is_active=True)
        else:
            self.fields['services'].queryset = Service.objects.none()
        
        tomorrow = date.today() + timedelta(days=1)
        self.fields['date'].widget.attrs['min'] = tomorrow.isoformat()

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '')
        phone = ''.join(filter(str.isdigit, phone))
        if len(phone) not in (10, 11):
            raise forms.ValidationError('Введите корректный номер телефона (10 или 11 цифр)')
        return phone

    def clean(self):
        cleaned_data = super().clean()
        date_val = cleaned_data.get('date')
        time_val = cleaned_data.get('time')
        master = cleaned_data.get('master')
        services = cleaned_data.get('services', [])
        
        if date_val and date_val < date.today():
            self.add_error('date', 'Нельзя выбрать прошедшую дату')
            
        if date_val and time_val:
            booking_time = timezone.make_aware(timezone.datetime.combine(date_val, time_val))
            if booking_time < timezone.now():
                self.add_error('time', 'Выбранное время уже прошло')
        
        if master and services:
            master_services = master.services.all()
            invalid_services = [s for s in services if s not in master_services]
            
            if invalid_services:
                invalid_names = ", ".join([s.name for s in invalid_services])
                self.add_error('services', 
                    f"Мастер {master.name} не предоставляет выбранные услуги: {invalid_names}")
        
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Привязываем пользователя если он авторизован
        if self.request_user and self.request_user.is_authenticated:
            instance.user = self.request_user
        
        if commit:
            instance.save()
            self.save_m2m()
        
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

class OrderStatusForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['status']
        widgets = {
            'status': forms.Select(attrs={
                'class': 'form-select'
            })
        }

# ================== ФОРМЫ ОТЗЫВОВ ==================
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
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'rating-select'
        }),
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
            'photo': FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'master': forms.Select(attrs={
                'class': 'form-select',
                'id': 'review-master-select'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['master'].queryset = Master.objects.filter(is_active=True)
        self.fields['master'].label_from_instance = lambda obj: f"{obj.name} ({obj.experience} лет опыта)"

class AdminReviewForm(ReviewForm):
    class Meta(ReviewForm.Meta):
        fields = ['client_name', 'text', 'rating', 'photo', 'master', 'is_published']
        widgets = {
            **ReviewForm.Meta.widgets,
            'is_published': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }

class ReviewPublishForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['is_published']
        widgets = {
            'is_published': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }

# ================== ФОРМЫ МАСТЕРОВ ==================
class MasterForm(forms.ModelForm):
    services = forms.ModelMultipleChoiceField(
        queryset=Service.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    class Meta:
        model = Master
        fields = '__all__'
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Полное имя мастера'
            }),
            'photo': FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Описание навыков и специализации'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+7 (999) 123-45-67'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'example@mail.ru'
            }),
            'instagram': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '@username'
            }),
            'experience': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '')
        phone = ''.join(filter(str.isdigit, phone))
        if len(phone) not in (10, 11):
            raise forms.ValidationError('Введите корректный номер телефона (10 или 11 цифр)')
        return phone

# ================== ФОРМЫ УСЛУГ ==================
class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['name', 'price', 'duration', 'description', 'category', 'is_active', 'is_popular', 'image']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Название услуги',
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Подробное описание услуги'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 100,
                'required': True
            }),
            'duration': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 15,
                'step': 15,
                'required': True
            }),
            'category': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_popular': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price < 100:
            raise forms.ValidationError('Цена должна быть не менее 100 рублей')
        return price

    def clean_duration(self):
        duration = self.cleaned_data.get('duration')
        if duration < 15:
            raise forms.ValidationError('Длительность должна быть не менее 15 минут')
        return duration
    
class CustomPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Ваш email',
            'autocomplete': 'email'
        })
    )

class CustomSetPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(
        label="Новый пароль",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Новый пароль',
            'autocomplete': 'new-password'
        }),
        strip=False,
        help_text=None,  # Убираем подсказки
    )
    new_password2 = forms.CharField(
        label="Подтверждение пароля",
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Подтвердите новый пароль',
            'autocomplete': 'new-password'
        }),
        help_text=None,  # Убираем подсказки
    )

class UserPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(
        label="Текущий пароль",
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Текущий пароль',
            'autocomplete': 'current-password'
        }),
    )
    new_password1 = forms.CharField(
        label="Новый пароль",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Новый пароль',
            'autocomplete': 'new-password'
        }),
        strip=False,
        help_text=None,
    )
    new_password2 = forms.CharField(
        label="Подтверждение пароля",
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Подтвердите новый пароль',
            'autocomplete': 'new-password'
        }),
        help_text=None,
    )