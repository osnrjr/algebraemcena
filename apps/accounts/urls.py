from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = 'accounts'

urlpatterns = [
    path('entrar/', views.LoginView.as_view(), name='login'),
    path('sair/', views.LogoutView.as_view(), name='logout'),
    path('senha/', views.PasswordResetView.as_view(), name='password_reset'),
    path('senha/enviada/', auth_views.PasswordResetDoneView.as_view(
        template_name='accounts/senha_enviada.html'), name='password_reset_done'),
    path('senha/<uidb64>/<token>/', views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('senha/concluida/', auth_views.PasswordResetCompleteView.as_view(
        template_name='accounts/senha_concluida.html'), name='password_reset_complete'),
]
