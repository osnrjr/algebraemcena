# regras_de_negocio.md — Álgebra em Cena

**Projeto:** `algebra_linear`  
**Versão:** 0.1 (2026-11-09)  
**Referência:** `PROJECT_SPEC.md` §1.6 (RF) e §11 (testes). Este arquivo é a **fonte única** das regras de negócio (RN); o `PROJECT_SPEC.md` só aponta para cá.

---

## 1. Notação

| Símbolo | Significado |
| :--- | :--- |
| n | Ordem do sistema (número de equações = número de incógnitas), n ∈ {2, 3} |
| x, y, z | Incógnitas (x₁, x₂, x₃). O professor pode dar rótulos (ex.: "x = servidores básicos") |
| aᵢⱼ | Coeficiente da linha i, coluna j |
| Kᵢ | Termo independente da linha i (notação do caderno) |
| A | Matriz dos coeficientes (n × n) |
| [A \| K] | Matriz aumentada |
| Lᵢ | Linha i |
| Cⱼ | Coluna j |
| D | det(A) |
| Dx, Dy, Dz | Determinante de A com a coluna da incógnita substituída por K |

---

## 2. Requisitos funcionais detalhados

### RF-001 — Informar o sistema

- Dois modos de entrada (alternados por botões **Matriz | Equações**):
  - **Matriz** (padrão): o visitante escolhe a ordem (2×2 ou 3×3) e preenche a grade n × (n + 1), coeficientes e K. Logo abaixo da grade, o quadro **Sistema informado** mostra as equações correspondentes, atualizadas enquanto se digita.
  - **Equações**: o visitante digita o sistema, uma equação por linha (RN-022), e o sistema monta a matriz para calcular.
- Ao abrir o resolver sem parâmetros, o exemplo 2×2 já vem resolvido, começando pela matriz montada.
- Exemplos prontos: um 2×2 e um 3×3 (quadro **Exemplos**).
- Campo vazio vale **0** e aparece como 0 nos passos (ex.: `−2x + 0y + 5z = 24`).
- Formatos aceitos: RN-001.
- Método: `cramer`, `escalonamento` ou `ambos` (padrão: `ambos`).

### RF-002 — Forma matricial

Exibir `A · X = K` e `[A | K]` com cores por coluna (RN-015). Primeiro passo de todo *trace*.

### RF-003 — Determinante principal

2×2 por produto cruzado (RN-004); 3×3 por Sarrus (RN-005). Cada produto aparece com seu sinal e a diagonal correspondente destacada.

### RF-004 — Determinantes das incógnitas

Para cada incógnita, um passo que mostra a coluna saindo e a coluna K entrando no lugar (RN-006), seguido do cálculo do determinante e de xⱼ = Dⱼ / D.

### RF-005 — Escalonamento

Cada operação elementar é um passo separado (RN-008), com linha pivô e linha alvo destacadas (RN-016).

### RF-006 — Classificação

RN-009 e RN-010. O resultado aparece como selo com texto e cor (SPD, SPI, SI) e uma frase de justificativa (ex.: "posto(A) = 2 = posto([A|K]) < 3 → infinitas soluções").

### RF-007 — Verificação

RN-011.

### RF-008 — Navegação e compartilhamento

- Controles: anterior, próximo, reproduzir/pausar, ir para o início/fim. Teclado: ← → e espaço.
- "Copiar link" copia a URL atual, `/resolver/?n=…&metodo=…&a11=…&k1=…` (RN-014). Abrir o link reconstrói o mesmo *trace*.

### RF-009 — *Trace* JSON

`GET /resolver/trace.json?…` (mesmos parâmetros) devolve o *trace* (RN-013). Público, sem efeito colateral, com rate limit (PROJECT_SPEC §10.1).

### RF-010 — Player Remotion

O player recebe o *trace* como `inputProps` e anima os mesmos passos; não recalcula nada.

### RF-011 — Exemplos

Campos: título; enunciado contextualizado (texto simples, opcional); ordem; coeficientes e K; rótulos das incógnitas (opcionais); método sugerido. Classificação, solução e *trace* são calculados pelo motor ao salvar (RN-019).

### RF-012 — Galeria

Lista apenas exemplos `publicado`. Filtros: ordem (2×2, 3×3), método, classificação (SPD, SPI, SI), e se tem vídeo.

### RF-013 e RF-014 — Renderização e vídeo

