from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse
from django.utils import timezone
from django.contrib import messages
from django.db.models import Q
from django.db import transaction
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse, HttpResponse, Http404 # Добавлен Http404
from django.core.exceptions import ValidationError
from .models import Master, Service, Order, Review
from .forms import OrderForm, OrderSearchForm, ReviewForm, MasterForm, ServiceForm, OrderStatusForm, ReviewPublishForm, RegisterForm, LoginForm
from datetime import datetime, timedelta, date
from .telegram_bot import send_telegram_message
from django.contrib.auth import login, logout, authenticate
from django.core.mail import send_mail
import logging
from django.contrib.auth import views as auth_views
from django.contrib.auth.forms import SetPasswordForm
from django.urls import reverse_lazy
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session

# Импорты для Class-Based Views
from django.views import View
from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView, DeleteView, FormView, RedirectView
from django.contrib.auth.mixins import UserPassesTestMixin # LoginRequiredMixin удален из импорта для некоторых классов


User = get_user_model()
logger = logging.getLogger(__name__)

# Инициализационные функции (Остаются без изменений)
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


# --- Основные представления (Public/User-facing) ---

# Рефакторинг: Landing (Главная страница) из FBV в TemplateView
class LandingView(TemplateView):
    template_name = 'landing.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        init_masters()
        init_services()
        context.update({
            'masters': Master.objects.filter(is_active=True),
            'services': Service.objects.filter(is_active=True)[:6],
            'reviews': Review.objects.filter(is_published=True).order_by('-created_at')[:6]
        })
        context['form'] = OrderForm()
        return context

# НОВОЕ ПРЕДСТАВЛЕНИЕ: Для обработки POST-запросов формы с главной страницы
class LandingOrderCreateView(CreateView):
    model = Order
    form_class = OrderForm
    success_url = reverse_lazy('thanks')

    def get_initial(self):
        initial = super().get_initial()
        if self.request.user.is_authenticated:
            initial.update({
                'client_name': self.request.user.get_full_name() or self.request.user.username,
                'phone': self.request.user.username,
                'email': self.request.user.email
            })
        return initial

    def form_valid(self, form):
        messages.success(self.request, 'Запись успешно создана! Ожидайте звонка для подтверждения.')
        order = form.save(commit=False)
        
        if self.request.user.is_authenticated:
            order.user = self.request.user
            if not order.client_name:
                order.client_name = self.request.user.get_full_name() or self.request.user.username
            if not order.phone:
                order.phone = self.request.user.username
        
        master = order.master
        selected_services = form.cleaned_data['services']
        master_services = master.services.all()
        
        invalid_services = [s for s in selected_services if s not in master_services]
        if invalid_services:
            messages.error(self.request, f"Мастер {master.name} не предоставляет выбранные услуги")
            return self.form_invalid(form) 

        order.save()
        form.save_m2m()
        
        if not self.request.user.is_authenticated:
            anonymous_orders = self.request.session.get('anonymous_orders', [])
            anonymous_orders.append(order.id)
            self.request.session['anonymous_orders'] = anonymous_orders
            self.request.session['show_my_orders'] = True
            self.request.session.modified = True
        
        self.request.session['last_order_id'] = order.id
        return super().form_valid(form)

    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"Ошибка в поле '{form.fields[field].label}': {error}")
        return redirect('landing')


# Рефакторинг: thanks из FBV в TemplateView
class ThanksView(TemplateView):
    template_name = 'thanks.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order_id = self.request.session.get('last_order_id')
        if order_id:
            order = get_object_or_404(Order, id=order_id)
            context['order'] = order
            if 'last_order_id' in self.request.session:
                del self.request.session['last_order_id']
        return context

def get_anonymous_orders(request):
    """Получает заказы анонимного пользователя из сессии"""
    if not request.user.is_authenticated and 'anonymous_orders' in request.session:
        return Order.objects.filter(id__in=request.session['anonymous_orders'])
    return Order.objects.none()

def has_order_access(request, order):
    """Проверка прав доступа к заказу"""
    if request.user.is_authenticated:
        return request.user.is_staff or order.user == request.user
    else:
        return 'anonymous_orders' in request.session and order.id in request.session['anonymous_orders']

