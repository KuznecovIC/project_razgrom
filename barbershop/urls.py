from django.contrib.auth import views as auth_views
from django.urls import path
from core import views
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.admin.views.decorators import staff_member_required

urlpatterns = [
    # Основные маршруты
    path('', views.index, name='home'),
    path('landing/', views.landing, name='landing'),
    path('thanks/', views.thanks, name='thanks'),
    
    
    # Маршруты для отзывов
    path('reviews/add/', views.add_review, name='add_review'),
    path('reviews/', views.review_list, name='review_list'),
    path('reviews/<int:pk>/', views.review_detail, name='review_detail'),
    path('reviews/delete/<int:review_id>/', login_required(views.delete_review), name='delete_review'),

    path('api/master/<int:master_id>/services/', views.get_master_services, name='master_services'),
    
    # Маршруты для заказов
    path('orders/', login_required(views.order_list), name='order_list'),
    path('orders/<int:pk>/', login_required(views.order_detail), name='order_detail'),
    path('orders/<int:pk>/edit/', login_required(views.order_edit), name='order_edit'),
    path('orders/<int:pk>/delete/', login_required(views.order_delete), name='order_delete'),

    # Административные маршруты
    path('admin/orders/', staff_member_required(views.admin_orders_list), name='admin_orders_list'),
    path('admin/orders/<int:order_id>/', staff_member_required(views.admin_order_detail), name='admin_order_detail'),
    path('admin/orders/<int:order_id>/edit/', staff_member_required(views.admin_order_edit), name='admin_order_edit'),
    path('admin/orders/<int:order_id>/delete/', staff_member_required(views.admin_order_delete), name='admin_order_delete'),
    
    # Аутентификация
    path('accounts/login/', auth_views.LoginView.as_view(
        template_name='registration/login.html',
        redirect_authenticated_user=True
    ), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path('accounts/password_reset/', auth_views.PasswordResetView.as_view(
        template_name='registration/password_reset.html',
        email_template_name='registration/password_reset_email.html',
        subject_template_name='registration/password_reset_subject.txt'
    ), name='password_reset'),
    path('accounts/password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='registration/password_reset_done.html'
    ), name='password_reset_done'),
    path('accounts/reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='registration/password_reset_confirm.html'
    ), name='password_reset_confirm'),
    path('accounts/reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='registration/password_reset_complete.html'
    ), name='password_reset_complete'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)