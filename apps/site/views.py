from django.http import HttpResponse
from django.views.decorators.http import require_GET
from django.views.generic import TemplateView

from .temas import gerar_css, tema_ativo


@require_GET
def tema_css(request):
    """/tema.css: tokens do tema ativo. URL versionada (?v=hash) com cache longo."""
    slug, _ = tema_ativo()
    resposta = HttpResponse(gerar_css(slug), content_type='text/css; charset=utf-8')
    resposta['Cache-Control'] = 'public, max-age=31536000, immutable'
    return resposta


class LandingView(TemplateView):
    template_name = 'site/landing.html'


class ComoFuncionaView(TemplateView):
    template_name = 'site/como_funciona.html'
