from django import forms
from .models import Order, Master, Service
from django.forms.widgets import CheckboxSelectMultiple, DateInput

class OrderForm(forms.ModelForm):
    services = forms.ModelMultipleChoiceField(
        queryset=Service.objects.all(),
        widget=CheckboxSelectMultiple,
        required=True
    )
    date = forms.DateField(
        widget=DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )

    class Meta:
        model = Order
        fields = ['client_name', 'phone', 'date', 'master', 'services']
        widgets = {
            'client_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+7 (999) 123-45-67'}),
            'master': forms.Select(attrs={'class': 'form-select'}),
            # services - виджет уже указан выше
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from datetime import date, timedelta
        tomorrow = date.today() + timedelta(days=1)
        self.fields['date'].widget.attrs['min'] = tomorrow.isoformat()

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '')
        import re
        if phone and not re.match(r'^\+?\d[\d\s\-\(\)]{7,}$', phone):
            raise forms.ValidationError('Некорректный номер телефона')
        return phone
