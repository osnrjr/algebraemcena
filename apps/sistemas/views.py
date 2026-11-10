import json
from urllib.parse import urlencode

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET

from apps.core.ratelimit import excedeu, ip_do_cliente

from . import exemplos_rapidos, relatorio
from .engine import METODOS, ErroEntrada, resolver
from .forms import SistemaForm, dados_de_exibicao

INICIAL = exemplos_rapidos.parametros(*exemplos_rapidos.EXEMPLOS[0][1:])
CAMPOS_QUERY = ['entrada', 'metodo', 'n', 'equacoes'] + [
    f'{c}{i}{j}' for i in range(1, 4) for c, j in [('a', 1), ('a', 2), ('a', 3), ('k', '')]]


def _query(dados):
    """Querystring do sistema atual (para o .txt e o link), só com os campos do formulário."""
    return urlencode([(c, dados.get(c)) for c in CAMPOS_QUERY if dados.get(c) not in (None, '')])


def _limite_excedido(request):
    return excedeu('resolver', ip_do_cliente(request), settings.RATELIMIT_RESOLVER)


def _calcular(form):
    dados = form.cleaned_data
    try:
        return resolver(dados['A'], dados['K'], dados['metodo'])
    except ErroEntrada as erro:
        form.add_error(None, str(erro))
        return None


@require_GET
def resolver_view(request):
    """Resolver público e sem estado (ADR-007): o sistema vem na querystring, nada é gravado.

    Sem parâmetros, abre já resolvido o exemplo 2×2, começando pela matriz montada.
    """
    status = 200
    if 'n' in request.GET or 'equacoes' in request.GET:
        if _limite_excedido(request):
            resposta = render(request, '429.html', status=429)
            resposta['Retry-After'] = '60'
            return resposta
        dados = request.GET
    else:
        dados = {k: str(v) for k, v in INICIAL.items()}
    form = SistemaForm(dados)
    trace = _calcular(form) if form.is_valid() else None
    if trace is None:
        status = 400
    else:
        equacoes = trace['passos'][0]['equacoes']
        form = SistemaForm(dados_de_exibicao(form.data, form.cleaned_data['A'],
                                              form.cleaned_data['K'], equacoes))
    try:
        ordem = int(form.data.get('n', 2))
    except (TypeError, ValueError):
        ordem = 2
    metodo = form.data.get('metodo') if form.data.get('metodo') in METODOS else 'ambos'
    contexto = {
        'form': form,
        'grade': form.grade(),
        'ordem': ordem if ordem in (2, 3) else 2,
        'entrada': 'equacoes' if form.data.get('entrada') == 'equacoes' else 'matriz',
        'trace': trace,
        'exemplos': exemplos_rapidos.lista(metodo),
        'exemplo_l3_json': json.dumps(exemplos_rapidos.exemplo_3x3_linha3()),
        'equacoes': trace['passos'][0]['equacoes'] if trace else [],
        'secoes': relatorio.secoes(trace) if trace else [],
        'query': _query(form.data),
    }
    return render(request, 'sistemas/resolver.html', contexto, status=status)


@require_GET
def trace_json(request):
    """RF-009: o *trace* JSON (contrato do Remotion e do Manim). Público e com rate limit."""
    if _limite_excedido(request):
        return JsonResponse({'erro': 'Muitas requisições. Tente de novo em um minuto.'}, status=429,
                            headers={'Retry-After': '60'})
    form = SistemaForm(request.GET)
    if not form.is_valid():
        return JsonResponse({'erros': form.errors.get_json_data()}, status=400)
    trace = _calcular(form)
    if trace is None:
        return JsonResponse({'erros': form.errors.get_json_data()}, status=400)
    return JsonResponse(trace, json_dumps_params={'ensure_ascii': False})


@require_GET
def solucao_txt(request):
    """RN-024: a resolução completa, dividida por método, em texto para salvar (.txt)."""
    if _limite_excedido(request):
        return HttpResponse('Muitas requisições. Tente de novo em um minuto.', status=429,
                            content_type='text/plain; charset=utf-8', headers={'Retry-After': '60'})
    form = SistemaForm(request.GET or {k: str(v) for k, v in INICIAL.items()})
    trace = _calcular(form) if form.is_valid() else None
    if trace is None:
        erros = '; '.join(m for lista in form.errors.values() for m in lista)
        return HttpResponse(f'Sistema inválido: {erros}', status=400, content_type='text/plain; charset=utf-8')
    n = trace['entrada']['n']
    resposta = HttpResponse(relatorio.texto(trace), content_type='text/plain; charset=utf-8')
    resposta['Content-Disposition'] = f'attachment; filename="solucao-sistema-{n}x{n}.txt"'
    return resposta
