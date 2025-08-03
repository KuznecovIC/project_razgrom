from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core import views
from django.contrib.auth.decorators import user_passes_test


urlpatterns = [
    # Админка
    path('admin/', admin.site.urls),
    
    # Подключение URL-адресов из приложения users
    path('', include('users.urls')),

    # Основные маршруты
    path('', views.LandingView.as_view(), name='home'),
    path('landing/', views.LandingView.as_view(), name='landing'),
    path('create-order-from-landing/', views.LandingOrderCreateView.as_view(), name='create_order_from_landing'),
    path('thanks/', views.ThanksView.as_view(), name='thanks'),
    path('services/', views.services_view, name='services'),

    # Отзывы (исправлены, чтобы избежать конфликтов)
    path('reviews/', views.PublicReviewListView.as_view(), name='review_list'),
    path('reviews/add/', views.ReviewCreateView.as_view(), name='add_review'),
    path('reviews/delete/<int:pk>/', views.UserReviewDeleteView.as_view(), name='delete_review'),
    path('reviews/<int:pk>/', views.PublicReviewDetailView.as_view(), name='review_detail'),

    # API
    path('api/master/<int:master_id>/services/', views.get_master_services, name='master_services'),

    # Заказы (пользовательские)
    path('orders/', views.OrdersListView.as_view(), name='order_list'),
    path('orders/<int:pk>/', views.OrderDetailView.as_view(), name='order_detail'),
    path('orders/<int:pk>/edit/', views.UserOrderUpdateView.as_view(), name='order_edit'),
    path('orders/<int:pk>/delete/', views.UserOrderDeleteView.as_view(), name='order_delete'),
    path('orders/create/', views.OrderCreateView.as_view(), name='order_create'),

    # Админ-панель
    path('admin-panel/', include([
        path('', user_passes_test(lambda u: u.is_staff)(views.admin_panel), name='admin_panel'),
        
        # Управление мастерами
        path('masters/', views.MasterListView.as_view(), name='master_list'),
        path('masters/create/', views.MasterCreateView.as_view(), name='master_create'),
        path('masters/edit/<int:pk>/', views.MasterUpdateView.as_view(), name='master_edit'),
        path('masters/delete/<int:pk>/', views.MasterDeleteView.as_view(), name='master_delete'),
        path('masters/<int:master_pk>/delete-service/<int:service_pk>/', 
             views.master_delete_service,
             name='admin_master_delete_service'),
        
        # Управление услугами
        path('services/', views.ServiceListView.as_view(), name='service_list'),
        path('services/create/', views.ServiceCreateView.as_view(), name='service_create'),
        path('services/edit/<int:pk>/', views.ServiceUpdateView.as_view(), name='service_edit'),
        path('services/delete/<int:pk>/', views.ServiceDeleteView.as_view(), name='service_delete'),
        
        # Управление заказами
        path('orders/', views.AdminOrderListView.as_view(), name='admin_order_list'),
        path('orders/<int:order_id>/', views.AdminOrderDetailView.as_view(), name='admin_order_detail'),
        path('orders/<int:order_id>/edit/', views.AdminOrderUpdateView.as_view(), name='admin_order_edit'),
        path('orders/<int:order_id>/delete/', views.AdminOrderDeleteView.as_view(), name='admin_order_delete'),
        path('orders/update-status/<int:pk>/', user_passes_test(lambda u: u.is_staff)(views.order_update_status), name='admin_order_update_status'),
        
        # Управление отзывами
        path('reviews/', views.AdminReviewListView.as_view(), name='admin_review_list'),
        path('reviews/toggle-publish/<int:pk>/', views.AdminReviewTogglePublishView.as_view(), name='admin_review_toggle_publish'),
        path('reviews/<int:pk>/edit/', views.AdminReviewUpdateView.as_view(), name='admin_review_edit'),
        path('reviews/<int:pk>/delete/', views.AdminReviewDeleteView.as_view(), name='admin_review_delete'),
    ])),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)