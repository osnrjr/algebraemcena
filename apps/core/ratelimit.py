"""Rate limit simples na aplicação, baseado no cache do Django (Doc ① §19).

Sem dependência nova: janela fixa por chave (IP com hash). Não confia em cabeçalhos de proxy
(PROJECT_SPEC §10.1: proxy reverso ainda não definido).
"""

import hashlib
import time
from functools import wraps

from django.core.cache import cache
from django.http import HttpResponse
from django.template.loader import render_to_string

UNIDADES = {'s': 1, 'm': 60, 'h': 3600}


def _parse(taxa):
    quantidade, unidade = taxa.split('/')
    return int(quantidade), UNIDADES[unidade]


def ip_do_cliente(request):
    return request.META.get('REMOTE_ADDR', '')


def excedeu(escopo, identificador, taxa):
    """Registra uma tentativa e informa se o limite da janela foi excedido."""
    limite, janela = _parse(taxa)
    chave_id = hashlib.sha256(identificador.encode()).hexdigest()[:32]
    chave = f'rl:{escopo}:{chave_id}:{int(time.time() // janela)}'
    cache.add(chave, 0, janela)
    try:
        total = cache.incr(chave)
    except ValueError:
        cache.set(chave, 1, janela)
        total = 1
    return total > limite


def limitar_por_ip(escopo, taxa_setting):
    """Decorator: responde 429 quando o IP excede a taxa definida em settings."""

    def decorador(view):
        @wraps(view)
        def _view(request, *args, **kwargs):
            from django.conf import settings

            taxa = getattr(settings, taxa_setting)
            if excedeu(escopo, ip_do_cliente(request), taxa):
                corpo = render_to_string('429.html', request=request)
                resposta = HttpResponse(corpo, status=429)
                resposta['Retry-After'] = str(_parse(taxa)[1])
                return resposta
            return view(request, *args, **kwargs)

        return _view

    return decorador
