"""Regras do rodízio da landing e da medição do vídeo (RF-016, RN-025 a RN-027).

- proxima_variante(): round robin global e atômico entre as variações ativas, na ordem do painel.
- registrar_evento(): aplica um evento do navegador (clique, progresso, fim) a uma exibição,
  com limites que impedem números impossíveis (tempo maior que o decorrido, duração absurda).
- estatisticas(): agregados por variação, calculados no banco.
"""

import re
import uuid
from datetime import timedelta

from django.db import transaction
from django.db.models import Avg, Count, F, FloatField, Q, Sum, Value
from django.db.models.functions import Cast, Greatest, Least
from django.utils import timezone

from .models import ExibicaoLanding, RodizioLanding, VarianteLanding

# Eventos aceitos só até este tempo depois do acesso; depois disso a exibição está fechada.
JANELA_EVENTOS = timedelta(hours=12)
DURACAO_MAXIMA = 4 * 3600          # s; protege contra durações absurdas
CLIQUES_MAXIMOS = 50               # por exibição
FRACAO_CONCLUSAO = 0.95            # assistiu até 95% da duração = concluiu
EVENTOS = {'clique', 'progresso', 'fim'}

_ROBOS = re.compile(
    r'bot|crawl|spider|slurp|preview|facebookexternalhit|whatsapp|telegram|discord|embedly|'
    r'curl|wget|python|httpx|okhttp|go-http|java/|headless|lighthouse|pagespeed', re.I)


def eh_robo(request):
    """Robôs e clientes sem navegador não entram no rodízio nem nas estatísticas."""
    agente = request.META.get('HTTP_USER_AGENT', '')
    return not agente or bool(_ROBOS.search(agente))


def ordenadas_ativas():
    return list(VarianteLanding.objects.filter(ativa=True).order_by('ordem', 'numero'))


def proxima_variante():
    """Devolve a variação deste acesso e avança o contador global (None se nenhuma estiver ativa)."""
    with transaction.atomic():
        estado, _ = RodizioLanding.objects.select_for_update().get_or_create(pk=1)
        ativas = ordenadas_ativas()
        if not ativas:
            return None
        variante = ativas[estado.contador % len(ativas)]
        estado.contador = F('contador') + 1
        estado.save(update_fields=['contador'])
    return variante


def previsao():
    """A variação que o próximo acesso vai receber, sem avançar o rodízio."""
    ativas = ordenadas_ativas()
    if not ativas:
        return None
    estado = RodizioLanding.objects.filter(pk=1).first()
    return ativas[(estado.contador if estado else 0) % len(ativas)]


def _numero(valor, minimo, maximo):
    try:
        n = float(valor)
    except (TypeError, ValueError):
        return minimo
    if n != n:                       # NaN
        return minimo
    return max(minimo, min(maximo, n))


def registrar_evento(token, evento, segundos=0, posicao=0, duracao=0):
    """Aplica o evento à exibição `token`. Devolve False se o token não vale (sem revelar o motivo)."""
    if evento not in EVENTOS:
        return False
    try:
        pk = uuid.UUID(str(token))
    except ValueError:
        return False
    agora = timezone.now()
    exibicao = ExibicaoLanding.objects.filter(pk=pk, criada_em__gte=agora - JANELA_EVENTOS).only('criada_em').first()
    if exibicao is None:
        return False

    decorrido = (agora - exibicao.criada_em).total_seconds()
    duracao = _numero(duracao, 0, DURACAO_MAXIMA)
    segundos = _numero(segundos, 0, decorrido + 5)          # não assiste mais do que o tempo na página
    posicao = _numero(posicao, 0, duracao or DURACAO_MAXIMA)

    campos = {
        'segundos_assistidos': Greatest(F('segundos_assistidos'), Value(segundos)),
        'posicao_maxima': Greatest(F('posicao_maxima'), Value(posicao)),
        'duracao_video': Greatest(F('duracao_video'), Value(duracao)),
        'atualizada_em': agora,
    }
    if evento == 'clique':
        campos['cliques'] = Least(F('cliques') + 1, Value(CLIQUES_MAXIMOS))
    concluiu = evento == 'fim' or (duracao > 0 and posicao >= FRACAO_CONCLUSAO * duracao)
    if concluiu:
        campos['concluiu'] = True
    ExibicaoLanding.objects.filter(pk=pk).update(**campos)
    return True


PERIODOS = {'hoje': ('Hoje', 0), '7d': ('7 dias', 7), '30d': ('30 dias', 30), 'tudo': ('Tudo', None)}


def inicio_do_periodo(periodo):
    if periodo not in PERIODOS:
        periodo = 'tudo'
    dias = PERIODOS[periodo][1]
    if dias is None:
        return periodo, None
    hoje = timezone.localtime().replace(hour=0, minute=0, second=0, microsecond=0)
    return periodo, hoje - timedelta(days=dias)


def estatisticas(desde=None):
    """Uma linha por variação (todas, ativas ou não) + total. Percentual por exibição limitado a 100%."""
    filtro = Q(exibicoes__criada_em__gte=desde) if desde else Q()
    com_play = filtro & Q(exibicoes__cliques__gt=0)
    percentual = Least(
        Cast(F('exibicoes__segundos_assistidos'), FloatField()) / F('exibicoes__duracao_video'), Value(1.0))
    linhas = (
        VarianteLanding.objects.order_by('ordem', 'numero')
        .annotate(
            exibicoes_total=Count('exibicoes', filter=filtro),
            exibicoes_com_play=Count('exibicoes', filter=com_play),
            cliques_total=Sum('exibicoes__cliques', filter=filtro, default=0),
            segundos_total=Sum('exibicoes__segundos_assistidos', filter=filtro, default=0.0),
            percentual_medio=Avg(percentual, filter=com_play & Q(exibicoes__duracao_video__gt=0)),
            concluiram=Count('exibicoes', filter=filtro & Q(exibicoes__concluiu=True)),
        )
    )
    resultado = []
    for v in linhas:
        resultado.append({
            'variante': v,
            'exibicoes': v.exibicoes_total,
            'com_play': v.exibicoes_com_play,
            'taxa_play': (v.exibicoes_com_play / v.exibicoes_total) if v.exibicoes_total else None,
            'cliques': v.cliques_total,
            'segundos': v.segundos_total,
            'segundos_por_play': (v.segundos_total / v.exibicoes_com_play) if v.exibicoes_com_play else None,
            'percentual_medio': v.percentual_medio,
            'concluiram': v.concluiram,
        })
    return resultado


def total(linhas):
    exib = sum(l['exibicoes'] for l in linhas)
    com_play = sum(l['com_play'] for l in linhas)
    segundos = sum(l['segundos'] for l in linhas)
    pesos = [(l['percentual_medio'], l['com_play']) for l in linhas if l['percentual_medio'] is not None]
    soma_pesos = sum(p for _, p in pesos)
    return {
        'exibicoes': exib, 'com_play': com_play,
        'taxa_play': com_play / exib if exib else None,
        'cliques': sum(l['cliques'] for l in linhas),
        'segundos': segundos,
        'segundos_por_play': segundos / com_play if com_play else None,
        'percentual_medio': (sum(m * p for m, p in pesos) / soma_pesos) if soma_pesos else None,
        'concluiram': sum(l['concluiram'] for l in linhas),
    }
