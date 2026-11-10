"""Escalonamento com operações elementares (RN-008), posto e classificação (RN-009, RN-010)."""

from fractions import Fraction
from math import gcd

from .numeros import formatar_expressao

PARAMETROS = ['t', 's']


def _rotulo(i):
    return f'L{i + 1}'


def _termo_linha(fator, linha):
    """'2·L1', 'L1', '(1/3)·L2' sem sinal."""
    fator = abs(Fraction(fator))
    if fator == 1:
        return _rotulo(linha)
    if fator.denominator == 1:
        return f'{fator.numerator}·{_rotulo(linha)}'
    return f'({fator})·{_rotulo(linha)}'


def notacao(operacao):
    codigo = operacao['codigo']
    alvo = _rotulo(operacao['alvo'])
    if codigo == 'E1':
        return f'{alvo} ↔ {_rotulo(operacao["pivo"])}'
    if codigo == 'E2':
        return f'{alvo} ← {_termo_linha(operacao["fator"], operacao["alvo"])}'
    if codigo == 'E3':
        fator = operacao['fator']
        sinal = '−' if fator < 0 else '+'
        return f'{alvo} ← {alvo} {sinal} {_termo_linha(fator, operacao["pivo"])}'
    alfa, beta = operacao['alfa'], operacao['beta']
    sinal = '−' if beta < 0 else '+'
    return (f'{alvo} ← {_termo_linha(alfa, operacao["alvo"])} {sinal} '
            f'{_termo_linha(beta, operacao["pivo"])}')


def _escolher_pivo(matriz, coluna, inicio):
    """Preferir ±1; senão menor valor absoluto; empate: linha mais acima (RN-008)."""
    candidatas = [i for i in range(inicio, len(matriz)) if matriz[i][coluna] != 0]
    if not candidatas:
        return None
    return min(candidatas, key=lambda i: (abs(matriz[i][coluna]) != 1, abs(matriz[i][coluna]), i))


def _combinacao_inteira(pivo, elemento):
    """α·Li + β·Lr anulando `elemento` com pivô `pivo`, α > 0 e coeficientes reduzidos."""
    alfa, beta = Fraction(pivo), Fraction(-elemento)
    if alfa < 0:
        alfa, beta = -alfa, -beta
    if alfa.denominator == 1 and beta.denominator == 1:
        divisor = gcd(alfa.numerator, beta.numerator)
        if divisor > 1:
            alfa, beta = alfa / divisor, beta / divisor
    return alfa, beta


def escalonar(aumentada, n):
    """Executa Gauss (fase de ida). Devolve (matriz, pivôs, eventos).

    Cada evento é (operacao, matriz_antes, matriz_depois).
    """
    matriz = [list(linha) for linha in aumentada]
    eventos = []
    pivos = []
    linha_atual = 0
    for coluna in range(n):
        if linha_atual >= len(matriz):
            break
        escolhida = _escolher_pivo(matriz, coluna, linha_atual)
        if escolhida is None:
            continue
        if escolhida != linha_atual:
            antes = [list(l) for l in matriz]
            matriz[linha_atual], matriz[escolhida] = matriz[escolhida], matriz[linha_atual]
            eventos.append(({'codigo': 'E1', 'alvo': linha_atual, 'pivo': escolhida}, antes,
                            [list(l) for l in matriz]))
        pivo = matriz[linha_atual][coluna]
        for i in range(linha_atual + 1, len(matriz)):
            elemento = matriz[i][coluna]
            if elemento == 0:
                continue
            antes = [list(l) for l in matriz]
            fator = elemento / pivo
            if fator.denominator == 1:
                matriz[i] = [a - fator * b for a, b in zip(matriz[i], matriz[linha_atual])]
                operacao = {'codigo': 'E3', 'alvo': i, 'pivo': linha_atual, 'fator': -fator}
            else:
                alfa, beta = _combinacao_inteira(pivo, elemento)
                matriz[i] = [alfa * a + beta * b for a, b in zip(matriz[i], matriz[linha_atual])]
                operacao = {'codigo': 'E4', 'alvo': i, 'pivo': linha_atual, 'alfa': alfa, 'beta': beta}
            eventos.append((operacao, antes, [list(l) for l in matriz]))
        pivos.append((linha_atual, coluna))
        linha_atual += 1
    return matriz, pivos, eventos


def postos(matriz, n):
    """(posto de A, posto de [A|K]) lidos da forma escalonada."""
    posto_a = sum(1 for linha in matriz if any(v != 0 for v in linha[:n]))
    posto_ak = sum(1 for linha in matriz if any(v != 0 for v in linha))
    return posto_a, posto_ak


def classificar(posto_a, posto_ak, n):
    if posto_a < posto_ak:
        return 'SI'
    if posto_a == n:
        return 'SPD'
    return 'SPI'


def reduzir(matriz, pivos):
    """Gauss–Jordan (fase de volta): pivôs viram 1 (E2) e zeros acima (E3)."""
    matriz = [list(linha) for linha in matriz]
    eventos = []
    for linha, coluna in reversed(pivos):
        pivo = matriz[linha][coluna]
        if pivo != 1:
            antes = [list(l) for l in matriz]
            fator = 1 / pivo
            matriz[linha] = [fator * v for v in matriz[linha]]
            eventos.append(({'codigo': 'E2', 'alvo': linha, 'pivo': linha, 'fator': fator}, antes,
                            [list(l) for l in matriz]))
        for i in range(linha):
            elemento = matriz[i][coluna]
            if elemento == 0:
                continue
            antes = [list(l) for l in matriz]
            matriz[i] = [a - elemento * b for a, b in zip(matriz[i], matriz[linha])]
            eventos.append(({'codigo': 'E3', 'alvo': i, 'pivo': linha, 'fator': -elemento}, antes,
                            [list(l) for l in matriz]))
    return matriz, eventos


def solucao_geral(reduzida, pivos, n, rotulos):
    """Solução a partir da forma reduzida (RN-010).

    Devolve (expressoes, parametros, particular): `expressoes[j]` é o texto de cada incógnita,
    `parametros` a lista {'nome', 'variavel'} e `particular` os valores com parâmetros = 0.
    """
    colunas_pivo = {c: l for l, c in pivos}
    livres = [c for c in range(n) if c not in colunas_pivo]
    nomes = {c: PARAMETROS[k] for k, c in enumerate(livres)}
    expressoes, particular = [], []
    for j in range(n):
        if j in nomes:
            expressoes.append(nomes[j])
            particular.append(Fraction(0))
            continue
        linha = reduzida[colunas_pivo[j]]
        constante = linha[n]
        termos = [(-linha[c], nomes[c]) for c in livres]
        expressoes.append(formatar_expressao(constante, termos))
        particular.append(constante)
    parametros = [{'nome': nomes[c], 'variavel': rotulos[c]} for c in livres]
    return expressoes, parametros, particular


def texto_classificacao(classe, posto_a, posto_ak, n):
    base = f'posto(A) = {posto_a}, posto([A|K]) = {posto_ak}, n = {n}. '
    if classe == 'SPD':
        return base + 'Postos iguais ao número de incógnitas: solução única.'
    if classe == 'SPI':
        livres = n - posto_a
        return base + (f'Postos iguais e menores que {n}: infinitas soluções, com {livres} '
                       f'parâmetro{"s" if livres > 1 else ""} livre{"s" if livres > 1 else ""}.')
    return base + 'Postos diferentes: há uma linha 0 = c com c ≠ 0, nenhuma solução.'

