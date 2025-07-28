from django.contrib.auth import views as auth_views
from django.urls import path, include, reverse_lazy
from core import views
from django.contrib.auth.decorators import login_required, user_passes_test # user_passes_test уже здесь был
from django.conf import settings
from django.conf.urls.static import static
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
        ['получатель@example.com'], # Замените на реальный email для тестирования
    )
    return HttpResponse("Проверьте почту!")

urlpatterns = [
    # Админка
    path('admin/', admin.site.urls),
    
    # Тест email
    path('test-email/', test_email),
    
    # Основные маршруты
    path('', views.LandingView.as_view(), name='home'), # Изменено на LandingView
    path('landing/', views.LandingView.as_view(), name='landing'), # Если это та же главная страница, что и ''
    path('create-order-from-landing/', views.LandingOrderCreateView.as_view(), name='create_order_from_landing'), # НОВЫЙ URL для обработки формы
    path('thanks/', views.ThanksView.as_view(), name='thanks'), # Изменено на ThanksView
    path('services/', views.services_view, name='services'), # Функциональное представление

    # Аутентификация
    path('register/', views.register_view, name='register'), # Функциональное представление
    path('login/', views.login_view, name='login'), # Функциональное представление
    path('logout/', views.logout_view, name='logout'), # Функциональное представление

    # Сброс пароля (Классовые представления Django, вызовы корректны)
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
    path('reviews/add/', views.ReviewCreateView.as_view(), name='add_review'), # Классовое представление
    path('reviews/', views.PublicReviewListView.as_view(), name='review_list'), # Классовое представление
    path('reviews/<int:pk>/', views.PublicReviewDetailView.as_view(), name='review_detail'), # Классовое представление
    path('reviews/delete/<int:pk>/', views.UserReviewDeleteView.as_view(), name='delete_review'), # Классовое представление

    # API
    path('api/master/<int:master_id>/services/', views.get_master_services, name='master_services'), # Функциональное представление

    # Заказы (пользовательские)
    path('orders/', views.OrdersListView.as_view(), name='order_list'), # Классовое представление (OrdersListView)
    path('orders/<int:pk>/', views.OrderDetailView.as_view(), name='order_detail'), # Классовое представление (OrderDetailView)
    path('orders/<int:pk>/edit/', views.UserOrderUpdateView.as_view(), name='order_edit'), # Классовое представление (UserOrderUpdateView)
    path('orders/<int:pk>/delete/', views.UserOrderDeleteView.as_view(), name='order_delete'), # Классовое представление (UserOrderDeleteView)
    path('orders/create/', views.OrderCreateView.as_view(), name='order_create'), # Классовое представление (OrderCreateView)

    # Админ-панель
    path('admin-panel/', include([
        path('', user_passes_test(lambda u: u.is_staff)(views.admin_panel), name='admin_panel'), # Функциональное представление
        
        # Управление мастерами
        path('masters/', views.MasterListView.as_view(), name='master_list'), # Классовое представление
        path('masters/create/', views.MasterCreateView.as_view(), name='master_create'), # Классовое представление
        path('masters/edit/<int:pk>/', views.MasterUpdateView.as_view(), name='master_edit'), # Классовое представление
        path('masters/delete/<int:pk>/', views.MasterDeleteView.as_view(), name='master_delete'), # Классовое представление
        path('masters/<int:master_pk>/delete-service/<int:service_pk>/', 
             views.master_delete_service, # Функциональное представление
             name='admin_master_delete_service'),
        
        # Управление услугами
        path('services/', views.ServiceListView.as_view(), name='service_list'), # Классовое представление
        path('services/create/', views.ServiceCreateView.as_view(), name='service_create'), # Классовое представление
        path('services/edit/<int:pk>/', views.ServiceUpdateView.as_view(), name='service_edit'), # Классовое представление
        path('services/delete/<int:pk>/', views.ServiceDeleteView.as_view(), name='service_delete'), # Классовое представление
        
        # Управление заказами
        path('orders/', views.AdminOrderListView.as_view(), name='admin_order_list'), # Классовое представление
        path('orders/<int:order_id>/', views.AdminOrderDetailView.as_view(), name='admin_order_detail'), # Классовое представление
        path('orders/<int:order_id>/edit/', views.AdminOrderUpdateView.as_view(), name='admin_order_edit'), # Классовое представление
        path('orders/<int:order_id>/delete/', views.AdminOrderDeleteView.as_view(), name='admin_order_delete'), # Классовое представление
        path('orders/update-status/<int:pk>/', user_passes_test(lambda u: u.is_staff)(views.order_update_status), name='admin_order_update_status'), # Функциональное представление
        
        # Управление отзывами
        path('reviews/', views.AdminReviewListView.as_view(), name='admin_review_list'), # Классовое представление
        path('reviews/toggle-publish/<int:pk>/', views.AdminReviewTogglePublishView.as_view(), name='admin_review_toggle_publish'), # Классовое представление
        path('reviews/<int:pk>/edit/', views.AdminReviewUpdateView.as_view(), name='admin_review_edit'), # Классовое представление
        path('reviews/<int:pk>/delete/', views.AdminReviewDeleteView.as_view(), name='admin_review_delete'), # Классовое представление
    ])),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)