# Рефакторинг: orders_list из FBV в OrdersListView (бывшее UserOrderListView)
class OrdersListView(ListView): # <<< УДАЛЕН LoginRequiredMixin
    model = Order
    template_name = 'orders/list.html'
    context_object_name = 'orders'
    paginate_by = 10
    ordering = ['-date', '-time']

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_authenticated:
            if not self.request.user.is_staff:
                query_filter = Q(user=self.request.user) | Q(phone=self.request.user.username)
                queryset = queryset.filter(query_filter)
        else:
            queryset = get_anonymous_orders(self.request)

        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(client_name__icontains=search) |
                Q(phone__icontains=search) |
                Q(comment__icontains=search) |
                Q(master__name__icontains=search) |
                Q(services__name__icontains=search)
            )
        return queryset.select_related('master', 'user').prefetch_related('services').distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if not self.request.user.is_authenticated:
            self.request.session['show_my_orders'] = bool(context['orders'].exists())
        context.update({
            'search': self.request.GET.get('search', ''),
            'user_authenticated': self.request.user.is_authenticated
        })
        return context

# Рефакторинг: order_detail из FBV в OrderDetailView (бывшее UserOrderDetailView)
class OrderDetailView(DetailView): # <<< УДАЛЕН LoginRequiredMixin
    model = Order
    template_name = 'orders/detail.html'
    context_object_name = 'order'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if not has_order_access(self.request, obj):
            # messages.error(self.request, 'У вас нет доступа к этому заказу') # Сообщения не покажутся на 404
            raise Http404("No access to this order") # Вызов 404, если нет доступа
        return obj
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order = context['order']
        context.update({
            'total_price': order.get_total_price(),
            'can_edit': has_order_access(self.request, order)
        })
        return context

# Рефакторинг: order_create из FBV в OrderCreateView (бывшее UserOrderCreateView)
class OrderCreateView(CreateView): # Этот класс не требовал LoginRequiredMixin
    model = Order
    form_class = OrderForm
    template_name = 'orders/create.html'
    success_url = reverse_lazy('thanks')

    def get_initial(self):
        initial = super().get_initial()
        if self.request.user.is_authenticated:
            initial.update({
                'client_name': self.request.user.get_full_name() or self.request.user.username,
                'phone': self.request.user.username,
                'email': self.request.user.email
            })
        return initial
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'masters': Master.objects.filter(is_active=True),
            'user_authenticated': self.request.user.is_authenticated
        })
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Запись успешно создана! Ожидайте звонка для подтверждения.')
        order = form.save(commit=False)
        
        if self.request.user.is_authenticated:
            order.user = self.request.user
            if not order.client_name:
                order.client_name = self.request.user.get_full_name() or self.request.user.username
            if not order.phone:
                order.phone = self.request.user.username
        
        master = order.master
        selected_services = form.cleaned_data['services']
        master_services = master.services.all()
        
        invalid_services = [s for s in selected_services if s not in master_services]
        if invalid_services:
            messages.error(self.request, f"Мастер {master.name} не предоставляет выбранные услуги")
            return self.form_invalid(form) 
        
        order.save()
        form.save_m2m()
        
        if not self.request.user.is_authenticated:
            anonymous_orders = self.request.session.get('anonymous_orders', [])
            anonymous_orders.append(order.id)
            self.request.session['anonymous_orders'] = anonymous_orders
            self.request.session['show_my_orders'] = True
            self.request.session.modified = True
        
        self.request.session['last_order_id'] = order.id
        return super().form_valid(form)


