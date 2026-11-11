"""Leitura do sistema digitado como equações (RN-022). Python puro, sem Django.

Exemplo aceito:
    2x + 3y = 4
    -x + 2y = 5

Qualquer letra pode ser incógnita (RN-022): `2a + 3b = 4` funciona como `2x + 3y = 4`.
- Só x, y e z (ou parte delas): as incógnitas são x, y[, z], como sempre — uma letra ausente
  em todas as equações vale coeficiente 0.
- Outras letras: cada letra distinta é uma incógnita; são tantas quanto as equações, em ordem
  alfabética (a, b, c → colunas 1, 2, 3). As cores seguem a coluna, não a letra.
"""

import re
from fractions import Fraction

from .numeros import ErroEntrada, ler_numero

VARIAVEIS = ['x', 'y', 'z']
LIMITE_TEXTO = 300

_RE_TERMO = re.compile(r'^([+-]?)(?:\(([^()]*)\)|([\d.,/]*))[*·]?([a-z])$')


def _ler_termo(termo, numero_eq):
    achado = _RE_TERMO.match(termo)
    if not achado:
        raise ErroEntrada(
            f"Equação {numero_eq}: não entendi o termo '{termo}'. "
            'À esquerda use termos com uma letra por incógnita (x, y, z ou outras); à direita, um número.')
    sinal, entre_parenteses, solto, variavel = achado.groups()
    texto = entre_parenteses if entre_parenteses is not None else solto
    if texto == '':
        if entre_parenteses is not None:
            raise ErroEntrada(f"Equação {numero_eq}: parênteses vazios em '{termo}'.")
        coef = Fraction(1)
    else:
        try:
            coef = ler_numero(texto)
        except ErroEntrada as erro:
            raise ErroEntrada(f"Equação {numero_eq}, termo '{termo}': {erro}") from None
    return (-coef if sinal == '-' else coef), variavel


def _incognitas(letras, n):
    """Escolhe as n incógnitas a partir das letras usadas (RN-022)."""
    if letras <= set(VARIAVEIS[:n]):
        return VARIAVEIS[:n]
    usadas = sorted(letras)
    lista = ', '.join(usadas)
    if len(usadas) > n:
        raise ErroEntrada(f'Há {len(usadas)} incógnitas ({lista}) para {n} equações. '
                          'Use uma incógnita para cada equação.')
    if len(usadas) < n:
        raise ErroEntrada(f'Com {n} equações use {n} incógnitas; encontrei só {lista}.')
    return usadas


def ler_sistema_com_incognitas(texto):
    """Converte o texto em (A, K, incognitas). Uma equação por linha (ou separadas por ';')."""
    if texto is None or not str(texto).strip():
        raise ErroEntrada('Digite o sistema, uma equação por linha.')
    texto = str(texto)
    if len(texto) > LIMITE_TEXTO:
        raise ErroEntrada('Texto longo demais.')
    texto = texto.replace('−', '-').replace('–', '-')
    linhas = [l.strip() for l in re.split(r'[\n;]', texto) if l.strip()]
    if len(linhas) not in (2, 3):
        raise ErroEntrada('Informe 2 ou 3 equações, uma por linha.')
    n = len(linhas)

    lidas = []                                        # [(termos [(coef, letra)], k)]
    for indice, linha in enumerate(linhas, start=1):
        compacta = re.sub(r'\s+', '', linha).lower()
        if compacta.count('=') != 1:
            raise ErroEntrada(f'Equação {indice}: use exatamente um sinal de igual.')
        esquerda, direita = compacta.split('=')
        if not esquerda or not direita:
            raise ErroEntrada(f'Equação {indice}: falta um lado da igualdade.')
        termos = re.findall(r'[+-]?[^+-]+', esquerda)
        if ''.join(termos) != esquerda:
            raise ErroEntrada(f'Equação {indice}: há sinais repetidos ou soltos.')
        lidos = [_ler_termo(termo, indice) for termo in termos]
        try:
            k = ler_numero(direita)
        except ErroEntrada as erro:
            raise ErroEntrada(f'Equação {indice}, lado direito: {erro}') from None
        lidas.append((lidos, k))

    incognitas = _incognitas({letra for lidos, _ in lidas for _, letra in lidos}, n)
    A, K = [], []
    for lidos, k in lidas:
        coeficientes = [Fraction(0)] * n
        for coef, letra in lidos:
            coeficientes[incognitas.index(letra)] += coef
        A.append(coeficientes)
        K.append(k)
    return A, K, incognitas


def ler_sistema(texto):
    """Converte o texto em (A, K). Ver ler_sistema_com_incognitas para saber as letras usadas."""
    A, K, _ = ler_sistema_com_incognitas(texto)
    return A, K
