from django.contrib.auth import views as auth_views
from django.urls import path
from core import views
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.landing, name='landing'),
    path('thanks/<int:order_id>/', views.thanks, name='thanks'),
    path('orders/', login_required(views.orders_list), name='orders_list'),
    path('orders/<int:order_id>/', login_required(views.order_detail), name='order_detail'),
    path('orders/<int:order_id>/edit/', login_required(views.order_edit), name='order_edit'),
    path('orders/<int:order_id>/delete/', login_required(views.order_delete), name='order_delete'),
    path(
        'accounts/login/',
        auth_views.LoginView.as_view(
            template_name='core/login.html',
            redirect_authenticated_user=True
        ),
        name='login'
    ),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)