# Рефакторинг: create_review из FBV в ReviewCreateView
class ReviewCreateView(CreateView): # <<< УДАЛЕН LoginRequiredMixin, если вы хотите разрешить анонимные отзывы.
                                     # НО: Если отзывы могут писать ТОЛЬКО авторизованные пользователи, оставьте.
                                     # Судя по задумке, авторизация для отзывов может быть обязательна.
                                     # Если анонимные отзывы не нужны, то LoginRequiredMixin здесь должен быть.
    model = Review
    form_class = ReviewForm
    template_name = 'reviews/add_review.html'
    success_url = reverse_lazy('review_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['masters'] = Master.objects.filter(is_active=True)
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Ваш отзыв успешно добавлен и ожидает модерации!')
        review = form.save(commit=False)
        # Если пользователь не авторизован, можно оставить user=None или как-то иначе помечать
        if self.request.user.is_authenticated:
            review.user = self.request.user
        else:
            # Если разрешены анонимные отзывы, но требуется имя, можно взять из формы
            # review.user = None
            pass # Если user может быть null в модели
        review.save()
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Пожалуйста, исправьте ошибки в форме отзыва.')
        return super().form_invalid(form)


# --- Существующие Классовые представления, которые не были FBV в задании, но ранее были конвертированы ---

# services_view остается функциональным представлением
def services_view(request):
    """Страница всех услуг (public view)"""
    popular_services = Service.objects.filter(is_popular=True, is_active=True).order_by('name')
    services = Service.objects.filter(is_active=True).exclude(is_popular=True).order_by('name')

    return render(request, 'core/services.html', {
        'popular_services': popular_services,
        'services': services
    })

# test_telegram остается функциональным представлением
def test_telegram(request):
    if send_telegram_message("Тестовое сообщение от бота"):
        return HttpResponse("Сообщение отправлено успешно")
    return HttpResponse("Ошибка отправки сообщения", status=500)

# register_view остается функциональным представлением
def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password1'])
            user.save()
            login(request, user)
            messages.success(request, 'Регистрация успешна!')
            return redirect('landing')
        else:
            print("Ошибки формы:", form.errors)
            messages.error(request, 'Исправьте ошибки в форме')
    else:
        form = RegisterForm()
    return render(request, 'core/register.html', {'form': form})

# login_view остается функциональным представлением
def login_view(request):
    if request.method == 'POST':
        form = LoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            
            if not form.cleaned_data['remember_me']:
                request.session.set_expiry(0)
            
            messages.success(request, f'Добро пожаловать, {user.username}!')
            next_url = request.GET.get('next', settings.LOGIN_REDIRECT_URL)
            return redirect(next_url)
    else:
        form = LoginForm()
    return render(request, 'core/login.html', {'form': form})

# logout_view остается функциональным представлением
def logout_view(request):
    logout(request)
    messages.info(request, 'Вы успешно вышли из системы.')
    return redirect('landing')  

# test_email остается функциональным представлением
def test_email(request):
    send_mail(
        'Тестовое письмо',
        'Проверка отправки почты.',
        'from@example.com', # Замените на реальный отправитель
        ['to@example.com'], # Замените на реальный получатель
        fail_silently=False,
    )
    return HttpResponse("Проверьте почту или консоль сервера")

# CustomPasswordResetConfirmView (Классовое, уже унаследовано от auth_views.PasswordResetConfirmView)
class CustomPasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    template_name = 'registration/password_reset_confirm.html'
    form_class = SetPasswordForm
    success_url = reverse_lazy('password_reset_complete')

    def form_valid(self, form):
        logger.info("Password reset form is valid")
        response = super().form_valid(form)
        user = form.save()
        logger.info(f"Password changed for user {user.username}")
        return response

# Admin and other views that were already class-based and remain so (renamed if necessary)

class UserOrderUpdateView(UserPassesTestMixin, UpdateView): # <<< УДАЛЕН LoginRequiredMixin
    model = Order
    form_class = OrderForm
    template_name = 'orders/edit.html'
    context_object_name = 'order'

    def test_func(self):
        obj = self.get_object() # get_object() вызовет 404 если объект не найден
        return has_order_access(self.request, obj) # Проверяем доступ с помощью вашей функции

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['master'].queryset = Master.objects.filter(is_active=True)
        if self.object.master:
            form.fields['services'].queryset = self.object.master.services.filter(is_active=True)
        return form

    def form_valid(self, form):
        messages.success(self.request, 'Запись успешно обновлена!')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('order_detail', kwargs={'pk': self.object.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_edit'] = has_order_access(self.request, context['order'])
        return context

class UserOrderDeleteView(UserPassesTestMixin, DeleteView): # <<< УДАЛЕН LoginRequiredMixin
    model = Order
    template_name = 'orders/confirm_delete.html'
    context_object_name = 'order'
    success_url = reverse_lazy('order_list')

    def test_func(self):
        obj = self.get_object() # get_object() вызовет 404 если объект не найден
        return has_order_access(self.request, obj)

    def post(self, request, *args, **kwargs):
        order = self.get_object()
        if not self.request.user.is_authenticated and 'anonymous_orders' in self.request.session:
            self.request.session['anonymous_orders'] = [
                oid for oid in self.request.session['anonymous_orders'] if oid != order.id
            ]
            self.request.session.modified = True
        
        messages.success(self.request, 'Запись успешно удалена!')
        return super().post(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_delete'] = has_order_access(self.request, context['order'])
        return context

# admin_panel остается функциональным представлением из-за сложной логики статистики (по вашему заданию не рефакторится)
@user_passes_test(lambda u: u.is_staff)
def admin_panel(request):
    """
    Главная панель администратора.
    Включает статистику и последние новые заказы для быстрого обзора.
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

# profile_admin остается функциональным представлением (не входило в задание на рефакторинг)
@user_passes_test(lambda u: u.is_staff)
def profile_admin(request):
    """Сводка профиля/панели администратора."""
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


# УПРАВЛЕНИЕ ЗАКАЗАМИ АДМИНИСТРАТОРА

class AdminOrderRedirectView(UserPassesTestMixin, RedirectView):
    pattern_name = 'admin_order_list'
    
    def test_func(self):
        return self.request.user.is_staff

class AdminOrderDetailView(UserPassesTestMixin, DetailView):
    model = Order
    template_name = 'admin_panel/orders/detail.html'
    context_object_name = 'order'
    pk_url_kwarg = 'order_id'

    def test_func(self):
        return self.request.user.is_staff
    
    def get_queryset(self):
        return super().get_queryset().select_related('master', 'user').prefetch_related('services')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_price'] = context['order'].total_price()
        return context

class AdminOrderUpdateView(UserPassesTestMixin, UpdateView):
    model = Order
    form_class = OrderForm
    template_name = 'admin_panel/orders/edit.html'
    context_object_name = 'order'
    pk_url_kwarg = 'order_id'

    def test_func(self):
        return self.request.user.is_staff

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['master'].queryset = Master.objects.filter(is_active=True)
        return form

    def form_valid(self, form):
        messages.success(self.request, 'Запись успешно обновлена!')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('admin_order_detail', kwargs={'order_id': self.object.pk})

class AdminOrderDeleteView(UserPassesTestMixin, DeleteView):
    model = Order
    template_name = 'admin_panel/orders/confirm_delete.html'
    context_object_name = 'order'
    pk_url_kwarg = 'order_id'
    success_url = reverse_lazy('admin_order_list')

    def test_func(self):
        return self.request.user.is_staff

    def form_valid(self, form):
        messages.success(self.request, 'Запись успешно удалена!')
        return super().form_valid(form)

class AdminOrderListView(UserPassesTestMixin, ListView):
    model = Order
    template_name = 'admin_panel/orders/list.html'
    context_object_name = 'orders'
    paginate_by = 25

    def test_func(self):
        return self.request.user.is_staff

    def get_queryset(self):
        queryset = super().get_queryset()
        query = Q()

        search = self.request.GET.get('search', '')
        status_filter = self.request.GET.get('status', '')
        master_filter = self.request.GET.get('master', '')
        date_filter = self.request.GET.get('date', '')

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
                messages.error(self.request, 'Неверный формат даты. Используйте ГГГГ-ММ-ДД.')
        
        queryset = queryset.filter(query)\
                          .select_related('master', 'user')\
                          .prefetch_related('services')\
                          .distinct()\
                          .order_by('-date', '-time')
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'search': self.request.GET.get('search', ''),
            'status_filter': self.request.GET.get('status', ''),
            'master_filter': self.request.GET.get('master', ''),
            'date_filter': self.request.GET.get('date', ''),
            'masters': Master.objects.all(),
            'all_statuses': Order.STATUS_CHOICES
        })
        return context

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


# УПРАВЛЕНИЕ МАСТЕРАМИ

class MasterListView(UserPassesTestMixin, ListView):
    model = Master
    template_name = 'admin_panel/masters/list.html'
    context_object_name = 'masters'

    def test_func(self):
        return self.request.user.is_staff

    def get_queryset(self):
        return super().get_queryset().order_by('name')

class MasterCreateView(UserPassesTestMixin, CreateView):
    model = Master
    form_class = MasterForm
    template_name = 'admin_panel/masters/create.html'
    success_url = reverse_lazy('master_list')

    def test_func(self):
        return self.request.user.is_staff

    def form_valid(self, form):
        messages.success(self.request, 'Мастер успешно добавлен!')
        return super().form_valid(form)

    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f'Ошибка в поле "{form.fields[field].label}": {error}')
        return super().form_invalid(form)

class MasterUpdateView(UserPassesTestMixin, UpdateView):
    model = Master
    form_class = MasterForm
    template_name = 'admin_panel/masters/edit.html'
    context_object_name = 'master'
    success_url = reverse_lazy('master_list')

    def test_func(self):
        return self.request.user.is_staff

    def form_valid(self, form):
        master = form.save(commit=False)
        master.save()
        form.save_m2m()
        messages.success(self.request, 'Мастер успешно обновлен!')
        return super().form_valid(form)

class MasterDeleteView(UserPassesTestMixin, DeleteView):
    model = Master
    template_name = 'admin_panel/masters/confirm_delete.html'
    context_object_name = 'master'
    success_url = reverse_lazy('master_list')

    def test_func(self):
        return self.request.user.is_staff

    def form_valid(self, form):
        try:
            master_name = self.object.name
            messages.success(self.request, f'Мастер "{master_name}" успешно удалён!')
            return super().form_valid(form)
        except Exception as e:
            messages.error(self.request, f'Ошибка при удалении мастера: {str(e)}')
            return redirect('master_list')

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
    
    return redirect('master_edit', pk=master_pk)

def get_master_services(request, master_id):
    """AJAX endpoint to get services for a specific master."""
    master = get_object_or_404(Master, id=master_id)
    services = master.services.filter(is_active=True).values('id', 'name', 'price', 'duration')
    return JsonResponse(list(services), safe=False)


# УПРАВЛЕНИЕ УСЛУГАМИ

class ServiceListView(UserPassesTestMixin, ListView):
    model = Service
    template_name = 'admin_panel/services/list.html'
    context_object_name = 'services'

    def test_func(self):
        return self.request.user.is_staff

    def get_queryset(self):
        return super().get_queryset().order_by('name')

class ServiceCreateView(UserPassesTestMixin, CreateView):
    model = Service
    form_class = ServiceForm
    template_name = 'admin_panel/services/create.html'
    success_url = reverse_lazy('service_list')

    def test_func(self):
        return self.request.user.is_staff

    def form_valid(self, form):
        try:
            service = form.save()
            messages.success(self.request, f'Услуга "{service.name}" успешно создана!')
            return super().form_valid(form)
        except Exception as e:
            messages.error(self.request, f'Ошибка при создании услуги: {str(e)}')
            return self.form_invalid(form)

    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f'{form.fields[field].label}: {error}')
        return super().form_invalid(form)

class ServiceUpdateView(UserPassesTestMixin, UpdateView):
    model = Service
    form_class = ServiceForm
    template_name = 'admin_panel/services/edit.html'
    context_object_name = 'service'
    success_url = reverse_lazy('service_list')

    def test_func(self):
        return self.request.user.is_staff

    def form_valid(self, form):
        try:
            service = form.save()
            messages.success(self.request, f'Услуга "{service.name}" успешно обновлена!')
            return super().form_valid(form)
        except Exception as e:
            messages.error(self.request, f'Ошибка при обновлении услуги: {str(e)}')
            return self.form_invalid(form)

    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f'Поле "{form.fields[field].label}": {error}')
        return super().form_invalid(form)

class ServiceDeleteView(UserPassesTestMixin, DeleteView):
    model = Service
    template_name = 'admin_panel/services/confirm_delete.html'
    context_object_name = 'service'
    success_url = reverse_lazy('service_list')

    def test_func(self):
        return self.request.user.is_staff

    def form_valid(self, form):
        try:
            service_name = self.object.name
            messages.success(self.request, f'Услуга "{service_name}" успешно удалена!')
            return super().form_valid(form)
        except Exception as e:
            messages.error(self.request, f'Ошибка при удалении услуги: {str(e)}')
            return redirect('service_list')


# УПРАВЛЕНИЕ ОТЗЫВАМИ

class PublicReviewListView(ListView):
    model = Review
    template_name = 'reviews/list.html'
    context_object_name = 'reviews'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset().filter(is_published=True)\
                             .select_related('master', 'user')\
                             .order_by('-created_at')
        rating = self.request.GET.get('rating')
        if rating:
            queryset = queryset.filter(rating=rating)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_reviews'] = self.get_queryset().count()
        context.update({
            'selected_rating': self.request.GET.get('rating', ''),
            'selected_status': self.request.GET.get('status', ''),
            'selected_ai_status': self.request.GET.get('ai_status', ''),
        })
        return context

class PublicReviewDetailView(DetailView):
    model = Review
    template_name = 'reviews/detail.html'
    context_object_name = 'review'

    def get_queryset(self):
        return super().get_queryset().filter(is_published=True).select_related('master', 'user')

class AdminReviewUpdateView(UserPassesTestMixin, UpdateView):
    model = Review
    form_class = ReviewForm
    template_name = 'admin_panel/reviews/edit.html'
    context_object_name = 'review'
    success_url = reverse_lazy('admin_review_list')

    def test_func(self):
        return self.request.user.is_staff

class AdminReviewListView(UserPassesTestMixin, ListView):
    model = Review
    template_name = 'admin_panel/reviews/list.html'
    context_object_name = 'reviews'
    paginate_by = 25

    def test_func(self):
        return self.request.user.is_staff

    def get_queryset(self):
        queryset = super().get_queryset()
        query = Q()

        rating_filter = self.request.GET.get('rating', '')
        status_filter = self.request.GET.get('status', '')
        ai_status_filter = self.request.GET.get('ai_status', '')

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
            query &= Q(ai_checked_status='pending')

        return queryset.filter(query)\
                             .select_related('master')\
                             .order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_reviews'] = self.get_queryset().count()
        context.update({
            'selected_rating': self.request.GET.get('rating', ''),
            'selected_status': self.request.GET.get('status', ''),
            'selected_ai_status': self.request.GET.get('ai_status', ''),
        })
        return context

class AdminReviewTogglePublishView(UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_staff

    def post(self, request, pk, *args, **kwargs):
        review = get_object_or_404(Review, pk=pk)
        review.is_published = not review.is_published
        review.save()
        messages.success(request, f'Статус публикации отзыва изменен на {"Опубликован" if review.is_published else "Скрыт"}.')
        return redirect('admin_review_list')

    def get(self, request, pk, *args, **kwargs):
        review = get_object_or_404(Review, pk=pk)
        return render(request, 'admin_panel/reviews/toggle_publish_confirm.html', {'review': review})

class AdminReviewCreateView(UserPassesTestMixin, CreateView):
    model = Review
    form_class = ReviewForm
    template_name = 'admin_panel/reviews/create.html'
    success_url = reverse_lazy('admin_review_list')

    def test_func(self):
        return self.request.user.is_staff

    def form_valid(self, form):
        review = form.save(commit=False)
        if not review.user and self.request.user.is_staff:
            review.user = self.request.user
        review.save()
        messages.success(self.request, 'Отзыв успешно добавлен!')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Пожалуйста, исправьте ошибки в форме.')
        return super().form_invalid(form)

class AdminReviewDeleteView(UserPassesTestMixin, DeleteView):
    model = Review
    template_name = 'admin_panel/reviews/confirm_delete.html'
    context_object_name = 'review'
    success_url = reverse_lazy('admin_review_list')

    def test_func(self):
        return self.request.user.is_staff

    def form_valid(self, form):
        messages.success(self.request, 'Отзыв был успешно удален.')
        return super().form_valid(form)

class UserReviewDeleteView(UserPassesTestMixin, DeleteView): 
    model = Review
    template_name = 'reviews/confirm_delete.html'
    context_object_name = 'review'
    success_url = reverse_lazy('review_list')

    def test_func(self): # Добавлен test_func для UserPassesTestMixin
        obj = self.get_object() # get_object() вызовет 404 если объект не найден
        return has_order_access(self.request, obj) # Использование вашей функции доступа

    def form_valid(self, form):
        messages.success(self.request, 'Отзыв успешно удален.')
        return super().form_valid(form)