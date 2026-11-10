"""Gera o *trace* (RN-013): a lista de passos que a web, o Remotion e o Manim desenham.

O *trace* é o contrato único (ADR-001). Mudança incompatível incrementa `VERSAO`.
"""

import hashlib
import json
from fractions import Fraction

from . import determinante, escalonamento
from .numeros import ErroEntrada, aproximado, entre_parenteses, exibir, formatar_combinacao, para_json

VERSAO = 1
METODOS = ('cramer', 'escalonamento', 'ambos')
ROTULOS_PADRAO = ['x', 'y', 'z']


def _mj(matriz):
    return [[para_json(v) for v in linha] for linha in matriz]


class _Construtor:
    def __init__(self):
        self.passos = []

    def add(self, tipo, secao, titulo, texto, **extra):
        passo = {'id': len(self.passos) + 1, 'tipo': tipo, 'secao': secao,
                 'titulo': titulo, 'texto': texto}
        passo.update(extra)
        self.passos.append(passo)
        return passo


def _validar(A, K, metodo, rotulos):
    n = len(A)
    if n not in (2, 3):
        raise ErroEntrada('A ordem do sistema deve ser 2 ou 3.')
    if any(len(linha) != n for linha in A) or len(K) != n:
        raise ErroEntrada('O sistema precisa ter o mesmo número de equações e incógnitas.')
    if metodo not in METODOS:
        raise ErroEntrada('Método inválido.')
    rotulos = list(rotulos or ROTULOS_PADRAO[:n])
    if len(rotulos) != n:
        raise ErroEntrada('Informe um rótulo para cada incógnita.')
    return n, rotulos


def _equacoes(A, K, rotulos):
    return [formatar_combinacao(list(zip(linha, rotulos)), K[i]) for i, linha in enumerate(A)]


def _passo_determinante(c, matriz, papeis, nome, secao):
    valor, diagonais, exibida, texto = determinante.memoria(matriz)
    copias = []
    papeis_exibidos = list(papeis)
    if len(matriz) == 3:
        copias = [3, 4]
        papeis_exibidos = papeis + papeis[:2]
    metodo = 'produto cruzado' if len(matriz) == 2 else 'Sarrus'
    # Contribuição de cada diagonal para D: + produto (descendentes) ou − produto (ascendentes),
    # como no caderno: "+9 +4 +4 → +17" e "−3 −24 −2 → −29" (RN-005).
    contribuicoes = [d['produto'] if d['sinal'] == '+' else -d['produto'] for d in diagonais]
    soma_mais = sum((v for v, d in zip(contribuicoes, diagonais) if d['sinal'] == '+'), Fraction(0))
    soma_menos = sum((v for v, d in zip(contribuicoes, diagonais) if d['sinal'] == '-'), Fraction(0))
    c.add(
        'determinante', secao, f'{nome} por {metodo}', f'{nome} = {exibir(valor)}. {texto}',
        matriz=_mj(exibida), papeis=papeis_exibidos, copias=copias,
        diagonais=[{'celulas': d['celulas'], 'sinal': d['sinal'], 'produto': para_json(d['produto']),
                    'contribuicao': para_json(v), 'texto': d['texto']}
                   for d, v in zip(diagonais, contribuicoes)],
        soma_mais=para_json(soma_mais), soma_menos=para_json(soma_menos),
        rotulo=nome, valor=para_json(valor),
    )
    return valor


def _passo_operacao(c, operacao, antes, depois, papeis, fase):
    destaques = [{'indice': operacao['alvo'], 'papel': 'alvo'}]
    if operacao['codigo'] in ('E1', 'E3', 'E4'):
        destaques.append({'indice': operacao['pivo'], 'papel': 'pivo'})
    op_json = {k: (para_json(v) if isinstance(v, Fraction) else v) for k, v in operacao.items()}
    nota = escalonamento.notacao(operacao)
    explicacoes = {
        'E1': 'Troca de linhas para trazer um pivô mais simples para cima.',
        'E2': 'Divide a linha pelo pivô para que ele vire 1.',
        'E3': 'Soma um múltiplo da linha pivô para zerar o elemento.',
        'E4': 'Combina as duas linhas com coeficientes inteiros para zerar o elemento sem frações.',
    }
    c.add('operacao_elementar', 'escalonamento', nota,
          f'{fase}: {nota}. {explicacoes[operacao["codigo"]]}',
          matriz=_mj(depois), matriz_antes=_mj(antes), papeis=papeis,
          linhas=destaques, operacao=op_json, notacao=nota)


