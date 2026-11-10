"""Leitura e exibição de números exatos (RN-001, RN-002). Python puro, sem Django."""

import re
from fractions import Fraction

LIMITE = 10**6

_RE_INTEIRO = re.compile(r'^[+-]?\d+$')
_RE_DECIMAL = re.compile(r'^[+-]?(\d+[.,]\d{1,6}|[.,]\d{1,6})$')
_RE_FRACAO = re.compile(r'^([+-]?\d+)/(\d+)$')


class ErroEntrada(ValueError):
    """Entrada fora dos formatos aceitos. A mensagem é exibida ao usuário."""


def ler_numero(texto):
    """Converte inteiro, decimal (vírgula ou ponto) ou fração em `Fraction`. Vazio vale 0."""
    if texto is None:
        return Fraction(0)
    bruto = str(texto).strip().replace('−', '-').replace(' ', '')
    if bruto == '':
        return Fraction(0)
    if len(bruto) > 20:
        raise ErroEntrada('Número longo demais.')
    if _RE_INTEIRO.match(bruto):
        valor = Fraction(int(bruto))
    elif _RE_DECIMAL.match(bruto):
        valor = Fraction(bruto.replace(',', '.'))
    else:
        achado = _RE_FRACAO.match(bruto)
        if not achado:
            raise ErroEntrada('Use número inteiro, decimal ou fração, como 3/4.')
        denominador = int(achado.group(2))
        if denominador == 0:
            raise ErroEntrada('O denominador não pode ser zero.')
        valor = Fraction(int(achado.group(1)), denominador)
    if abs(valor.numerator) > LIMITE or valor.denominator > LIMITE:
        raise ErroEntrada('Use valores entre −1.000.000 e 1.000.000.')
    return valor


def para_json(valor):
    """Fração como texto ASCII sem perda: '-7/2', '4'."""
    return str(Fraction(valor))


def exibir(valor):
    """Fração para leitura humana, com sinal de menos tipográfico: '−7/2'."""
    return str(Fraction(valor)).replace('-', '−')


def entre_parenteses(valor):
    """Negativos e frações entre parênteses, para produtos: '(−3)', '(22/5)'."""
    valor = Fraction(valor)
    return f'({exibir(valor)})' if valor < 0 or valor.denominator != 1 else exibir(valor)


def aproximado(valor, casas=4):
    """Aproximação decimal com vírgula, só quando a fração não é inteira."""
    valor = Fraction(valor)
    if valor.denominator == 1:
        return None
    texto = f'{float(valor):.{casas}f}'.rstrip('0').rstrip('.')
    return '≈ ' + texto.replace('.', ',').replace('-', '−')


def coeficiente_de_termo(valor):
    """Coeficiente sem sinal para montar termos como '3x', 'x', '(3/4)x'."""
    valor = abs(Fraction(valor))
    if valor == 1:
        return ''
    if valor.denominator == 1:
        return str(valor.numerator)
    return f'({valor})'


def formatar_combinacao(termos, constante=None):
    """Monta 'a·x + b·y' a partir de pares (coeficiente, nome), com sinais tipográficos.

    Termos com coeficiente zero são mantidos (ex.: '0y'), como no caderno.
    """
    partes = []
    for indice, (coef, nome) in enumerate(termos):
        coef = Fraction(coef)
        corpo = f'0{nome}' if coef == 0 else f'{coeficiente_de_termo(coef)}{nome}'
        if indice == 0:
            partes.append(('−' if coef < 0 else '') + corpo)
        else:
            partes.append(('− ' if coef < 0 else '+ ') + corpo)
    texto = ' '.join(partes)
    if constante is not None:
        texto += f' = {exibir(constante)}'
    return texto


def formatar_expressao(constante, parametros):
    """Expressão afim para solução geral: '22/5 − (7/5)t'. `parametros` é lista (coef, nome)."""
    partes = []
    constante = Fraction(constante)
    nao_nulos = [(Fraction(c), n) for c, n in parametros if c != 0]
    if constante != 0 or not nao_nulos:
        partes.append(exibir(constante))
    for coef, nome in nao_nulos:
        corpo = f'{coeficiente_de_termo(coef)}{nome}'
        if not partes:
            partes.append(('−' if coef < 0 else '') + corpo)
        else:
            partes.append(('− ' if coef < 0 else '+ ') + corpo)
    return ' '.join(partes)
