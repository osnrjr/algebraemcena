from django.urls import path

from . import views

app_name = 'site'

urlpatterns = [
    path('', views.LandingView.as_view(), name='landing'),
    path('como-funciona/', views.ComoFuncionaView.as_view(), name='como_funciona'),
    path('tema.css', views.tema_css, name='tema_css'),
    # Rodízio da landing (RF-016): sem link público; painel exige site.experimento_gerenciar
    path('experimento/', views.PainelExperimentoView.as_view(), name='experimento'),
    path('experimento/previa/<int:numero>/', views.PreviaVarianteView.as_view(), name='experimento_previa'),
    path('experimento/evento/', views.evento_experimento, name='experimento_evento'),
]
