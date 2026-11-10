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
