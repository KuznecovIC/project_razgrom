from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse
from django.utils import timezone
from django.contrib import messages
from django.db.models import Q
from django.db import transaction
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from .models import Master, Service, Order, Review # Ensure all models are imported
from .forms import OrderForm, OrderSearchForm, ReviewForm, MasterForm, ServiceForm, OrderStatusForm, ReviewPublishForm # Ensure all forms are imported
from datetime import datetime, timedelta, date
from .telegram_bot import send_telegram_message
from django.http import HttpResponse

# Инициализационные функции
def init_masters():
    if not Master.objects.exists():
        Master.objects.bulk_create([
            Master(name="Алексей 'Бритва' Петров", photo="masters/master1.jpg",
                   description="Специалист по классическим стрижкам", experience=8),
            Master(name="Дмитрий 'Стиль' Иванов", photo="masters/master2.jpg",
                   description="Эксперт по бородам", experience=5),
        ])

def init_services():
    if not Service.objects.exists():
        Service.objects.bulk_create([
            Service(name="Мужская стрижка", price=1200, duration=60),
            Service(name="Оформление бороды", price=800, duration=45),
            Service(name="Комплекс (стрижка + борода)", price=1800, duration=100),
            Service(name="Детская стрижка", price=900, duration=45),
            Service(name="Бритье головы", price=1000, duration=60),
            Service(name="Тонирование волос/бороды", price=700, duration=30),
            Service(name="Уход за лицом", price=1500, duration=60),
        ])


# Основные представления (Public/User-facing)
def index(request):
    init_masters()
    init_services()
    context = {
        'masters': Master.objects.filter(is_active=True),
        'services': Service.objects.filter(is_active=True)[:6],
        'reviews': Review.objects.filter(is_published=True).order_by('-created_at')[:6]
    }
    return render(request, 'landing.html', context)

def landing(request):
    min_date = date.today() + timedelta(days=1) # Consistent min_date calculation

    if request.method == 'POST':
        form = OrderForm(request.POST)
        selected_master_services = None # Initialize for POST path

        if form.is_valid():
            try:
                with transaction.atomic():
                    order = form.save(commit=False)
                    if request.user.is_authenticated:
                        order.user = request.user
                    
                    master = order.master
                    selected_services_from_form = form.cleaned_data['services']
                    master_services = master.services.all()
                    
                    # Store master's services for re-rendering if validation fails
                    selected_master_services = master_services 

                    invalid_services = [s for s in selected_services_from_form if s not in master_services]
                    if invalid_services:
                        messages.error(request, 'Выбраны услуги, которые не предоставляет мастер')
                        # If invalid services, we re-render the form with validation errors
                        # and need to pass the master's services again
                        context = {
                            'form': form,
                            'masters': Master.objects.filter(is_active=True),
                            'services': Service.objects.filter(is_active=True), # General services
                            'reviews': Review.objects.filter(is_published=True).order_by('-created_at')[:6],
                            'min_date': min_date,
                            'selected_master_services': selected_master_services, # Pass master's services
                        }
                        return render(request, 'landing.html', context)
                    
                    order.save()
                    form.save_m2m()
                    request.session['last_order_id'] = order.id
                    messages.success(request, 'Запись успешно создана! Ожидайте звонка для подтверждения.')
                    return redirect('thanks')
            except Exception as e:
                messages.error(request, f'Ошибка: {str(e)}')
                # If exception, also re-render the form
                if form.cleaned_data.get('master'):
                    try:
                        master_obj = Master.objects.get(id=form.cleaned_data['master'].id)
                        selected_master_services = master_obj.services.all()
                    except Master.DoesNotExist:
                        selected_master_services = None
        else:
            messages.error(request, 'Исправьте ошибки в форме. Пожалуйста, проверьте все поля.')
            # If form is invalid, and a master was selected, get their services
            if request.POST.get('master'):
                try:
                    master_id_from_post = request.POST.get('master')
                    master_obj = Master.objects.get(id=master_id_from_post)
                    selected_master_services = master_obj.services.all()
                except (Master.DoesNotExist, ValueError):
                    selected_master_services = None
    else: # GET request
        form = OrderForm()
        selected_master_services = None # Initialize for GET path
        # If there's a master pre-selected in GET params (unlikely for a new form load but good for robustness)
        if 'master' in request.GET:
            try:
                pre_selected_master_id = request.GET.get('master')
                master_obj = Master.objects.get(id=pre_selected_master_id)
                selected_master_services = master_obj.services.all()
            except (Master.DoesNotExist, ValueError):
                selected_master_services = None


    context = {
        'form': form,
        'masters': Master.objects.filter(is_active=True),
        'services': Service.objects.filter(is_active=True), # This remains all services for general display
        'reviews': Review.objects.filter(is_published=True).order_by('-created_at')[:6],
        'min_date': min_date,
        'selected_master_services': selected_master_services, # Pass the dynamically fetched services
    }
    return render(request, 'landing.html', context)


