"""Exemplos prontos do resolver: um 2×2 e um 3×3 (casos de referência, regras_de_negocio.md §6)."""

from urllib.parse import urlencode

EXEMPLOS = [
    ('2×2', [[2, 3], [-1, 2]], [4, 5]),
    ('3×3', [[3, -2, 1], [-1, 3, -2], [1, -4, 1]], [-2, -3, -4]),
]


def parametros(A, K, metodo='ambos'):
    dados = {'entrada': 'matriz', 'n': len(A), 'metodo': metodo}
    for i, linha in enumerate(A, start=1):
        for j, valor in enumerate(linha, start=1):
            dados[f'a{i}{j}'] = valor
        dados[f'k{i}'] = K[i - 1]
    return dados


def lista(metodo='ambos'):
    return [{'rotulo': rotulo, 'query': urlencode(parametros(A, K, metodo))} for rotulo, A, K in EXEMPLOS]


def exemplo_3x3_linha3():
    """Valores de L3 do exemplo 3×3 como dicionário {'a31': '1', 'a32': '-4', ...}."""
    for rotulo, A, K in EXEMPLOS:
        if rotulo.startswith('3'):
            dados = {f'a3{j}': str(v) for j, v in enumerate(A[2], start=1)}
            dados['k3'] = str(K[2])
            return dados
    return {'a31': '1', 'a32': '-4', 'a33': '1', 'k3': '-4'}
