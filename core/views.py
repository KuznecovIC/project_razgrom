from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.urls import reverse
from django.utils import timezone
from .models import Master, Service, Order
from .forms import OrderForm
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Order
from .forms import OrderForm


def init_masters():
    """Инициализация мастеров при первом запуске"""
    if not Master.objects.exists():
        Master.objects.bulk_create([
            Master(
                name="Алексей 'Бритва' Петров",
                photo="masters/master1.jpg",
                description="Специалист по классическим и современным стрижкам. Стаж 8 лет.",
                instagram="@barber_alex",
                experience=8
            ),
            Master(
                name="Дмитрий 'Стиль' Иванов",
                photo="masters/master2.jpg",
                description="Эксперт по бородам и уходу за ними. Любит сложные формы.",
                instagram="@beard_master",
                experience=5
            ),
            Master(
                name="Сергей 'Точность' Смирнов",
                photo="masters/master3.jpg",
                description="Мастер детализации. Идеальные линии и четкие контуры.",
                instagram="@sharp_lines",
                experience=6
            )
        ])

def init_services():
    """Инициализация услуг при первом запуске"""
    if not Service.objects.exists():
        Service.objects.bulk_create([
            Service(name="Мужская стрижка", price=1200),
            Service(name="Детская стрижка", price=800),
            Service(name="Стрижка машинкой", price=700),
            Service(name="Оформление бороды", price=600),
            Service(name="Королевское бритьё", price=900),
            Service(name="Комплекс (стрижка+борода)", price=1500),
            Service(name="Камуфляж седины", price=500),
            Service(name="Укладка", price=300)
        ])

def landing(request):
    """Главная страница с формой записи"""
    init_masters()
    init_services()
    
    masters = Master.objects.all()
    services = Service.objects.all()
    
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.created_at = timezone.now()
            order.save()
            form.save_m2m()  # Сохраняем многие-ко-многим (услуги)
            return redirect(reverse('thanks', kwargs={'order_id': order.id}))
    else:
        form = OrderForm()
    
    return render(request, 'landing.html', {
        'masters': masters,
        'services': services,
        'form': form
    })

def thanks(request, order_id):
    """Страница подтверждения записи"""
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'core/thanks.html', {
        'order': order,
        'services': order.services.all(),
        'total_price': sum(service.price for service in order.services.all())
    })

@user_passes_test(lambda u: u.is_staff)
def orders_list(request):
    """Список всех записей для администратора"""
    orders = Order.objects.select_related('master').prefetch_related('services').all()
    return render(request, 'core/orders_list.html', {'orders': orders})

@user_passes_test(lambda u: u.is_staff)
def order_detail(request, order_id):  # Было pk
    order = get_object_or_404(Order.objects.select_related('master'), pk=order_id)
    return render(request, 'core/order_detail.html', {
        'order': order,
        'services': order.services.all()
    })

@user_passes_test(lambda u: u.is_staff)
def order_edit(request, order_id):  # Было pk
    order = get_object_or_404(Order, pk=order_id)
    if request.method == 'POST':
        form = OrderForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            messages.success(request, 'Запись успешно обновлена!')
            return redirect('order_detail', order_id=order.id)
    else:
        form = OrderForm(instance=order)
    return render(request, 'core/order_edit.html', {'form': form, 'order': order})

@user_passes_test(lambda u: u.is_staff)
def order_delete(request, order_id):  # Было pk
    order = get_object_or_404(Order, pk=order_id)
    if request.method == 'POST':
        order.delete()
        messages.success(request, 'Запись успешно удалена!')
        return redirect('orders_list')
    return render(request, 'core/order_confirm_delete.html', {'order': order})