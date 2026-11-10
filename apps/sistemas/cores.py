"""Fonte única das cores semânticas de matemática (ADR-006; PROJECT_SPEC §4.2; RN-015).

Usada pelo `/tema.css` (tokens `--mat-*`), pelo player Remotion e pelas cenas Manim
(`exportar_json`). Contraste mínimo sobre Fundos: 4,5:1 (7:1 no T09), coberto por teste.
"""

import json

CORES = {
    't08': {'x': '#7FC4F0', 'y': '#3FD1A6', 'z': '#FF9A5C', 'k': '#F0E442', 'pivo': '#E3A3C7'},
    't05': {'x': '#0067A3', 'y': '#007A5A', 'z': '#B34700', 'k': '#6E5F00', 'pivo': '#9C3D74'},
    't09': {'x': '#004C7A', 'y': '#005A42', 'z': '#8A3600', 'k': '#524600', 'pivo': '#7A2E5A'},
}

FUNDOS = {'t08': '#12141A', 't05': '#F8FAFC', 't09': '#FFFFFF'}
CONTRASTE_MINIMO = {'t08': 4.5, 't05': 4.5, 't09': 7.0}


def _rgb(hexa):
    hexa = hexa.lstrip('#')
    return tuple(int(hexa[i:i + 2], 16) for i in (0, 2, 4))


def luminancia(hexa):
    canais = []
    for c in _rgb(hexa):
        c /= 255
        canais.append(c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4)
    r, g, b = canais
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contraste(a, b):
    la, lb = sorted((luminancia(a), luminancia(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def tokens_css(slug):
    """Linhas `--mat-*` para o `/tema.css` (registrado em settings.TEMA_EXTENSOES)."""
    cores = CORES.get(slug, CORES['t08'])
    linhas = []
    for nome, hexa in cores.items():
        r, g, b = _rgb(hexa)
        linhas.append(f'  --mat-{nome}: {hexa};')
        linhas.append(f'  --mat-{nome}-rgb: {r}, {g}, {b};')
    return linhas


def exportar_json(slug='t08'):
    """Paleta em JSON para Remotion e Manim."""
    return json.dumps({'tema': slug, 'fundo': FUNDOS[slug], 'cores': CORES[slug]}, indent=2)
