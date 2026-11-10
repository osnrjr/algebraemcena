from django.urls import path

from . import views

app_name = 'sistemas'

urlpatterns = [
    path('', views.resolver_view, name='resolver'),
    path('trace.json', views.trace_json, name='trace'),
    path('solucao.txt', views.solucao_txt, name='solucao_txt'),
]