def thanks(request):
    order_id = request.session.get('last_order_id')
    if not order_id:
        return redirect('landing')
    order = get_object_or_404(Order, id=order_id)
    if 'last_order_id' in request.session:
        del request.session['last_order_id']
    return render(request, 'thanks.html', {'order': order})


# Представления для работы с заказами (User-specific)
@login_required
def order_list(request):
    """Список записей с пагинацией и поиском для пользователя."""
    query = Q(user=request.user) | Q(phone=request.user.username)
    
    search = request.GET.get('search', '')
    if search:
        query &= (
            Q(client_name__icontains=search) |
            Q(phone__icontains=search) |
            Q(comment__icontains=search) |
            Q(master__name__icontains=search) |
            Q(services__name__icontains=search)
        )

    orders = Order.objects.filter(query)\
               .select_related('master', 'user')\
               .prefetch_related('services')\
               .order_by('-date', '-time')

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
    """Детали заказа для пользователя."""
    order_query = Order.objects.select_related('master').prefetch_related('services')
    if not request.user.is_staff:
        order = get_object_or_404(order_query, pk=pk, user=request.user)
    else:
        order = get_object_or_404(order_query, pk=pk)

    return render(request, 'orders/detail.html', {
        'order': order,
        'total_price': order.total_price()
    })

@login_required
def order_create(request):
    """Создание новой записи пользователем."""
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user
            
            # Проверка услуг мастера
            master = order.master
            selected_services = form.cleaned_data['services']
            master_services = master.services.all()
            
            invalid_services = [s for s in selected_services if s not in master_services]
            if invalid_services:
                messages.error(request, 
                    f"Мастер {master.name} не предоставляет выбранные услуги")
                return render(request, 'orders/create.html', {
                    'form': form,
                    'masters': Master.objects.filter(is_active=True)
                })
            
            order.save()
            form.save_m2m()
            messages.success(request, 'Запись успешно создана!')
            return redirect('order_list')
    else:
        form = OrderForm(initial={
            'client_name': request.user.get_full_name() or request.user.username,
            'phone': request.user.username
        })
    
    return render(request, 'orders/create.html', {
        'form': form,
        'masters': Master.objects.filter(is_active=True)
    })


@login_required
def order_edit(request, pk):
    """Редактирование записи пользователем."""
    order = get_object_or_404(Order, pk=pk)
    if not request.user.is_staff and order.user != request.user:
        messages.error(request, 'У вас нет прав для редактирования этой записи.')
        return redirect('order_list')

    if request.method == 'POST':
        form = OrderForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            messages.success(request, 'Запись успешно обновлена!')
            return redirect('order_detail', pk=order.id)
    else:
        form = OrderForm(instance=order)
        form.fields['master'].queryset = Master.objects.filter(is_active=True)

    return render(request, 'orders/edit.html', {
        'form': form,
        'order': order
    })

