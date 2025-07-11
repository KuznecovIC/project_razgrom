from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse
from django.utils import timezone
from django.contrib import messages
from django.db.models import Q, Max
from .models import Master, Service, Order, Review
from .forms import OrderForm, OrderSearchForm, ReviewForm
from django.db import connection
from django.db import transaction
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.http import JsonResponse



def init_masters():
    """Инициализация мастеров при первом запуске"""
    if not Master.objects.exists():
        Master.objects.bulk_create([
            Master(
                name="Алексей 'Бритва' Петров",
                photo="masters/master1.jpg",
                description="Специалист по классическим и современным стрижкам. Стаж 8 лет.",
                instagram="@barber_alex",
                experience=8,
                is_active=True
            ),
            Master(
                name="Дмитрий 'Стиль' Иванов",
                photo="masters/master2.jpg",
                description="Эксперт по бородам и уходу за ними. Любит сложные формы.",
                instagram="@beard_master",
                experience=5,
                is_active=True
            ),
            Master(
                name="Сергей 'Точность' Смирнов",
                photo="masters/master3.jpg",
                description="Мастер детализации. Идеальные линии и четкие контуры.",
                instagram="@sharp_lines",
                experience=6,
                is_active=True
            )
        ])

def init_services():
    """Инициализация услуг при первом запуске"""
    if not Service.objects.exists():
        Service.objects.bulk_create([
            Service(name="Мужская стрижка", price=1200, is_popular=True),
            Service(name="Детская стрижка", price=800),
            Service(name="Стрижка машинкой", price=700),
            Service(name="Оформление бороды", price=600, is_popular=True),
            Service(name="Королевское бритьё", price=900),
            Service(name="Комплекс (стрижка+борода)", price=1500, is_popular=True),
            Service(name="Камуфляж седины", price=500),
            Service(name="Укладка", price=300)
        ])

def index(request):
    """Главная страница"""
    context = {
        'masters': Master.objects.filter(is_active=True),
        'services': Service.objects.filter(is_active=True)[:6],  # Убрали order_by('?')
        'reviews': Review.objects.filter(is_published=True)
                               .select_related('master')
                               .order_by('-created_at')[:6]
    }
    return render(request, 'landing.html', context)

def landing(request):
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    order = form.save(commit=False)
                    if request.user.is_authenticated:
                        order.user = request.user
                    order.save()
                    form.save_m2m()
                    request.session['last_order_id'] = order.id
                    return redirect('thanks')
            except Exception as e:
                messages.error(request, f'Ошибка при сохранении: {str(e)}')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме')
    else:
        form = OrderForm()
    
    context = {
        'form': form,
        'masters': Master.objects.filter(is_active=True),
        'services': Service.objects.filter(is_active=True)
    }
    return render(request, 'landing.html', context)

@login_required
def order_list(request):
    """Улучшенный список записей с пагинацией и поиском"""
    # Отладочная информация
    print(f"\n[DEBUG] Пользователь: {request.user.username} (ID: {request.user.id})")
    print(f"[DEBUG] Персонал: {request.user.is_staff}")
    
    # Базовый запрос
    query = Q()
    if not request.user.is_staff:
        query &= Q(user=request.user)
    
    # Поиск по параметрам
    search_form = OrderSearchForm(request.GET)
    if search_form.is_valid():
        search = search_form.cleaned_data.get('search', '')
        if search:
            query &= (
                Q(client_name__icontains=search) |
                Q(phone__icontains=search) |
                Q(comment__icontains=search) |
                Q(master__name__icontains=search)
            )
    else:
        search = ''
    
    # Полный запрос с оптимизацией
    orders = Order.objects.filter(query)\
               .select_related('master')\
               .prefetch_related('services')\
               .order_by('-date', '-time')
    
    # Пагинация (по 10 записей на страницу)
    paginator = Paginator(orders, 10)
    page_number = request.GET.get('page')
    
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    
    # Отладочная информация для шаблона
    debug_info = {
        'current_user': request.user.username,
        'user_id': request.user.id,
        'total_orders': orders.count(),
        'sql_query': str(orders.query),
        'is_staff': request.user.is_staff
    }
    
    return render(request, 'orders/list.html', {
        'orders': page_obj,
        'search_form': search_form,
        'debug_info': debug_info,
        'user': request.user
    })

def thanks(request):
    """Страница подтверждения записи"""
    order_id = request.session.get('last_order_id')
    if not order_id:
        messages.error(request, 'Не найден ID заказа')
        return redirect('landing')
    
    try:
        order = get_object_or_404(Order, id=order_id)
        return render(request, 'core/thanks.html', {
            'order': order,
            'services': order.services.all(),
            'total_price': order.total_price()
        })
    except Exception as e:
        messages.error(request, f'Ошибка при отображении заказа: {str(e)}')
        return redirect('landing')

def services_view(request):
    """Страница всех услуг"""
    services = Service.objects.filter(is_active=True)
    return render(request, 'core/services.html', {
        'services': services
    })

def get_master_services(request, master_id):
    master = get_object_or_404(Master, id=master_id)
    services = master.services.filter(is_active=True).values('id', 'name', 'description', 'price')
    return JsonResponse(list(services), safe=False)

