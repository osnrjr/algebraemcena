from django.urls import path

from . import views

app_name = 'site'

urlpatterns = [
    path('', views.LandingView.as_view(), name='landing'),
    path('como-funciona/', views.ComoFuncionaView.as_view(), name='como_funciona'),
    path('tema.css', views.tema_css, name='tema_css'),
]