@login_required
def order_delete(request, pk):
    """Удаление записи пользователем."""
    order = get_object_or_404(Order, pk=pk)
    if not request.user.is_staff and order.user != request.user:
        messages.error(request, 'У вас нет прав для удаления этой записи.')
        return redirect('order_list')

    if request.method == 'POST':
        order.delete()
        messages.success(request, 'Запись успешно удалена!')
        return redirect('order_list')

    return render(request, 'orders/confirm_delete.html', {
        'order': order
    })


# Административные представления (Admin-specific)
@user_passes_test(lambda u: u.is_staff)
def admin_panel(request):
    """
    Main admin dashboard view.
    Includes stats and recent new orders for quick overview.
    """
    today = timezone.now().date()
    start_of_week = today - timedelta(days=today.weekday())

    recent_orders = Order.objects.filter(
        date__gte=start_of_week,
        status='new'
    ).select_related('master', 'user').prefetch_related('services').order_by('-date', '-time')[:10]

    stats = {
        'masters_count': Master.objects.count(),
        'services_count': Service.objects.count(),
        'orders_count': Order.objects.count(),
        'reviews_count': Review.objects.count(),
        'new_orders_this_week': Order.objects.filter(date__gte=start_of_week, status='new').count(),
        'total_pending_reviews': Review.objects.filter(is_published=False).count(),
    }

    return render(request, 'admin_panel/dashboard.html', {
        'stats': stats,
        'recent_orders': recent_orders
    })

@user_passes_test(lambda u: u.is_staff)
def profile_admin(request):
    """Admin profile/dashboard summary."""
    context = {
        'orders': Order.objects.select_related('master', 'user')
                               .prefetch_related('services')
                               .order_by('-date', '-time')[:5],
        'masters': Master.objects.all()[:4],
        'services': Service.objects.all()[:6],
        'reviews': Review.objects.select_related('master')
                               .order_by('-created_at')[:5]
    }
    return render(request, 'core/profile_admin.html', context)


# ADMIN ORDER MANAGEMENT VIEWS
@user_passes_test(lambda u: u.is_staff)
def admin_orders_list(request):
    """Redirects to the comprehensive admin order list."""
    return redirect('order_list_admin')