RN-020 e RN-021.

### RF-015 — Páginas institucionais

Landing, "Como funciona" e perguntas frequentes (PROJECT_SPEC §3).

### RF-016 — Landing em rodízio com vídeo de apresentação

A landing tem 5 layouts com o vídeo de apresentação (YouTube não listado, player próprio).
Cada acesso recebe o próximo layout ativo (round robin global). O painel `/experimento/`,
sem link público, define a ordem e quais layouts participam e mostra, por layout, exibições,
cliques no vídeo, tempo assistido e percentual assistido. RN-025 a RN-027.

---

## 3. Regras de negócio — motor de cálculo

### RN-001 — Formatos de número aceitos

| Formato | Exemplos | Observação |
| :--- | :--- | :--- |
| Inteiro | `4`, `-450`, `+3` | |
| Decimal | `31,5`, `0.25`, `-2,75` | Vírgula ou ponto; até 6 casas decimais |
| Fração | `3/4`, `-7/2` | Denominador ≠ 0 |

- Espaços nas pontas são removidos; não se aceitam expressões (`2+3`), notação científica nem letras.
- Limite: numerador e denominador, após converter para fração irredutível, com |valor| ≤ 10⁶.
- Erro de formato aparece no campo, sem apagar os demais.

### RN-002 — Aritmética exata

- Todo cálculo usa `fractions.Fraction`. Nunca ponto flutuante.
- Exibição: inteiro quando o denominador é 1; senão fração irredutível com sinal no numerador (`-7/2`). Valor aproximado opcional com vírgula e 4 casas, sempre precedido de "≈".

### RN-003 — Ordem e forma

- n ∈ {2, 3}. A matriz é sempre quadrada (n equações, n incógnitas).
- Uma linha toda zero (`0x + 0y + 0z = 0`) é aceita (o sistema será SPI ou continuará a ser analisado pelo posto).

### RN-004 — Determinante 2×2 (produto cruzado)

D = a₁₁·a₂₂ − a₁₂·a₂₁. O passo mostra os dois produtos, como no caderno: diagonal principal (sinal +) e secundária (sinal −).

Exemplo: `[2 3; −1 2]` → 2·2 = 4 e 3·(−1) = −3 → D = 4 − (−3) = 7.

### RN-005 — Determinante 3×3 (Sarrus)

1. Repetir C1 e C2 à direita da matriz (destacadas como "cópia", em tom atenuado).
2. Três produtos descendentes (diagonais principais) somados: sinal +.
3. Três produtos ascendentes (diagonais secundárias) subtraídos: sinal −.
4. D = (soma dos descendentes) − (soma dos ascendentes).

O passo também exibe a forma do caderno, em que os produtos ascendentes já entram com o sinal trocado (ex.: `−3 − 24 − 2 = −29` e `+9 + 4 + 4 = +17` → D = −12).

Na animação, o **resultado de cada diagonal** (a sua contribuição com sinal) aparece **abaixo da matriz, sob a coluna onde a diagonal termina**, fora dos colchetes: em 3×3, uma linha para as descendentes (+) e outra para as ascendentes (−); em 2×2, uma linha só. O *trace* traz `contribuicao` por diagonal e `soma_mais` / `soma_menos` por determinante. A conta completa (produtos, somas e D) fica no quadrante **Conta**.

### RN-006 — Regra de Cramer

- Dⱼ = det(A com a coluna j substituída por K). Todas as outras colunas ficam **na posição original**:
  - Dx = `[K1 a12 a13; K2 a22 a23; K3 a32 a33]`
  - Dy = `[a11 K1 a13; a21 K2 a23; a31 K3 a33]`
  - Dz = `[a11 a12 K1; a21 a22 K2; a31 a32 K3]`
- Montar Dz como `[a11 a21 K1; a12 a22 K2; a13 a23 K3]` (A transposta com K) é **erro** e está coberto por teste de regressão.
- Com D ≠ 0: xⱼ = Dⱼ / D, sistema SPD.

### RN-007 — Aplicabilidade da regra de Cramer

- D ≠ 0 → Cramer conclui (SPD).
- D = 0 → Cramer **não conclui**. O *trace* registra o aviso e segue pelo escalonamento (RN-008) para classificar.
- É proibido concluir "SPI" só porque D = 0 e todos os Dⱼ = 0. Contraexemplo obrigatório nos testes: `x + y + z = 1; x + y + z = 2; x + y + z = 3` (D = Dx = Dy = Dz = 0 e o sistema é **SI**).
- Em 2×2, com D = 0: algum Dⱼ ≠ 0 → SI. Mesmo assim, a classificação final vem do posto (RN-009), para manter uma regra só.

