# Álgebra em Cena

> 🌐 **Acesse online:** [https://algebraemcena.pythonanywhere.com](https://algebraemcena.pythonanywhere.com)

Resolve sistemas lineares 2×2 e 3×3 **passo a passo**, com animações que destacam em cores as linhas e as colunas substituídas, e classifica o sistema como **SPD**, **SPI** ou **SI**.

Projeto Django `algebra_linear`. Status: **em desenvolvimento** — resolver público funcionando (marcos M0 a M2); player Remotion, exemplos do professor e vídeos Manim ainda por fazer (ver [Roteiro](#roteiro)).

---

## O que o sistema faz

- **Entrada do sistema** de duas formas:
  - **Equações**: uma por linha, por exemplo `3x − 2y + z = −2`; o sistema monta a matriz.
  - **Matriz**: grade [A | K] com o quadro "Sistema informado" atualizado enquanto se digita.
- **Contas exatas**: inteiros, decimais (`31,5`) e frações (`3/4`), sem arredondamento.
- **Regra de Cramer**: produto cruzado (2×2) e **Sarrus** (3×3), com cada diagonal traçada e o seu resultado escrito **abaixo da coluna onde ela termina**, como no caderno (`+9 +4 +4` e `−3 −24 −2`).
- **Dx, Dy, Dz**: a coluna da incógnita sai e a coluna K entra no mesmo lugar; as outras não se movem.
- **Escalonamento**: cada operação elementar (troca, multiplicação, combinação de linhas) é um passo, com linha pivô e linha alterada destacadas.
- **Classificação pelo posto** (Rouché–Capelli), nunca só por D = 0; solução geral com parâmetro no SPI.
- **Verificação** da solução substituindo em cada equação original.
- **Resolução por método** recolhível e **exportação em `.txt`** formatada.
- **Link compartilhável**: o sistema vai na URL; nada é gravado no servidor.

### Convenção de cores

| Elemento | Cor (tema T08 Noturno) |
| :--- | :--- |
| Coluna de x | azul `#7FC4F0` |
| Coluna de y | verde-água `#3FD1A6` |
| Coluna de z | laranja `#FF9A5C` |
| Coluna K (termos independentes) | amarelo `#F0E442` |
| Linha pivô / linha alterada | rosa `#E3A3C7` (contorno cheio / tracejado) |
| Diagonal somada / subtraída | verde / vermelho tracejado |

As cores vêm de uma fonte única ([apps/sistemas/cores.py](apps/sistemas/cores.py)), têm contraste validado por teste (≥ 4,5:1; ≥ 7:1 no tema Acessível) e sempre aparecem com rótulo (x, y, z, K, L1, C1, +, −).

### Classificação

| Condição | Resultado |
| :--- | :--- |
| posto(A) = posto([A\|K]) = n | **SPD** — solução única |
| posto(A) = posto([A\|K]) < n | **SPI** — infinitas soluções, com parâmetro |
| posto(A) < posto([A\|K]) | **SI** — nenhuma solução |

D = 0 não decide sozinho: `x + y + z = 1; x + y + z = 2; x + y + z = 3` tem D = Dx = Dy = Dz = 0 e é **impossível**.

---

## Tela do resolver

```
┌──────────────────────────── barra superior ─────────────────────────────┐
│ Álgebra em Cena · Resolver · Como funciona │ Método ▾ │ Exemplos 2×2 3×3 │
├───────────────┬──────────────────────────────┬──────────────────────────┤
│ 1. Sistema    │ 2. Matriz                    │ 3. Conta     [Salvar .txt]│
│ Equações|Matriz│ seções · progresso           │ conta do passo atual     │
│ grade [A | K] │ ⏮ ‹ ▶ › ⏭  (fixos no topo)    │ ─────────────────────────│
│ Sistema       │ matriz animada               │ Resolução por método     │
│ informado     │ resultados das diagonais     │ ▸ Sistema                │
│ [Resolver]    │ legenda                      │ ▸ Regra de Cramer  …     │
└───────────────┴──────────────────────────────┴──────────────────────────┘
```

Em telas largas os três quadrantes ocupam a primeira dobra. No celular e no tablet eles se empilham, com atalhos **Sistema · Matriz · Conta**. Teclado: **←** e **→** mudam de passo, **espaço** reproduz ou pausa.

---

## Tecnologias

| Camada | Escolha |
| :--- | :--- |
| Linguagem | Python 3.12+ (desenvolvido em 3.14) |
| Framework | Django 6.1 (CSP nativa) |
| Configuração | `django-environ` (`.env`) |
| Senhas | Argon2id (`argon2-cffi`) |
| Banco | SQLite no desenvolvimento; PostgreSQL previsto em produção |
| Front-end | Templates Django, Bootstrap 5.3.3 e Bootstrap Icons por CDN com SRI, JavaScript próprio sem build |
| Animação no navegador | JS/CSS próprio (atual); **Remotion** previsto (M3) |
| Vídeos | **Manim Community Edition** previsto (M5) |

---

## Como rodar

Ambiente de referência: WSL 2 (Ubuntu), projeto em `~/projetos/django/algebra_linear/` (nunca em `/mnt/c/`).

```bash
cd ~/projetos/django
git clone <url-do-repositorio> algebra_linear
cd algebra_linear
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Crie o `.env` a partir do modelo e preencha os valores locais:

```bash
cp .env.example .env
```

Valores mínimos para desenvolvimento:

```env
SECRET_KEY='<gere com o comando abaixo>'
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
CSRF_TRUSTED_ORIGINS=http://127.0.0.1:8000,http://localhost:8000
ADMIN_URL=painel-<valor-aleatorio>/
TENANCY_MODE=single
TEMA_PADRAO=t08
```

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

```bash
python -c "import secrets; print('painel-' + secrets.token_urlsafe(8) + '/')"
```

Banco, administrador e servidor:

```bash
python manage.py migrate
```

```bash
python manage.py createsuperuser
```

```bash
python manage.py runserver
```

Abra <http://127.0.0.1:8000/resolver/>. Se a porta 8000 estiver ocupada, use `python manage.py runserver 8001`.

### Variáveis de ambiente

| Variável | Uso |
| :--- | :--- |
| `SECRET_KEY` | Chave do Django, exclusiva do projeto |
| `DEBUG` | `True` só no desenvolvimento |
| `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS` | Hosts e origens permitidos |
| `ADMIN_URL` | Caminho não padrão do Django Admin (terminado em `/`) |
| `TENANCY_MODE` | `single` |
| `TEMA_PADRAO` | `t08` (Noturno), `t05` (Profissional) ou `t09` (Acessível) |
| `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL` | SMTP fora do desenvolvimento (no desenvolvimento os e-mails vão para o console) |
| `FIELD_ENCRYPTION_KEY` | Reservada para dados cifrados (Fernet) |
| `RENDER_*` | Reservadas para a fila de vídeos Manim (M5) |

---

## Uso

### Rotas

| Rota | O que faz |
| :--- | :--- |
| `/` | Landing (layouts em rodízio com o vídeo de apresentação) |
| `/resolver/` | Resolver passo a passo (abre com o exemplo 2×2 já resolvido) |
| `/resolver/trace.json?…` | Passos da resolução em JSON (contrato para Remotion e Manim) |
| `/resolver/solucao.txt?…` | Resolução completa em texto, como anexo |
| `/como-funciona/` | Legenda de cores, métodos e classificação |
| `/conta/entrar/` | Login de professores e administradores |

### Parâmetros da URL

```
/resolver/?entrada=matriz&n=2&metodo=ambos&a11=2&a12=3&k1=4&a21=-1&a22=2&k2=5
/resolver/?entrada=equacoes&metodo=cramer&equacoes=2x%2B3y%3D4%0A-x%2B2y%3D5
```

| Parâmetro | Valores |
| :--- | :--- |
| `entrada` | `matriz` ou `equacoes` |
| `metodo` | `ambos`, `cramer` ou `escalonamento` |
| `n` | `2` ou `3` (modo matriz) |
| `aij`, `ki` | coeficiente da linha i, coluna j, e termo independente da linha i |
| `equacoes` | uma equação por linha (modo equações) |

### Formato das equações

- 2 linhas = sistema 2×2 (x, y); 3 linhas = 3×3 (x, y, z). Linhas também podem ser separadas por `;`.
- Termos em qualquer ordem: `3x`, `3*x`, `(3/4)x`, `0,5z`, `x`, `−y`; variável ausente vale 0.
- À direita do `=`, um número. Constantes à esquerda (`2x + 3 = 4`) não são aceitas.

### Usando o motor em Python

O motor não depende do Django:

```python
from apps.sistemas.engine import ler_sistema, resolver

A, K = ler_sistema('3x - 2y + z = -2\n-x + 3y - 2z = -3\nx - 4y + z = -4')
trace = resolver(A, K, metodo='ambos')
trace['resultado']['classificacao']   # 'SPD'
trace['resultado']['conjunto']        # 'S = {(−1, 2, 5)}'
```

---

## Arquitetura

```
algebra_linear/
├── config/                 settings (django-environ, baseline de segurança, CSP), urls
├── apps/
│   ├── core/               UUIDModel, rate limit por IP
│   ├── accounts/           usuário com UUID, login/logout, recuperação de senha
│   ├── site/               landing, "Como funciona", temas e /tema.css
│   └── sistemas/
│       ├── engine/         motor puro: numeros, equacoes, determinante, escalonamento, trace
│       ├── cores.py        fonte única das cores --mat-*
│       ├── relatorio.py    resolução por método e .txt
│       ├── forms.py · views.py · urls.py
│       ├── static/sistemas/js/passo-a-passo.js   animação a partir do trace
│       └── tests/
├── templates/              casca (layouts/shell/topo.html), login, páginas de erro
├── static/css/base.css     estrutura que consome os tokens do tema
├── PROJECT_SPEC.md         especificação do produto e técnica (Doc ②)
└── regras_de_negocio.md    requisitos funcionais (RF) e regras de negócio (RN)
```

**O *trace* é o contrato único** ([ADR-001](PROJECT_SPEC.md)): o motor calcula uma vez e devolve a lista de passos em JSON (matrizes como frações em texto, papéis de cada coluna, linhas destacadas, diagonais com contribuição, operação elementar). A página web, o futuro player Remotion e as futuras cenas Manim só desenham esses passos. Mudança incompatível no formato incrementa a versão do *trace*.

Cada app tem o seu README: [core](apps/core/README.md) · [accounts](apps/accounts/README.md) · [site](apps/site/README.md) · [sistemas](apps/sistemas/README.md).

---

## Segurança

Segue o baseline do `AGENT_INSTRUCTIONS_DJANGO.md` (Doc ①):

- CSP imposta, sem `'unsafe-inline'` nem `'unsafe-eval'`; nenhum estilo ou script inline; `frame-ancestors 'none'`.
- Bootstrap por CDN com versão fixa e SRI.
- Cookies `Secure`/`HttpOnly`/`SameSite`, HTTPS e HSTS fora do desenvolvimento.
- Senhas com Argon2id; usuário com chave UUID; Admin em URL não padrão.
- Rate limit na aplicação: resolver e `.txt`/JSON 30/min por IP, login 5/min, recuperação de senha 3/h.
- Resolver *stateless*: o sistema digitado não é armazenado (LGPD mínima).

`python manage.py check --deploy` com `DEBUG=False` deixa apenas os avisos de HSTS para subdomínios e *preload*, que dependem do domínio de produção.

---

## Testes

```bash
python manage.py test apps
```

São 51 testes. Os principais:

- Casos de referência do caderno:
  - 2×2: (−1, 2), (150, 2700) e (27, 16);
  - 3×3: (−1, 2, 5) e (423, −148, 174);
  - problema dos servidores: (7, 5).
- SPI, SI e o contraexemplo de D = 0.
- Leitura de números e de equações, com os casos de erro.
- Resultados das diagonais e a montagem correta de Dz.
- Determinismo do *trace*.
- Views: resolver sem gravação no banco, rate limit, `.txt`, CSP, contraste das cores, ordem do formulário de login e 404 personalizada.

---

## Roteiro

| Marco | Entrega | Situação |
| :--- | :--- | :--- |
| M0 | Bootstrap do projeto, usuário UUID, baseline de segurança | Feito |
| M1 | Motor de cálculo exato + *trace* v1 | Feito |
| M2 | Resolver web passo a passo | Feito |
| M3 | Player **Remotion** embutido (exige Node no WSL — exceção EXC-001) | A fazer |
| M4 | Exemplos e problemas contextualizados do professor, galeria pública, matriz RBAC | A fazer |
| M5 | Vídeos MP4 com **Manim** (16:9 e 9:16) por fila de renderização | A fazer |
| M6 | Tema e visibilidade pública configuráveis, onboarding | A fazer |

Fora da v1: sistemas não quadrados e de ordem ≥ 4, contas de aluno, interpretação automática de enunciados em texto, login social.

---

## Documentação

| Documento | Conteúdo |
| :--- | :--- |
| [PROJECT_SPEC.md](PROJECT_SPEC.md) | Visão, escopo, perfis e RBAC, design e temas, topologia, dados, segurança, testes, ADRs e exceções |
| [regras_de_negocio.md](regras_de_negocio.md) | RF-001 a RF-015 e RN-001 a RN-024, com os casos de referência |
| `AGENT_INSTRUCTIONS_DJANGO.md` (Doc ①) e `DEV_ENVIRONMENT_GUIDELINES.txt` (Doc ③) | Padrões do ecossistema Django; ficam na pasta `~/projetos/django/` |

## Como contribuir

- Nunca trabalhar direto na `main`: uma branch por tarefa (`feat/…`, `fix/…`, `docs/…`).
- Mensagens no padrão [Conventional Commits](https://www.conventionalcommits.org/pt-br/), em português.
- Uma tarefa só está concluída quando cumpre a *Definition of Done* do [PROJECT_SPEC.md](PROJECT_SPEC.md) §12: testes, README da app e `.env.example` atualizados, sem estilo/JS inline.

## Licença

A definir.
