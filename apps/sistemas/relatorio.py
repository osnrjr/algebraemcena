"""Resumo da resolução por método (3º quadrante) e exportação em .txt (RN-024).

Lê só o *trace* (contrato único, ADR-001): não recalcula nada.
"""

from .engine.numeros import exibir

SECOES = [
    ('inicio', 'Sistema'),
    ('cramer', 'Regra de Cramer'),
    ('escalonamento', 'Escalonamento'),
    ('resultado', 'Resultado'),
]
NOMES_METODO = {'ambos': 'Cramer e escalonamento', 'cramer': 'Regra de Cramer',
                'escalonamento': 'Escalonamento'}
MATRIZ_AUMENTADA = {'forma_matricial', 'operacao_elementar', 'forma_escalonada', 'forma_reduzida'}


def _com_sinal(valor):
    texto = exibir(valor)
    return texto if texto.startswith('−') else '+' + texto


def matriz_texto(passo, rotulos):
    """Matriz alinhada em texto monoespaçado, com cabeçalho das colunas.

    Aumentada: `[ 3  −2   1 | −2 ]`. Sarrus: colunas repetidas fora dos colchetes, como no caderno.
    """
    matriz = passo.get('matriz')
    if not matriz:
        return ''
    papeis = passo.get('papeis') or []
    copias = set(passo.get('copias') or [])
    nomes = {'x': rotulos[0] if rotulos else 'x', 'y': rotulos[1] if len(rotulos) > 1 else 'y',
             'z': rotulos[2] if len(rotulos) > 2 else 'z', 'k': 'K'}
    cabecalho = [nomes.get(p, p) for p in papeis]
    celulas = [[exibir(v) for v in linha] for linha in matriz]
    largura = [max(len(cabecalho[j]) if j < len(cabecalho) else 0, *(len(l[j]) for l in celulas))
               for j in range(len(matriz[0]))]
    aumentada = passo['tipo'] in MATRIZ_AUMENTADA
    ultima = len(largura) - 1

    def montar(valores, abre, fecha, barra):
        partes = []
        for j, valor in enumerate(valores):
            if j in copias and j - 1 not in copias:
                partes.append(fecha)
            elif aumentada and j == ultima:
                partes.append(barra)
            partes.append(valor.rjust(largura[j]))
        texto = abre + ' ' + '  '.join(partes)
        if not copias:
            texto += ' ' + fecha
        return texto

    linhas = ['     ' + montar(cabecalho, ' ', ' ', ' ')]
    for i, linha in enumerate(celulas, start=1):
        linhas.append(f'L{i}:  ' + montar(linha, '[', ']', '|'))
    return '\n'.join(l.rstrip() for l in linhas)


def linhas_do_passo(passo):
    """Linhas de conta de um passo, no mesmo texto mostrado no quadrante Conta."""
    tipo = passo['tipo']
    if tipo == 'forma_matricial':
        return [f'L{i}: {eq}' for i, eq in enumerate(passo['equacoes'], start=1)]
    if tipo == 'determinante':
        linhas = [('+ ' if d['sinal'] == '+' else '− ') + d['texto'] for d in passo['diagonais']]
        mais = ' '.join(_com_sinal(d['contribuicao']) for d in passo['diagonais'] if d['sinal'] == '+')
        menos = ' '.join(_com_sinal(d['contribuicao']) for d in passo['diagonais'] if d['sinal'] == '-')
        soma_menos = exibir(passo['soma_menos'])
        sinal = ' − ' if soma_menos.startswith('−') else ' + '
        linhas += [
            f'Soma (+): {mais} = {exibir(passo["soma_mais"])}',
            f'Soma (−): {menos} = {soma_menos}',
            f'{passo["rotulo"]} = {exibir(passo["soma_mais"])}{sinal}{soma_menos.lstrip("−")}'
            f' = {exibir(passo["valor"])}',
        ]
        return linhas
    if tipo == 'substituir_coluna':
        return [passo['texto']]
    if tipo == 'operacao_elementar':
        return [passo['texto']]
    if tipo in ('quocientes', 'verificacao'):
        return [item['texto'] for item in passo['itens']]
    if tipo == 'solucao':
        formal = passo.get('formal')
        if not formal:
            return [passo['conjunto']] + [item['texto'] for item in passo['itens']]
        return ([formal['formas'][0]] + [f'ou {f}' for f in formal['formas'][1:]]
                + [formal['leitura']] + [item['texto'] for item in passo['itens']]
                + [f'Nota: {formal["nota"]}', 'Como se escreve o conjunto solução:']
                + [f'{"►" if r["atual"] else "·"} {r["classe"]} — {r["quantidade"]}: {r["formato"]}'
                   for r in formal['resumo']])
    return [passo['texto']]


def secoes(trace):
    """Passos agrupados por método/seção, para os blocos recolhíveis e para o .txt."""
    rotulos = trace['entrada']['rotulos']
    grupos = []
    for chave, nome in SECOES:
        passos = [p for p in trace['passos'] if p['secao'] == chave]
        if not passos:
            continue
        grupos.append({
            'chave': chave,
            'nome': nome,
            'passos': [{'id': p['id'], 'titulo': p['titulo'], 'matriz': matriz_texto(p, rotulos),
                        'linhas': linhas_do_passo(p)} for p in passos],
        })
    return grupos


def texto(trace):
    """Resolução completa em texto puro, pronta para salvar como .txt."""
    entrada = trace['entrada']
    resultado = trace['resultado']
    n = entrada['n']
    regua = '=' * 64
    linhas = [
        'ÁLGEBRA EM CENA — Resolução de sistema linear',
        regua,
        f'Ordem: {n}×{n}    Método: {NOMES_METODO.get(entrada["metodo"], entrada["metodo"])}',
        f'Classificação: {resultado["classificacao"]} ({resultado["formal"]["quantidade"].lower()})'
        f'    {resultado["formal"]["formas"][0]}',
        regua,
    ]
    for numero, grupo in enumerate(secoes(trace), start=1):
        linhas += ['', f'{numero}. {grupo["nome"].upper()}', '-' * 64]
        for passo in grupo['passos']:
            linhas += ['', f'Passo {passo["id"]}: {passo["titulo"]}']
            if passo['matriz']:
                linhas += ['', *('    ' + l for l in passo['matriz'].split('\n')), '']
            linhas += ['    ' + l for l in passo['linhas']]
    linhas += ['', regua, 'Gerado por Álgebra em Cena. Contas exatas, com frações.', '']
    return '\n'.join(linhas)
