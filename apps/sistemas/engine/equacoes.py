"""Leitura do sistema digitado como equações (RN-022). Python puro, sem Django.

Exemplo aceito:
    2x + 3y = 4
    -x + 2y = 5
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
            'À esquerda use termos com x, y ou z; à direita, um número.')
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


def ler_sistema(texto):
    """Converte o texto em (A, K). Uma equação por linha (ou separadas por ';'); n = nº de equações."""
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
    variaveis = VARIAVEIS[:n]
    A, K = [], []
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
        coeficientes = [Fraction(0)] * n
        for termo in termos:
            coef, variavel = _ler_termo(termo, indice)
            if variavel not in variaveis:
                permitidas = ', '.join(variaveis)
                raise ErroEntrada(f'Equação {indice}: com {n} equações use só {permitidas}.')
            coeficientes[variaveis.index(variavel)] += coef
        try:
            k = ler_numero(direita)
        except ErroEntrada as erro:
            raise ErroEntrada(f'Equação {indice}, lado direito: {erro}') from None
        A.append(coeficientes)
        K.append(k)
    return A, K