def _linhas_especiais(matriz, n):
    marcas = []
    for i, linha in enumerate(matriz):
        if all(v == 0 for v in linha[:n]):
            marcas.append({'indice': i, 'papel': 'contradicao' if linha[n] != 0 else 'nula'})
    return marcas


def _verificar(A, K, valores, rotulos):
    itens, todos = [], True
    for i, linha in enumerate(A):
        total = sum((a * v for a, v in zip(linha, valores)), Fraction(0))
        ok = total == K[i]
        todos = todos and ok
        conta = ' + '.join(f'{entre_parenteses(a)}·{entre_parenteses(v)}' for a, v in zip(linha, valores))
        itens.append({'linha': i, 'texto': f'L{i + 1}: {conta} = {exibir(total)} {"✓" if ok else "✗"}',
                      'ok': ok})
    return itens, todos


def resolver(A, K, metodo='ambos', rotulos=None):
    """Resolve o sistema A·X = K e devolve o *trace* (dict serializável em JSON).

    `A` e `K` podem conter textos (RN-001) ou números; tudo vira `Fraction`.
    """
    from .numeros import ler_numero

    A = [[ler_numero(v) if not isinstance(v, Fraction) else v for v in linha] for linha in A]
    K = [ler_numero(v) if not isinstance(v, Fraction) else v for v in K]
    n, rotulos = _validar(A, K, metodo, rotulos)
    papeis = ['x', 'y', 'z'][:n]
    aumentada = [linha + [K[i]] for i, linha in enumerate(A)]
    c = _Construtor()

    c.add('forma_matricial', 'inicio', 'Sistema na forma matricial [A | K]',
          'Cada coluna guarda os coeficientes de uma incógnita, sempre com a mesma cor. '
          'A coluna K reúne os termos independentes.',
          matriz=_mj(aumentada), papeis=papeis + ['k'], equacoes=_equacoes(A, K, rotulos))

    resultado = {}
    usar_cramer = metodo in ('cramer', 'ambos')
    usar_escalonamento = metodo in ('escalonamento', 'ambos')
    D = determinante.det(A)

    if usar_cramer:
        _passo_determinante(c, A, papeis, 'D', 'cramer')
        if D == 0:
            usar_escalonamento = True
            c.add('aviso', 'cramer', 'D = 0: a regra de Cramer não decide',
                  'Com D = 0 o sistema pode ser SPI ou SI, e os determinantes Dx, Dy, Dz não bastam '
                  'para distinguir. Seguimos pelo escalonamento.', nivel='atencao')
        else:
            valores = []
            for j in range(n):
                nome = f'D{rotulos[j]}' if len(rotulos[j]) == 1 else f'D{j + 1}'
                substituida = determinante.substituir_coluna(A, j, K)
                papeis_j = list(papeis)
                papeis_j[j] = 'k'
                c.add('substituir_coluna', 'cramer', f'{nome}: a coluna de {rotulos[j]} é substituída por K',
                      f'A coluna C{j + 1} ({rotulos[j]}) sai e a coluna K entra no mesmo lugar. '
                      'As outras colunas não mudam de posição.',
                      matriz=_mj(substituida), matriz_antes=_mj(A), papeis=papeis_j,
                      coluna=j, papel_original=papeis[j], rotulo=nome)
                Dj = _passo_determinante(c, substituida, papeis_j, nome, 'cramer')
                valores.append((nome, Dj))
            itens = []
            for j, (nome, Dj) in enumerate(valores):
                valor = Dj / D
                texto = f'{rotulos[j]} = {nome} / D = {exibir(Dj)} / {entre_parenteses(D)} = {exibir(valor)}'
                aprox = aproximado(valor)
                itens.append({'variavel': j, 'texto': texto + (f' ({aprox})' if aprox else ''),
                              'valor': para_json(valor)})
            c.add('quocientes', 'cramer', 'Regra de Cramer: cada incógnita é Dⱼ / D',
                  'Como D ≠ 0, cada incógnita é o seu determinante dividido por D.', itens=itens)

    if usar_escalonamento:
        papeis_aum = papeis + ['k']
        escalonada, pivos, eventos = escalonamento.escalonar(aumentada, n)
        if not eventos:
            c.add('aviso', 'escalonamento', 'A matriz já está escalonada',
                  'Nenhuma operação elementar é necessária nesta fase.', nivel='info')
        for operacao, antes, depois in eventos:
            _passo_operacao(c, operacao, antes, depois, papeis_aum, 'Escalonamento')
        posto_a, posto_ak = escalonamento.postos(escalonada, n)
        c.add('forma_escalonada', 'escalonamento', 'Forma escalonada',
              f'Abaixo de cada pivô só há zeros. {escalonamento.texto_classificacao(escalonamento.classificar(posto_a, posto_ak, n), posto_a, posto_ak, n)}',
              matriz=_mj(escalonada), papeis=papeis_aum, linhas=_linhas_especiais(escalonada, n),
              pivos=[list(p) for p in pivos])
        reduzida = escalonada
        if posto_a == posto_ak:
            reduzida, eventos_volta = escalonamento.reduzir(escalonada, pivos)
            for operacao, antes, depois in eventos_volta:
                _passo_operacao(c, operacao, antes, depois, papeis_aum, 'Forma reduzida')
            if eventos_volta:
                c.add('forma_reduzida', 'escalonamento', 'Forma reduzida (Gauss–Jordan)',
                      'Cada pivô vale 1 e é o único elemento não nulo da sua coluna; a solução se lê na coluna K.',
                      matriz=_mj(reduzida), papeis=papeis_aum, linhas=_linhas_especiais(reduzida, n),
                      pivos=[list(p) for p in pivos])
    else:
        reduzida, pivos = None, None
        posto_a = posto_ak = n

    classe = escalonamento.classificar(posto_a, posto_ak, n)
    nomes_classe = {'SPD': 'Sistema possível e determinado', 'SPI': 'Sistema possível e indeterminado',
                    'SI': 'Sistema impossível'}
    c.add('classificacao', 'resultado', f'{classe}: {nomes_classe[classe]}',
          escalonamento.texto_classificacao(classe, posto_a, posto_ak, n)
          if usar_escalonamento else f'D = {exibir(D)} ≠ 0: solução única.',
          valor=classe, posto_A=posto_a, posto_AK=posto_ak)

    parametros, valores_verif = [], None
    if classe == 'SPD':
        if usar_escalonamento:
            solucao = [reduzida[l][n] for l, _ in sorted(pivos, key=lambda p: p[1])]
        else:
            solucao = [determinante.det(determinante.substituir_coluna(A, j, K)) / D for j in range(n)]
        expressoes = [exibir(v) for v in solucao]
        conjunto = 'S = {(' + ', '.join(expressoes) + ')}'
        valores_verif = solucao
        resultado['solucao'] = [para_json(v) for v in solucao]
    elif classe == 'SPI':
        expressoes, parametros, particular = escalonamento.solucao_geral(reduzida, pivos, n, rotulos)
        dominio = ', '.join(p['nome'] for p in parametros)
        conjunto = 'S = {(' + ', '.join(expressoes) + ') | ' + dominio + ' ∈ ℝ}'
        valores_verif = particular
        resultado['solucao'] = expressoes
        resultado['particular'] = [para_json(v) for v in particular]
    else:
        expressoes = []
        conjunto = 'S = ∅'
        resultado['solucao'] = []

    itens_sol = [{'variavel': j, 'texto': f'{rotulos[j]} = {e}'} for j, e in enumerate(expressoes)]
    c.add('solucao', 'resultado', 'Conjunto solução', conjunto, itens=itens_sol, conjunto=conjunto,
          parametros=parametros)

    if valores_verif is not None:
        itens, todos = _verificar(A, K, valores_verif, rotulos)
        titulo = 'Verificação nas equações originais'
        texto = 'Substituindo a solução em cada equação original:'
        if classe == 'SPI':
            texto = ('Substituindo a solução particular com ' +
                     ', '.join(f'{p["nome"]} = 0' for p in parametros) + ' em cada equação original:')
        c.add('verificacao', 'resultado', titulo, texto, itens=itens, ok=todos)

    entrada = {'n': n, 'A': _mj(A), 'K': [para_json(v) for v in K], 'metodo': metodo,
               'rotulos': rotulos}
    resumo = json.dumps(entrada, sort_keys=True, ensure_ascii=False)
    resultado.update({'classificacao': classe, 'posto_A': posto_a, 'posto_AK': posto_ak,
                      'D': para_json(D), 'conjunto': conjunto,
                      'parametros': [p['nome'] for p in parametros]})
    return {
        'versao': VERSAO,
        'hash': hashlib.sha256(resumo.encode()).hexdigest(),
        'entrada': entrada,
        'passos': c.passos,
        'resultado': resultado,
    }