### RN-008 — Escalonamento (operações elementares)

Operações permitidas, cada uma é um passo do *trace*:

| Código | Operação | Notação exibida |
| :--- | :--- | :--- |
| E1 | Trocar duas linhas | `L1 ↔ L2` |
| E2 | Multiplicar uma linha por c ≠ 0 | `L2 ← (1/3)·L2` |
| E3 | Somar a uma linha um múltiplo de outra | `L2 ← L2 + 2·L1` |
| E4 | Combinação de E2 e E3, com α ≠ 0 (evita frações, como no caderno) | `L2 ← 3·L2 − 2·L1` |

Na eliminação abaixo do pivô p, para anular o elemento a: se a/p é inteiro, usa-se E3 (`Li ← Li − (a/p)·Lr`); senão, E4 com α = p e β = −a (sinais ajustados para α > 0 e divididos pelo MDC). Na forma reduzida (Gauss–Jordan), o pivô vira 1 por E2 e os elementos acima são anulados por E3.

Escolha do pivô (didática, determinística): na coluna atual, entre as linhas ainda não usadas, preferir o elemento 1 ou −1; senão o de menor valor absoluto diferente de zero; em empate, a linha mais acima. Se o pivô não estiver na linha atual, aplicar E1 antes.

Forma final: escalonada (Gauss). A forma reduzida (Gauss–Jordan) é usada para ler a solução e aparece como passos adicionais.

### RN-009 — Classificação (Rouché–Capelli)

Seja r = posto(A), r' = posto([A | K]) e n o número de incógnitas:

| Condição | Classificação | Solução |
| :--- | :--- | :--- |
| r = r' = n | **SPD** — sistema possível e determinado | Única |
| r = r' < n | **SPI** — sistema possível e indeterminado | Infinitas, com n − r parâmetros livres |
| r < r' | **SI** — sistema impossível | Nenhuma; o escalonamento mostra uma linha `0 = c`, c ≠ 0 |

A frase de justificativa sempre cita r, r' e n.

### RN-010 — Solução geral no SPI

- Variáveis livres: as das colunas sem pivô. Recebem parâmetros `t` (e `s`, se forem duas), com t, s ∈ ℝ.
- Exibir a solução geral (ex.: `S = {(2 − t, 1 + t, t) | t ∈ ℝ}`) e uma solução particular com t = 0.

### RN-011 — Verificação

Para SPD (e para a solução particular no SPI), substituir os valores em **cada equação original** e mostrar a conta e o resultado com ✓ ou ✗ (ex.: `2·(−1) + 3·2 = 4 ✓`). ✗ nunca deve ocorrer; se ocorrer, é defeito do motor e o teste falha.

### RN-029 — Conjunto solução nos termos formais

O passo final "Conjunto solução" (animação, quadrante Conta e .txt) apresenta S conforme a classificação:

| Classe | Soluções | Como se escreve | Exemplo (2 incógnitas) |
| :-: | :-- | :-- | :-- |
| SPD | Única | o valor de cada incógnita, entre parênteses, dentro das chaves; **sem** "x ∈ ℝ" | `S = {(−1, 2)}` |
| SPI | Infinitas | forma genérica em função da(s) variável(is) livre(s) e o conjunto a que pertence(m); também com parâmetro | `S = {(1 − y, y) \| y ∈ ℝ}` ou `S = {(1 − t, t) \| t ∈ ℝ}` |
| SI | Nenhuma | conjunto vazio | `S = ∅` ou `S = { }` — **nunca** `S = {∅}` |