@user_passes_test(lambda u: u.is_staff)
def admin_order_detail(request, order_id):
    """Детали заказа (админ)"""
    order = get_object_or_404(
        Order.objects.select_related('master', 'user').prefetch_related('services'),
        pk=order_id
    )
    return render(request, 'admin_panel/orders/detail.html', {
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
        form.fields['master'].queryset = Master.objects.filter(is_active=True)

    return render(request, 'admin_panel/orders/edit.html', {
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
        return redirect('order_list_admin')

    return render(request, 'admin_panel/orders/confirm_delete.html', {
        'order': order
    })

@user_passes_test(lambda u: u.is_staff)
def order_list_admin(request):
    """Список всех заказов для администратора с пагинацией и поиском"""
    query = Q()
    search = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    master_filter = request.GET.get('master', '')
    date_filter = request.GET.get('date', '')

    if search:
        query &= (
            Q(client_name__icontains=search) |
            Q(phone__icontains=search) |
            Q(comment__icontains=search) |
            Q(master__name__icontains=search) |
            Q(services__name__icontains=search)
        )
    if status_filter:
        query &= Q(status=status_filter)
    if master_filter:
        query &= Q(master__id=master_filter)
    if date_filter:
        try:
            parsed_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
            query &= Q(date=parsed_date)
        except ValueError:
            messages.error(request, 'Неверный формат даты. Используйте ГГГГ-ММ-ДД.')

    orders = Order.objects.filter(query)\
                          .select_related('master', 'user')\
                          .prefetch_related('services')\
                          .distinct()\
                          .order_by('-date', '-time')

    paginator = Paginator(orders, 25)
    page_number = request.GET.get('page')

    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    masters = Master.objects.all()

    return render(request, 'admin_panel/orders/list.html', {
        'page_obj': page_obj,
        'orders': page_obj.object_list,
        'search': search,
        'status_filter': status_filter,
        'master_filter': master_filter,
        'date_filter': date_filter,
        'masters': masters,
        'all_statuses': Order.STATUS_CHOICES
    })

@user_passes_test(lambda u: u.is_staff)
def order_update_status(request, pk):
    order = get_object_or_404(Order, pk=pk)
    
    if request.method == 'POST':
        form = OrderStatusForm(request.POST, instance=order)
        if form.is_valid():
            try:
                new_status = form.cleaned_data['status']
                order.status = new_status
                order.save()
                
                messages.success(request, f'Статус заказа #{order.id} успешно изменен на "{order.get_status_display()}"')
                return redirect('admin_order_detail', order_id=order.id)
                
            except Exception as e:
                messages.error(request, f'Ошибка при сохранении: {str(e)}')
        else:
            messages.error(request, 'Ошибка при изменении статуса. Пожалуйста, проверьте форму.')
    else:
        form = OrderStatusForm(instance=order)
    
    return render(request, 'admin_panel/orders/update_status.html', {
        'form': form,
        'order': order
    })


# MASTER MANAGEMENT VIEWS
@user_passes_test(lambda u: u.is_staff)
def master_list(request):
    """Список мастеров для администратора"""
    masters = Master.objects.all().order_by('name')
    return render(request, 'admin_panel/masters/list.html', {'masters': masters})

@user_passes_test(lambda u: u.is_staff)
def master_create(request):
    """Создание мастера"""
    if request.method == 'POST':
        form = MasterForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Мастер успешно добавлен!')
            return redirect('master_list')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'Ошибка в поле "{form.fields[field].label}": {error}')
    else:
        form = MasterForm()

    return render(request, 'admin_panel/masters/create.html', {'form': form})

@user_passes_test(lambda u: u.is_staff)
def master_edit(request, pk):
    master = get_object_or_404(Master, pk=pk)
    
    if request.method == 'POST':
        form = MasterForm(request.POST, request.FILES, instance=master)
        if form.is_valid():
            master = form.save(commit=False)
            master.save()
            form.save_m2m()  # Важно для сохранения ManyToMany отношений
            messages.success(request, 'Мастер успешно обновлен!')
            return redirect('master_list')
    else:
        form = MasterForm(instance=master)
    
    return render(request, 'admin_panel/masters/edit.html', {
        'form': form,
        'master': master
    })


@user_passes_test(lambda u: u.is_staff)
def master_delete(request, pk):
    master = get_object_or_404(Master, pk=pk)

    if request.method == 'POST':
        try:
            master_name = master.name
            master.delete()
            messages.success(request, f'Мастер "{master_name}" успешно удалён!')
            return redirect('master_list')
        except Exception as e:
            messages.error(request, f'Ошибка при удалении мастера: {str(e)}')
            return redirect('master_list')

    return render(request, 'admin_panel/masters/confirm_delete.html', {'master': master})

@user_passes_test(lambda u: u.is_staff)
def master_delete_service(request, master_pk, service_pk):
    master = get_object_or_404(Master, pk=master_pk)
    service = get_object_or_404(Service, pk=service_pk)
    
    if request.method == 'POST':
        try:
            master.services.remove(service)
            messages.success(request, f'Услуга "{service.name}" удалена у мастера {master.name}')
        except Exception as e:
            messages.error(request, f'Ошибка: {str(e)}')
    
    return redirect('admin_master_edit', pk=master_pk)

def get_master_services(request, master_id):
    """AJAX endpoint to get services for a specific master."""
    master = get_object_or_404(Master, id=master_id)
    services = master.services.filter(is_active=True).values('id', 'name', 'price', 'duration')
    return JsonResponse(list(services), safe=False)


# SERVICE MANAGEMENT VIEWS
@user_passes_test(lambda u: u.is_staff)
def service_list(request):
    services = Service.objects.all().order_by('name')
    return render(request, 'admin_panel/services/list.html', {'services': services})

@user_passes_test(lambda u: u.is_staff)
def service_create(request):
    """Создание услуги"""
    if request.method == 'POST':
        form = ServiceForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                service = form.save()
                messages.success(request, f'Услуга "{service.name}" успешно создана!')
                return redirect('service_list')
            except Exception as e:
                messages.error(request, f'Ошибка при создании услуги: {str(e)}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{form.fields[field].label}: {error}')
    else:
        form = ServiceForm()

    return render(request, 'admin_panel/services/create.html', {
        'form': form,
    })

@user_passes_test(lambda u: u.is_staff)
def service_edit(request, pk):
    """Редактирование услуги"""
    service = get_object_or_404(Service, pk=pk)

    if request.method == 'POST':
        form = ServiceForm(request.POST, request.FILES, instance=service)
        if form.is_valid():
            try:
                service = form.save()
                messages.success(request, f'Услуга "{service.name}" успешно обновлена!')
                return redirect('service_list')
            except Exception as e:
                messages.error(request, f'Ошибка при обновлении услуги: {str(e)}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'Поле "{form.fields[field].label}": {error}')
    else:
        form = ServiceForm(instance=service)

    return render(request, 'admin_panel/services/edit.html', {
        'form': form,
        'service': service
    })

@user_passes_test(lambda u: u.is_staff)
def service_delete(request, pk):
    """Удаление услуги"""
    service = get_object_or_404(Service, pk=pk)

    if request.method == 'POST':
        try:
            service_name = service.name
            service.delete()
            messages.success(request, f'Услуга "{service_name}" успешно удалена!')
            return redirect('service_list')
        except Exception as e:
            messages.error(request, f'Ошибка при удалении услуги: {str(e)}')
            return redirect('service_list')

    return render(request, 'admin_panel/services/confirm_delete.html', {
        'service': service
    })

# REVIEW MANAGEMENT VIEWS
@login_required
def add_review(request):
    """Добавление отзыва пользователем"""
    if request.method == 'POST':
        form = ReviewForm(request.POST, request.FILES)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.save()
            messages.success(request, 'Ваш отзыв успешно добавлен и ожидает модерации!')
            return redirect('review_list')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме отзыва.')
    else:
        form = ReviewForm()
    
    return render(request, 'reviews/add_review.html', {
        'form': form,
        'masters': Master.objects.filter(is_active=True)
    })

def review_list(request):
    """Список опубликованных отзывов для всех пользователей."""
    reviews = Review.objects.filter(is_published=True)\
                             .select_related('master', 'user')\
                             .order_by('-created_at')

    rating = request.GET.get('rating')
    if rating:
        reviews = reviews.filter(rating=rating)

    paginator = Paginator(reviews, 10)
    page_number = request.GET.get('page')

    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    return render(request, 'reviews/list.html', {
        'page_obj': page_obj,
        'total_reviews': paginator.count,
    })

def review_detail(request, pk):
    """Детали отзыва (публичный, только опубликованные)"""
    review = get_object_or_404(
        Review.objects.select_related('master', 'user'),
        pk=pk,
        is_published=True
    )
    return render(request, 'reviews/detail.html', {
        'review': review
    })

def review_edit(request, pk):
    review = get_object_or_404(Review, pk=pk)
    if request.method == 'POST':
        form = ReviewForm(request.POST, request.FILES, instance=review)
        if form.is_valid():
            form.save()
            return redirect('admin_review_list')  # Теперь это имя существует
    else:
        form = ReviewForm(instance=review)
    
    return render(request, 'admin_panel/reviews/edit.html', {
        'form': form,
        'review': review
    })


@user_passes_test(lambda u: u.is_staff)
def review_list_admin(request):
    """Список всех отзывов для администратора с пагинацией и поиском."""
    query = Q()
    rating_filter = request.GET.get('rating', '')
    status_filter = request.GET.get('status', '')
    ai_status_filter = request.GET.get('ai_status', '')

    if rating_filter:
        query &= Q(rating=rating_filter)
    if status_filter == 'published':
        query &= Q(is_published=True)
    elif status_filter == 'unpublished':
        query &= Q(is_published=False)
    
    if ai_status_filter == 'approved':
        query &= Q(ai_checked_status='ai_checked_true')
    elif ai_status_filter == 'rejected':
        query &= Q(ai_checked_status='ai_cancelled')
    elif ai_status_filter == 'not_checked':
        query &= Q(ai_checked_status='pending') # Assuming 'pending' means 'not checked'

    reviews = Review.objects.filter(query)\
                             .select_related('master')\
                             .order_by('-created_at')

    paginator = Paginator(reviews, 25)
    page_number = request.GET.get('page')

    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    return render(request, 'admin_panel/reviews/list.html', {
        'page_obj': page_obj,
        'total_reviews': reviews.count(), # Total count without filters
        'selected_rating': rating_filter,
        'selected_status': status_filter,
        'selected_ai_status': ai_status_filter,
    })

@user_passes_test(lambda u: u.is_staff)
def review_toggle_publish(request, pk):
    """Админ: переключение статуса публикации отзыва."""
    review = get_object_or_404(Review, pk=pk)
    if request.method == 'POST':
        review.is_published = not review.is_published
        review.save()
        messages.success(request, f'Статус публикации отзыва изменен на {"Опубликован" if review.is_published else "Скрыт"}.')
        return redirect('admin_review_list')  # Исправлено имя URL
    return render(request, 'admin_panel/reviews/toggle_publish_confirm.html', {'review': review})


@user_passes_test(lambda u: u.is_staff)
def review_create_admin(request):
    """Создание отзыва (админ)"""
    if request.method == 'POST':
        form = ReviewForm(request.POST, request.FILES)
        if form.is_valid():
            review = form.save(commit=False)
            if not review.user and request.user.is_staff:
                review.user = request.user
            review.save()
            messages.success(request, 'Отзыв успешно добавлен!')
            return redirect('review_list_admin')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        form = ReviewForm()

    return render(request, 'admin_panel/reviews/create.html', {'form': form})

@user_passes_test(lambda u: u.is_staff)
def review_delete(request, pk):
    review = get_object_or_404(Review, pk=pk)
    if request.method == 'POST':
        review.delete()
        messages.success(request, 'Отзыв был успешно удален.')
        return redirect('admin_review_list')  # Используем правильное имя URL
    return render(request, 'admin_panel/reviews/confirm_delete.html', {'review': review})

@login_required
def delete_review(request, review_id):
    """Удаление отзыва пользователем"""
    review = get_object_or_404(Review, id=review_id)

    if request.user.is_staff or (review.user and request.user == review.user):
        review.delete()
        messages.success(request, 'Отзыв успешно удален.')
    else:
        messages.error(request, 'У вас нет прав для удаления этого отзыва.')

    return redirect('review_list')

def get_master_services(request, master_id):
    """AJAX endpoint to get services for a specific master."""
    master = get_object_or_404(Master, id=master_id)
    services = master.services.filter(is_active=True).values('id', 'name', 'price', 'duration')
    return JsonResponse(list(services), safe=False)

def services_view(request):
    """Страница всех услуг (public view)"""
    popular_services = Service.objects.filter(is_popular=True, is_active=True).order_by('name')
    services = Service.objects.filter(is_active=True).exclude(is_popular=True).order_by('name')

    return render(request, 'core/services.html', {
        'popular_services': popular_services,
        'services': services
    })


def test_telegram(request):
    if send_telegram_message("Тестовое сообщение от бота"):
        return HttpResponse("Сообщение отправлено успешно")
    return HttpResponse("Ошибка отправки сообщения", status=500)