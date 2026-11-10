from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from django.views.generic import TemplateView

from apps.core.ratelimit import limitar_por_ip

from . import experimento
from .forms import VariantesFormSet
from .models import ExibicaoLanding, VarianteLanding
from .temas import gerar_css, tema_ativo

PERMISSAO_EXPERIMENTO = 'site.experimento_gerenciar'


@require_GET
def tema_css(request):
    """/tema.css: tokens do tema ativo. URL versionada (?v=hash) com cache longo."""
    slug, _ = tema_ativo()
    resposta = HttpResponse(gerar_css(slug), content_type='text/css; charset=utf-8')
    resposta['Cache-Control'] = 'public, max-age=31536000, immutable'
    return resposta


@method_decorator(never_cache, name='dispatch')
class LandingView(TemplateView):
    """Landing em rodízio (RF-016): cada acesso recebe a próxima variação ativa e vira uma exibição."""

    template_name = 'site/landing.html'

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        exibicao = None
        if self.request.method == 'GET' and not experimento.eh_robo(self.request):
            variante = experimento.proxima_variante()
            if variante:
                exibicao = ExibicaoLanding.objects.create(variante=variante)
        else:                                       # robôs e HEAD: não avançam nem contam
            variante = experimento.previsao()
        contexto.update(variante=variante.numero if variante else 1, exibicao=exibicao.pk if exibicao else None,
                        video_id=settings.VIDEO_APRESENTACAO_ID)
        return contexto


class ComoFuncionaView(TemplateView):
    template_name = 'site/como_funciona.html'


class ExperimentoMixin(LoginRequiredMixin, PermissionRequiredMixin):
    """Anônimo vai para o login; logado sem a permissão recebe 403."""

    permission_required = PERMISSAO_EXPERIMENTO


@method_decorator(never_cache, name='dispatch')
class PainelExperimentoView(ExperimentoMixin, TemplateView):
    """/experimento/: ordem e variações ativas do rodízio + estatísticas por variação."""

    template_name = 'site/experimento_painel.html'

    def get_context_data(self, formset=None, **kwargs):
        contexto = super().get_context_data(**kwargs)
        periodo, desde = experimento.inicio_do_periodo(self.request.GET.get('periodo', 'tudo'))
        linhas = experimento.estatisticas(desde)
        contexto.update(
            formset=formset or VariantesFormSet(queryset=VarianteLanding.objects.order_by('ordem', 'numero')),
            linhas=linhas, total=experimento.total(linhas), proxima=experimento.previsao(),
            periodo=periodo, periodos=[(chave, rotulo) for chave, (rotulo, _) in experimento.PERIODOS.items()],
        )
        return contexto

    def post(self, request, *args, **kwargs):
        formset = VariantesFormSet(request.POST, queryset=VarianteLanding.objects.order_by('ordem', 'numero'))
        if formset.is_valid():
            formset.save()
            messages.success(request, 'Rodízio atualizado. A ordem nova vale a partir do próximo acesso.')
            return redirect(f"{request.path}?periodo={request.GET.get('periodo', 'tudo')}")
        return self.render_to_response(self.get_context_data(formset=formset))


@method_decorator(never_cache, name='dispatch')
class PreviaVarianteView(ExperimentoMixin, TemplateView):
    """/experimento/previa/<n>/: mostra uma variação sem avançar o rodízio nem registrar nada."""

    template_name = 'site/experimento_previa.html'

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        atual = get_object_or_404(VarianteLanding, numero=kwargs['numero'])
        contexto.update(variante=atual.numero, atual=atual, exibicao=None, video_id=settings.VIDEO_APRESENTACAO_ID,
                        variantes=VarianteLanding.objects.order_by('ordem', 'numero'))
        return contexto


@csrf_exempt                   # enviado por sendBeacon; autorizado pelo UUID da exibição (RN-026)
@require_POST
@limitar_por_ip('experimento', 'RATELIMIT_EXPERIMENTO')
def evento_experimento(request):
    """Recebe clique/progresso/fim do vídeo. 204 mesmo para token inválido (não revela quais existem)."""
    token = request.POST.get('token', '')
    evento = request.POST.get('evento', '')
    if not token or evento not in experimento.EVENTOS:
        return HttpResponseBadRequest()
    experimento.registrar_evento(token, evento, request.POST.get('segundos'), request.POST.get('posicao'),
                                 request.POST.get('duracao'))
    return HttpResponse(status=204)
