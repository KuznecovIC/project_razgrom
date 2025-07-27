from django.contrib.auth import views as auth_views
from django.urls import path, include, reverse_lazy
from core import views
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import user_passes_test
from django.contrib import admin
from django.core.mail import send_mail
from django.http import HttpResponse
import logging

logger = logging.getLogger(__name__)

def test_email(request):
    send_mail(
        'Тест Яндекс.Почты',
        'Проверка отправки писем',
        settings.EMAIL_HOST_USER,
        ['получатель@example.com'],
    )
    return HttpResponse("Проверьте почту!")

urlpatterns = [
    # Админка
    path('admin/', admin.site.urls),
    
    # Тест email
    path('test-email/', test_email),
    
    # Основные маршруты
    path('', views.index, name='home'),
    path('landing/', views.landing, name='landing'),
    path('thanks/', views.thanks, name='thanks'),
    path('services/', views.services_view, name='services'),

    # Аутентификация
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Сброс пароля
    path('password-reset/', auth_views.PasswordResetView.as_view(
    template_name='registration/password_reset.html',
    email_template_name='registration/password_reset_email.html',
    subject_template_name='registration/password_reset_subject.txt',
    success_url=reverse_lazy('password_reset_done')
), name='password_reset'),
    
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
    template_name='registration/password_reset_done.html'
), name='password_reset_done'),
    
    path('reset/<uidb64>/<token>/', 
    views.CustomPasswordResetConfirmView.as_view(
        template_name='registration/password_reset_confirm.html'
    ), 
    name='password_reset_confirm'),
    
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
    template_name='registration/password_reset_complete.html'
), name='password_reset_complete'),

    # Отзывы
    path('reviews/add/', views.add_review, name='add_review'),
    path('reviews/', views.review_list, name='review_list'),
    path('reviews/<int:pk>/', views.review_detail, name='review_detail'),
    path('reviews/delete/<int:review_id>/', login_required(views.delete_review), name='delete_review'),

    # API
    path('api/master/<int:master_id>/services/', views.get_master_services, name='master_services'),

    # Заказы
    path('orders/', (views.order_list), name='order_list'),
    path('orders/<int:pk>/', (views.order_detail), name='order_detail'),
    path('orders/<int:pk>/edit/', (views.order_edit), name='order_edit'),
    path('orders/<int:pk>/delete/', (views.order_delete), name='order_delete'),
    path('orders/create/', (views.order_create), name='order_create'),

    # Админ-панель
    path('admin-panel/', include([
        path('', user_passes_test(lambda u: u.is_staff)(views.admin_panel), name='admin_panel'),
        path('masters/', user_passes_test(lambda u: u.is_staff)(views.master_list), name='master_list'),
        path('masters/create/', user_passes_test(lambda u: u.is_staff)(views.master_create), name='master_create'),
        path('masters/edit/<int:pk>/', user_passes_test(lambda u: u.is_staff)(views.master_edit), name='master_edit'),
        path('masters/delete/<int:pk>/', user_passes_test(lambda u: u.is_staff)(views.master_delete), name='master_delete'),
        path('masters/<int:master_pk>/delete-service/<int:service_pk>/', 
            views.master_delete_service, 
            name='admin_master_delete_service'),
        
        # Управление услугами
        path('services/', user_passes_test(lambda u: u.is_staff)(views.service_list), name='service_list'),
        path('services/create/', user_passes_test(lambda u: u.is_staff)(views.service_create), name='service_create'),
        path('services/edit/<int:pk>/', user_passes_test(lambda u: u.is_staff)(views.service_edit), name='service_edit'),
        path('services/delete/<int:pk>/', user_passes_test(lambda u: u.is_staff)(views.service_delete), name='service_delete'),
        
        # Управление заказами
        path('orders/', user_passes_test(lambda u: u.is_staff)(views.order_list_admin), name='admin_order_list'),
        path('orders/<int:order_id>/', user_passes_test(lambda u: u.is_staff)(views.admin_order_detail), name='admin_order_detail'),
        path('orders/<int:order_id>/edit/', user_passes_test(lambda u: u.is_staff)(views.admin_order_edit), name='admin_order_edit'),
        path('orders/<int:order_id>/delete/', user_passes_test(lambda u: u.is_staff)(views.admin_order_delete), name='admin_order_delete'),
        path('orders/update-status/<int:pk>/', user_passes_test(lambda u: u.is_staff)(views.order_update_status), name='admin_order_update_status'),
        
        # Управление отзывами
        path('reviews/', user_passes_test(lambda u: u.is_staff)(views.review_list_admin), name='admin_review_list'),
        path('reviews/toggle-publish/<int:pk>/', user_passes_test(lambda u: u.is_staff)(views.review_toggle_publish), name='admin_review_toggle_publish'),
        path('reviews/<int:pk>/edit/', user_passes_test(lambda u: u.is_staff)(views.review_edit), name='admin_review_edit'),
        path('reviews/<int:pk>/delete/', user_passes_test(lambda u: u.is_staff)(views.review_delete), name='admin_review_delete'),
    ])),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)