- Além da forma, o passo traz a **leitura** ("…formado pelos pares ordenados (1 − y, y), tal que y pertence
  aos reais"; a barra "|" ou ";" se lê "tal que"), uma **nota** no SPI (variável livre, "tal que") e no SI
  (o alerta sobre `S = {∅}`) — o SPD não tem nota — e, no .txt e no bloco
  Resultado, o **resumo comparativo** das três classes com a do sistema marcada (►).
- Par ordenado (2×2) ou terno ordenado (3×3). No SPI, a variável livre aparece como `z ∈ ℝ (variável livre)`
  e a verificação usa a solução particular com as livres iguais a 0.
- No *trace*: `passo.formal` e `resultado.formal` = `{quantidade, formas, leitura, nota, resumo}`;
  `resultado.conjunto` segue com a forma paramétrica (contrato do Remotion/Manim).

### RN-012 — Determinismo

A mesma entrada (após normalização para frações) gera exatamente o mesmo *trace*. O *trace* inclui `hash` SHA-256 da entrada normalizada.

### RN-013 — *Trace* (schema v1)

```json
{
  "versao": 1,
  "hash": "<sha256>",
  "entrada": {"n": 3, "A": [["3","-2","1"],["-1","3","-2"],["1","-4","1"]], "K": ["-2","-3","-4"], "metodo": "ambos", "rotulos": ["x","y","z"]},
  "passos": [
    {
      "id": 1,
      "tipo": "forma_matricial | determinante | sarrus | substituir_coluna | operacao_elementar | classificacao | solucao | verificacao | aviso",
      "titulo": "Dz: a coluna de z é substituída por K",
      "texto": "Frase lida pelo leitor de tela e usada como legenda",
      "matriz": [["3","-2","-2"],["-1","3","-3"],["1","-4","-4"]],
      "destaques": {"colunas": [{"indice": 2, "papel": "k"}], "linhas": [], "diagonais": []},
      "operacao": null,
      "valor": "-60"
    }
  ],
  "resultado": {"classificacao": "SPD", "posto_A": 3, "posto_AK": 3, "D": "-12", "solucao": ["-1","2","5"], "parametros": []}
}
```

- Números sempre como texto de fração (`"-7/2"`) para não perder exatidão no JSON.
- `destaques.colunas[].papel` ∈ {`x`, `y`, `z`, `k`, `copia`}; `destaques.linhas[].papel` ∈ {`pivo`, `alvo`}; `destaques.diagonais[].sinal` ∈ {`+`, `−`}.
- `operacao` (só em `operacao_elementar`): `{"codigo": "E3", "alvo": 2, "pivo": 1, "fator": "2"}`.
- Mudança incompatível no schema incrementa `versao` e exige atualização simultânea do resolver web, do Remotion e das cenas Manim.

### RN-014 — Link compartilhável

`/resolver/?n=2&metodo=ambos&a11=2&a12=3&a21=-1&a22=2&k1=4&k2=5` — um parâmetro por coeficiente (`aij`) e por termo independente (`ki`), mais `n` e `metodo`. É o mesmo formato enviado pelo formulário (funciona sem JavaScript); frações usam `/` codificado na URL. Parâmetros inválidos levam ao formulário com erro (HTTP 400), nunca a 500.

---

### RN-022 — Sistema digitado como equações

- Uma equação por linha (ou separadas por `;`); 2 linhas = sistema 2×2; 3 linhas = 3×3.
- **Incógnitas: qualquer letra.** Cada letra é uma incógnita; `2a + 3b = 4` é tratado como `2x + 3y = 4`.
  - Só x, y, z (ou parte delas): as incógnitas são x, y[, z], e uma letra ausente em todas as
    equações vale coeficiente 0 (ex.: 3 equações só com x e y).
  - Outras letras: são tantas quanto as equações, em **ordem alfabética** (a, b, c → colunas 1, 2, 3).
    Mais letras que equações, ou menos, é erro ("Há 3 incógnitas (w, x, y) para 2 equações").
  - As cores seguem a **coluna**, não a letra: a 1ª incógnita é sempre azul, a 2ª verde, a 3ª laranja.
  - As letras aparecem em toda a resolução (cabeçalhos, `Da`, `a = Da / D`, verificação, .txt) e
    seguem no modo Matriz e no link (campo `incognitas`, ex.: `a,b,c`; valor inválido volta a x, y, z).
  - Os parâmetros do SPI (t, s, …) nunca repetem uma letra usada como incógnita.
- Lado esquerdo: soma de termos `coeficiente·variável`, em qualquer ordem; coeficiente omitido vale 1 (`x`, `−y`); aceita `3x`, `3*x`, `3·x`, `(3/4)x`, `0,5z`; termos repetidos são somados; variável ausente vale 0. Maiúsculas e o sinal `−` são aceitos.
- Lado direito: um número (RN-001). Constantes à esquerda não são aceitas (`2x + 3 = 4` é erro).
- Erros indicam a equação: "Equação 2: não entendi o termo '…'". Limite de 300 caracteres.
- A leitura oficial é feita no servidor (`engine/equacoes.py`); depois de resolvido, a grade da matriz mostra os valores lidos.

## 4. Regras de negócio — apresentação

### RN-023 — Layout do resolver: barra superior e três quadrantes

**Barra superior** (parâmetros gerais, sem segunda barra): título da página, **Método** (vinculado ao formulário; trocar o método resolve de novo), **Exemplos** 2×2 e 3×3 (um clique) e **Copiar link**.

Quadrantes, que em telas largas (≥ 1200 px) ocupam juntos a primeira dobra, cada um com rolagem própria:

1. **Sistema**: botões **Equações | Matriz** (nessa ordem; o padrão é Matriz, com o "Sistema informado" abaixo da grade), ajuda de formatos e botão **Resolver** sempre visível.
2. **Matriz**: seções, progresso e **controles fixos no topo** (não mudam de lugar quando a conta cresce), título do passo, matriz animada e legenda.
3. **Conta**: botão **Salvar .txt** no topo; a conta do passo atual; e a **Resolução por método** (Sistema, Regra de Cramer, Escalonamento, Resultado) em blocos **recolhidos e expansíveis**, com o passo atual marcado.

Celular e tablet (< 1200 px): os quadrantes se empilham na mesma ordem, cada um como uma tela, com atalhos fixos **Sistema · Matriz · Conta**; ao resolver, a página vai direto ao quadrante Matriz. A barra superior recolhe no menu.

### RN-028 — Celular: tela dividida no passo a passo

Em telas com menos de 1200 px de largura e pelo menos 540 px de altura (celular e tablet em pé),
depois de resolver:

- A tela se divide: o 2º quadrante (matriz, controles e seções) fica **fixo** em cima, só com a
  altura de que precisa (no máximo 64% da tela); o 3º (conta) **rola** no restante. A página não rola.
- A divisória não salta entre os passos: o espaço dos produtos das diagonais fica reservado
  (1 linha no 2×2, 2 no 3×3) e a parte de cima nunca encolhe durante a resolução.
- A cada passo, só a metade de baixo se move, e volta ao topo para mostrar a explicação do passo.
  Nenhum passo muda o foco nem arrasta a página para outro quadrante.
- Sem faixa extra de atalhos: o botão **Editar**, no início da linha das seções (Editar, Sistema, Cramer…), pausa a
  resolução, libera os campos para uma nova consulta e abre o formulário em tela cheia; o
  botão **◫** ao lado de Resolver/Parar volta ao passo a passo (oculto depois de Parar).
- No celular (< 992 px), **Método** e **Exemplos** ficam dentro do 1º quadrante (no desktop seguem
  na barra superior); a barra superior fica mais baixa e os textos da resolução, mais leves.
- Celular (< 992 px), tela de edição:
  - abre sempre em **Equações** (o texto já traz o sistema atual; a resolução não é apagada);
  - quem chega sem sistema no link (página inicial, menu) cai **nela**; com sistema no link
    (Resolver, Avançar, exemplo), cai no passo a passo;
  - botões, nesta ordem: **Avançar** (contorno, ›) — passo a passo, parado, o usuário avança;
    **Resolver** (cheio, ▶) — reprodução automática; **■** Parar; **◫** voltar ao passo a passo.
    Só dicas (tooltip), sem textos explicativos. No desktop não há Avançar, e Enter continua
    acionando o Resolver.
  - **Exemplos** (2×2, 3×3) só **preenchem** o formulário e a tela fica na edição: a resolução
    anterior é limpa, as letras voltam a x, y, z, o campo preenchido (texto das equações ou células
    da matriz) recebe foco e um destaque, e o botão do exemplo escolhido fica marcado até a próxima
    edição. Quem resolve é o usuário (Avançar ou Resolver). No desktop, o exemplo resolve direto.
- **Parar** leva ao 1º quadrante, com os campos liberados para uma nova escolha; **Resolver** ou
  **Continuar** volta à tela dividida.
- Na metade de cima a matriz é compacta e a legenda de cores sai (ela está em "Como funciona").
- Em pé com pouca altura, deitado ou sem JavaScript, os quadrantes continuam empilhados, e mesmo
  assim a página não salta: a conta só rola quando tem rolagem própria.

### RN-024 — Salvar a resolução em .txt

- `GET /resolver/solucao.txt?…` (mesmos parâmetros do resolver) devolve `text/plain; charset=utf-8` como anexo `solucao-sistema-NxN.txt`.
- Conteúdo: cabeçalho (ordem, método, classificação, conjunto solução) e as seções numeradas por método; em cada passo, a matriz alinhada em texto (Sarrus com as colunas repetidas fora dos colchetes) e as contas (produtos, somas, D, operações, verificação).
- Gerado só a partir do *trace* (`apps/sistemas/relatorio.py`), com o mesmo rate limit do resolver.

### RN-015 — Convenção de cores por coluna

| Elemento | Token | Regra |
| :--- | :--- | :--- |
| Coluna/incógnita x | `--mat-x` | Mesma cor em todos os passos, na web, no Remotion e no Manim |
| Coluna/incógnita y | `--mat-y` | idem |
| Coluna/incógnita z | `--mat-z` | idem |
| Coluna K | `--mat-k` | Na matriz aumentada e quando entra no lugar de uma coluna (Dx, Dy, Dz) |
| Colunas repetidas no Sarrus | `--mat-*` atenuado + borda tracejada | Indicam cópia de C1 e C2 |
| Diagonal somada / subtraída | `success` / `danger` do tema | Com sinal "+" / "−" escrito ao lado |

Valores por tema e contraste: `PROJECT_SPEC.md` §4.2. Fonte única: `apps/sistemas/cores.py`.

### RN-016 — Destaque de linhas

- Linha pivô: fundo `--mat-pivo` atenuado + rótulo `Lᵢ (pivô)`.
- Linha alvo: borda `--mat-pivo` + rótulo `Lᵢ ←`, com a operação escrita ao lado.
- Linha zerada `0 = 0`: atenuada com rótulo "linha nula". Linha `0 = c` (c ≠ 0): borda `danger` + rótulo "contradição".

### RN-017 — Substituição de coluna (animação)

No passo `substituir_coluna`, a coluna original sai (desliza para fora e desbota), a coluna K entra no mesmo lugar e fica com borda `--mat-k` e rótulo `K → Cⱼ`. As outras colunas não se movem.

### RN-018 — Acessibilidade das cores

Nenhuma informação só por cor: sempre rótulo (x, y, z, K, Lᵢ, Cⱼ, +, −) e, quando houver, padrão de borda. Sob `prefers-reduced-motion`, as animações viram troca instantânea de estado.

---

### RN-025 — Rodízio da landing (round robin)

- Ordem: `ordem` crescente e, no empate, o número da variação; só as ativas entram.
- Um contador global (linha única, travada na transação) avança a cada acesso `GET` e escolhe
  `ativas[contador mod n]`. Alterar ordem ou ativas vale a partir do próximo acesso.
- Padrão: as 5 variações ativas, na ordem 1 a 5. O painel não deixa salvar sem nenhuma ativa;
  se mesmo assim nenhuma estiver ativa, a landing mostra a variação 1 sem registrar nada.
- Robôs e clientes sem navegador (agente vazio ou conhecido: bot, crawler, curl, prévias de link)
  e requisições `HEAD` não avançam o rodízio nem contam.
- A landing responde com `Cache-Control: no-cache, no-store`: cada acesso chega ao servidor.

### RN-026 — Medição do vídeo

- Cada acesso cria uma exibição (UUID). O UUID vai para a página e é a única autorização para
  enviar eventos a `/experimento/evento/` (POST sem CSRF, por `sendBeacon`; limite por IP).
- Eventos: `clique` (play na capa; cada replay conta), `progresso` (a cada 15 s em reprodução,
  ao pausar e ao sair da página) e `fim`.
- Tempo assistido = tempo em reprodução, somando replays. Os valores só crescem e são limitados:
  tempo ≤ tempo decorrido desde o acesso + 5 s; duração ≤ 4 h; cliques ≤ 50 por exibição.
- Eventos só valem até 12 h após o acesso. Token inválido ou vencido recebe `204` sem efeito
  (não revela quais existem).
- Concluiu: evento `fim` ou posição ≥ 95% da duração.
- Nenhum dado pessoal é guardado: nem IP, nem agente, nem cookie de rastreio.

### RN-027 — Painel do rodízio

- Rota `/experimento/` (e prévias `/experimento/previa/<n>/`): anônimo vai para o login; logado
  sem `site.experimento_gerenciar` recebe `403`. O link aparece só no menu de quem tem a permissão.
- Por variação: exibições, exibições com play (e taxa), cliques, tempo assistido total, média por
  play, % assistido (tempo ÷ duração, limitado a 100% por exibição, na média de quem deu play) e
  quantos foram até o fim. Períodos: hoje, 7 dias, 30 dias e tudo.
- A prévia mostra uma variação sem avançar o rodízio nem registrar exibição.

## 5. Regras de negócio — exemplos e vídeos

### RN-019 — Exemplos

- Estados: `rascunho → publicado → arquivado`; `publicado → rascunho`; `arquivado → rascunho`.
- Ao salvar: o motor recalcula *trace*, classificação e solução; esses campos não são editáveis.
- Publicar exige título e *trace* válido. Só `publicado` aparece na galeria.
- Professor edita/publica só os próprios; Administrador e Desenvolvedor, todos.
- Alterar coeficientes de um exemplo marca os vídeos existentes como obsoletos (deixam de aparecer até nova renderização).
- Exemplos iniciais (carga de dados): os casos de referência da §6.

### RN-020 — Renderização

- Formatos: `16x9` (1920×1080) e `9x16` (1080×1920).
- Estados: `pendente → renderizando → concluido`; `renderizando → falhou`; `falhou → pendente` (reprocessar); `pendente → cancelado`.
- No máximo uma renderização ativa (pendente ou renderizando) por exemplo + formato.
- Tempo máximo: `RENDER_MAX_SEGUNDOS`; ao estourar, `falhou` com motivo "tempo excedido".
- A cena Manim lê o *trace* gravado no exemplo; não recalcula.
- Rate limit: 10 solicitações por hora por usuário.

### RN-021 — Vídeos

- Um vídeo "atual" por exemplo + formato; o novo substitui o anterior (o arquivo antigo é removido após a troca).
- Vídeo de exemplo publicado é público; caso contrário, só autor e gestores.

---

## 6. Casos de referência (do caderno, 03/11/2026)

| Caso | Sistema | Resultado esperado |
| :--- | :--- | :--- |
| a) 2×2 | `2x + 3y = 4; −x + 2y = 5` | D = 7; Dx = −7; Dy = 14; S = {(−1, 2)}; SPD |
| b) 2×2 | `23x − y = 750; 15x − y = −450` | D = −8; Dx = −1200; Dy = −21600; S = {(150, 2700)}; SPD |
| c) 2×2 | `x + y = 43; x − y = 11` | D = −2; S = {(27, 16)}; SPD |
| Ordem 3, ex. 1 | `3x − 2y + z = −2; −x + 3y − 2z = −3; x − 4y + z = −4` | D = −12 (+17 − 29); Dx = 12; Dy = −24; Dz = −60; S = {(−1, 2, 5)}; SPD |
| Problema dos servidores | `x + y = 12; 150x + 300y = 2550` (x = básicos, y = avançados) | D = 150; S = {(7, 5)}; SPD |
| Escalonamento SPI | `x + 2y − z = 4; 2x − y + 3z = 9; 3x + y + 2z = 13` | posto(A) = posto([A\|K]) = 2 < 3; SPI com 1 parâmetro |
| Variante SI | Mesmo sistema com K3 = 10 | posto(A) = 2 < posto([A\|K]) = 3; SI |
| Contraexemplo de Cramer | `x + y + z = 1; x + y + z = 2; x + y + z = 3` | D = Dx = Dy = Dz = 0; posto 1 < 2; SI |

| Ordem 3, ex. 2 | `x − y − 3z = 49; x + 3y + z = 153; −2x + 0y + 5z = 24` | D = 4; Dx = 1692; Dy = −592; Dz = 696; S = {(423, −148, 174)}; SPD |

Anotações do caderno tratadas como erro de cópia (vale a formulação correta acima):

- Exercício b): a 2ª equação é `15x − y = −450`, coerente com os determinantes e com S = {(150, 2700)}.
- Dz do 3×3: a forma correta é `[a11 a12 K1; a21 a22 K2; a31 a32 K3]` (RN-006); a forma transposta anotada não é usada.
- Ordem 3, ex. 2: a resposta anotada (31,5; 34,7; 17,4) não satisfaz a 1ª equação; vale a solução exata calculada pelo motor, (423, −148, 174).
