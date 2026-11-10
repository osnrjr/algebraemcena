"""Determinantes com memória de cálculo: produto cruzado 2×2 (RN-004) e Sarrus 3×3 (RN-005)."""

from fractions import Fraction

from .numeros import entre_parenteses, exibir


def det(matriz):
    """Determinante exato por expansão de Laplace na 1ª linha (n ≤ 3 no produto)."""
    n = len(matriz)
    if n == 1:
        return Fraction(matriz[0][0])
    if n == 2:
        return matriz[0][0] * matriz[1][1] - matriz[0][1] * matriz[1][0]
    total = Fraction(0)
    for j in range(n):
        menor = [linha[:j] + linha[j + 1:] for linha in matriz[1:]]
        total += (-1) ** j * matriz[0][j] * det(menor)
    return total


def substituir_coluna(matriz, coluna, valores):
    """Cópia da matriz com a coluna `coluna` trocada por `valores` (RN-006). Demais colunas fixas."""
    return [
        [valores[i] if j == coluna else valor for j, valor in enumerate(linha)]
        for i, linha in enumerate(matriz)
    ]


def _diagonal(matriz, celulas, sinal):
    fatores = [matriz[i][j] for i, j in celulas]
    produto = Fraction(1)
    for fator in fatores:
        produto *= fator
    return {
        'celulas': [list(c) for c in celulas],
        'sinal': sinal,
        'fatores': fatores,
        'produto': produto,
        'texto': '·'.join(entre_parenteses(f) for f in fatores) + f' = {exibir(produto)}',
    }


def memoria_2x2(matriz):
    """Diagonais e texto do produto cruzado. Devolve (valor, diagonais, matriz_exibida, texto)."""
    principal = _diagonal(matriz, [(0, 0), (1, 1)], '+')
    secundaria = _diagonal(matriz, [(0, 1), (1, 0)], '-')
    valor = principal['produto'] - secundaria['produto']
    texto = (
        f'Diagonal principal: {principal["texto"]}. '
        f'Diagonal secundária: {secundaria["texto"]}. '
        f'Resultado: {exibir(principal["produto"])} − {entre_parenteses(secundaria["produto"])}'
        f' = {exibir(valor)}.'
    )
    return valor, [principal, secundaria], matriz, texto


def memoria_sarrus(matriz):
    """Sarrus: repete C1 e C2 à direita; 3 diagonais descendentes (+) e 3 ascendentes (−)."""
    estendida = [linha + linha[:2] for linha in matriz]
    descendentes = [_diagonal(estendida, [(i, c + i) for i in range(3)], '+') for c in range(3)]
    ascendentes = [_diagonal(estendida, [(i, c - i) for i in range(3)], '-') for c in range(2, 5)]
    soma_mais = sum((d['produto'] for d in descendentes), Fraction(0))
    soma_menos = sum((d['produto'] for d in ascendentes), Fraction(0))
    valor = soma_mais - soma_menos
    texto = (
        'Descendentes (+): ' + '; '.join(d['texto'] for d in descendentes)
        + f' → soma {exibir(soma_mais)}. '
        'Ascendentes (−): ' + '; '.join(d['texto'] for d in ascendentes)
        + f' → soma {exibir(soma_menos)}. '
        f'Resultado: {exibir(soma_mais)} − {entre_parenteses(soma_menos)} = {exibir(valor)}.'
    )
    return valor, descendentes + ascendentes, estendida, texto


def memoria(matriz):
    """Escolhe o método pela ordem: 2×2 produto cruzado; 3×3 Sarrus."""
    if len(matriz) == 2:
        return memoria_2x2(matriz)
    if len(matriz) == 3:
        return memoria_sarrus(matriz)
    raise ValueError('Ordem não suportada.')
