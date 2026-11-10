from .temas import SLUG_PADRAO, TEMAS, tema_ativo, versao_css


def tema(request):
    """Contrato do PROJECT_SPEC Anexo A.5. Nunca levanta exceção."""
    try:
        slug, dados = tema_ativo()
        versao = versao_css(slug)
    except Exception:  # noqa: BLE001 — o tema nunca pode derrubar a página
        slug, dados, versao = SLUG_PADRAO, TEMAS[SLUG_PADRAO], ''
    return {
        'tema': {'slug': slug, 'bs_theme': dados['bs_theme'], 'navbar_bs': dados['navbar_bs'],
                 **dados['eixos']},
        'tema_versao': versao,
        'shell_template': 'layouts/shell/topo.html',
    }