@login_required
def order_list(request):
    """Список записей с исправлениями"""
    # Улучшенная фильтрация
    query = Q()
    if not request.user.is_staff:
        query &= Q(user=request.user) | Q(phone=request.user.username)
    
    # Поиск
    search = request.GET.get('search', '')
    if search:
        query &= (
            Q(client_name__icontains=search) |
            Q(phone__icontains=search) |
            Q(comment__icontains=search)
        )
    
    orders = Order.objects.filter(query)\
               .select_related('master')\
               .prefetch_related('services')\
               .order_by('-date', '-time')
    
    # Пагинация
    paginator = Paginator(orders, 10)
    page = request.GET.get('page')
    
    try:
        orders = paginator.page(page)
    except PageNotAnInteger:
        orders = paginator.page(1)
    except EmptyPage:
        orders = paginator.page(paginator.num_pages)
    
    return render(request, 'orders/list.html', {
        'orders': orders,
        'search': search
    })

@login_required
def order_detail(request, pk):
    """Детали заказа"""
    order = get_object_or_404(
        Order.objects.select_related('master').prefetch_related('services'),
        pk=pk,
        user=request.user
    )
    return render(request, 'orders/detail.html', {
        'order': order,
        'total_price': order.total_price()
    })

@login_required
def order_edit(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = OrderForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            messages.success(request, 'Запись успешно обновлена!')
            return redirect('order_detail', pk=order.id)
    else:
        form = OrderForm(instance=order)
        # Явно задаем queryset для поля master
        form.fields['master'].queryset = Master.objects.filter(is_active=True)
    
    return render(request, 'orders/edit.html', {
        'form': form,
        'order': order
    })

@login_required
def order_delete(request, pk):
    """Удаление заказа"""
    order = get_object_or_404(Order, pk=pk, user=request.user)
    
    if request.method == 'POST':
        order.delete()
        messages.success(request, 'Запись успешно удалена!')
        return redirect('order_list')
    
    return render(request, 'orders/confirm_delete.html', {
        'order': order
    })

@user_passes_test(lambda u: u.is_staff)
def admin_orders_list(request):
    """Список всех заказов (админ)"""
    orders = Order.objects.select_related('master', 'user')\
                         .prefetch_related('services')\
                         .order_by('-date', '-time')
    return render(request, 'admin/orders_list.html', {'orders': orders})

@user_passes_test(lambda u: u.is_staff)
def admin_order_detail(request, order_id):
    """Детали заказа (админ)"""
    order = get_object_or_404(
        Order.objects.select_related('master', 'user').prefetch_related('services'),
        pk=order_id
    )
    return render(request, 'admin/order_detail.html', {
        'order': order,
        'total_price': order.total_price()
    })

@user_passes_test(lambda u: u.is_staff)
def admin_order_edit(request, order_id):
    """Редактирование заказа (админ)"""
    order = get_object_or_404(Order, pk=order_id)
    
    if request.method == 'POST':
        form = OrderForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            messages.success(request, 'Запись успешно обновлена!')
            return redirect('admin_order_detail', order_id=order.id)
    else:
        form = OrderForm(instance=order)
    
    return render(request, 'admin/order_edit.html', {
        'form': form,
        'order': order
    })

@user_passes_test(lambda u: u.is_staff)
def admin_order_delete(request, order_id):
    """Удаление заказа (админ)"""
    order = get_object_or_404(Order, pk=order_id)
    
    if request.method == 'POST':
        order.delete()
        messages.success(request, 'Запись успешно удалена!')
        return redirect('admin_orders_list')
    
    return render(request, 'admin/order_confirm_delete.html', {
        'order': order
    })

@login_required
def add_review(request):
    """Добавление нового отзыва"""
    if request.method == 'POST':
        form = ReviewForm(request.POST, request.FILES)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.save()
            messages.success(request, 'Ваш отзыв успешно добавлен!')
            return redirect('review_list')
    else:
        form = ReviewForm()
    
    return render(request, 'reviews/add_review.html', {
        'form': form,
        'masters': Master.objects.filter(is_active=True)
    })

def review_list(request):
    """Список всех отзывов"""
    reviews = Review.objects.filter(is_published=True)\
                           .select_related('master')
    
    rating = request.GET.get('rating')
    if rating:
        reviews = reviews.filter(rating=rating)
    
    # Добавьте отладочный вывод
    print(f"Found {reviews.count()} published reviews")
    
    paginator = Paginator(reviews.order_by('-created_at'), 10)
    page_number = request.GET.get('page')
    
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    
    # Добавьте отладочную информацию в контекст
    return render(request, 'reviews/list.html', {
        'page_obj': page_obj,
        'total_reviews': paginator.count,
        'debug': {
            'total_in_db': Review.objects.count(),
            'published': Review.objects.filter(is_published=True).count(),
            'current_page': page_number,
            'items_on_page': len(page_obj.object_list)
        }
    })

def review_detail(request, pk):
    """Детальная страница отзыва"""
    review = get_object_or_404(
        Review.objects.select_related('master'),
        pk=pk,
        is_published=True
    )
    return render(request, 'reviews/detail.html', {
        'review': review
    })

@login_required
def delete_review(request, review_id):
    """Удаление отзыва"""
    review = get_object_or_404(Review, id=review_id)
    
    if request.user.is_staff or request.user == review.user:
        review.delete()
        messages.success(request, 'Отзыв успешно удален.')
    else:
        messages.error(request, 'У вас нет прав для удаления этого отзыва.')
    
    return redirect('review_list') 