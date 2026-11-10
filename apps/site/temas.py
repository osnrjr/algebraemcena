"""Presets de tema habilitados no produto (PROJECT_SPEC §4.2; Doc ① §11.6).

Cada preset traz as três cores (Fundos, Destaques, Escritas), as cores derivadas e os eixos de
estilo. Extensões de tokens de outras apps entram por `settings.TEMA_EXTENSOES` (ADR-006), sem que
esta app dependa delas.
"""

import hashlib

from django.conf import settings
from django.utils.module_loading import import_string

TEMAS = {
    't05': {
        'nome': 'T05 Profissional',
        'bs_theme': 'light',
        'navbar_bs': 'dark',
        'cores': {
            'fundo': '#F8FAFC', 'destaque': '#1E3A8A', 'escrita': '#0F172A',
            'destaque-rgb': '30, 58, 138', 'superficie': '#FFFFFF', 'borda': '#E2E8F0',
            'escrita-suave': '#475569', 'destaque-hover': '#1A3278', 'sobre-destaque': '#FFFFFF',
            'navbar': '#1E3A8A', 'superficie-2': '#F1F5F9',
            'sem-sucesso': '#15803D', 'sem-perigo': '#B91C1C', 'sem-alerta': '#B45309',
            'sem-sucesso-hover': '#166534', 'sem-perigo-hover': '#991B1B', 'sem-sobre': '#FFFFFF',
        },
        'eixos': {'raio': 'suave', 'sombra': 'suave', 'densidade': 'confortavel',
                  'movimento': 'discreto', 'tipografia': 'sistema', 'icones': 'contorno'},
    },
    't08': {
        'nome': 'T08 Noturno',
        'bs_theme': 'dark',
        'navbar_bs': 'dark',
        'cores': {
            'fundo': '#12141A', 'destaque': '#4FA3FF', 'escrita': '#E6E8EE',
            'destaque-rgb': '79, 163, 255', 'superficie': '#1A1D25', 'borda': '#2C313D',
            'escrita-suave': '#A9B0BF', 'destaque-hover': '#7AB8FF', 'sobre-destaque': '#0B0D12',
            'navbar': '#161920', 'superficie-2': '#21252F',
            'sem-sucesso': '#4ADE80', 'sem-perigo': '#F87171', 'sem-alerta': '#FBBF24',
            'sem-sucesso-hover': '#86EFAC', 'sem-perigo-hover': '#FCA5A5', 'sem-sobre': '#0B0D12',
        },
        'eixos': {'raio': 'suave', 'sombra': 'nenhuma', 'densidade': 'confortavel',
                  'movimento': 'discreto', 'tipografia': 'sistema', 'icones': 'contorno'},
    },
    't09': {
        'nome': 'T09 Acessível',
        'bs_theme': 'light',
        'navbar_bs': 'dark',
        'cores': {
            'fundo': '#FFFFFF', 'destaque': '#0B3D91', 'escrita': '#000000',
            'destaque-rgb': '11, 61, 145', 'superficie': '#FFFFFF', 'borda': '#000000',
            'escrita-suave': '#1F1F1F', 'destaque-hover': '#082C6A', 'sobre-destaque': '#FFFFFF',
            'navbar': '#0B3D91', 'superficie-2': '#F2F2F2',
            'sem-sucesso': '#0B6B2B', 'sem-perigo': '#A50E0E', 'sem-alerta': '#7A4A00',
            'sem-sucesso-hover': '#084D1F', 'sem-perigo-hover': '#7A0A0A', 'sem-sobre': '#FFFFFF',
        },
        'eixos': {'raio': 'reto', 'sombra': 'nenhuma', 'densidade': 'ampla',
                  'movimento': 'nenhum', 'tipografia': 'sistema', 'icones': 'contorno'},
    },
}

SLUG_PADRAO = 't08'


def tema_ativo():
    """Tema em uso. Nunca levanta exceção: em falha, devolve o padrão (Doc ① §11.5)."""
    slug = getattr(settings, 'TEMA_PADRAO', SLUG_PADRAO)
    if slug not in TEMAS:
        slug = SLUG_PADRAO
    return slug, TEMAS[slug]


def _extensoes(slug):
    linhas = []
    for caminho in getattr(settings, 'TEMA_EXTENSOES', []):
        linhas.extend(import_string(caminho)(slug))
    return linhas


def gerar_css(slug):
    tema = TEMAS[slug]
    linhas = [
        f'  --{nome}: {valor};' if nome.startswith('sem-') else f'  --tema-{nome}: {valor};'
        for nome, valor in tema['cores'].items()
    ]
    linhas += _extensoes(slug)
    return ':root {\n' + '\n'.join(linhas) + '\n}\n'


def versao_css(slug):
    return hashlib.sha256(gerar_css(slug).encode()).hexdigest()[:12]
