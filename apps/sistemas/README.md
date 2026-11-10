# apps.sistemas

Motor de cálculo e resolver público (RF-001 a RF-009; regras em `regras_de_negocio.md`).

## Estrutura

- `engine/` — **Python puro, sem Django** (ADR-001):
  - `numeros.py`: leitura de inteiros, decimais e frações (RN-001) e exibição exata (RN-002).
  - `equacoes.py`: `ler_sistema(texto)` lê o sistema digitado como equações (RN-022).
  - `determinante.py`: produto cruzado 2×2, Sarrus 3×3 com memória de cálculo, substituição de coluna (RN-004 a RN-006).
  - `escalonamento.py`: operações E1–E4, posto, classificação SPD/SPI/SI, forma reduzida e solução geral (RN-008 a RN-010).
  - `trace.py`: `resolver(A, K, metodo, rotulos)` monta o *trace* v1 (RN-013), contrato da web, do Remotion e do Manim.
- `cores.py` — fonte única das cores `--mat-*` (ADR-006); `tokens_css` alimenta o `/tema.css`, `exportar_json` alimenta Remotion/Manim.
- `relatorio.py` — resolução agrupada por método (3º quadrante) e texto do `.txt` (RN-024), só a partir do *trace*.
- `forms.py` — `SistemaForm`: modo `equacoes` (texto) ou `matriz` (grade 3×3 + K; usa as n primeiras linhas/colunas). O campo `metodo` fica na barra superior, ligado ao formulário pelo atributo `form`.
- `views.py` — `/resolver/` (página), `/resolver/trace.json` (JSON) e `/resolver/solucao.txt` (anexo). Todos GET, sem gravação, rate limit 30/min por IP.
- `static/sistemas/js/passo-a-passo.js` — anima o *trace*: troca de coluna (Dx, Dy, Dz), diagonais de Sarrus, operações nas linhas, classificação e verificação. Respeita `prefers-reduced-motion`.

## Uso do motor

```python
from apps.sistemas.engine import resolver
trace = resolver([[2, 3], [-1, 2]], [4, 5], metodo='cramer')
trace['resultado']  # {'classificacao': 'SPD', 'solucao': ['-1', '2'], ...}
```

## Testes

```bash
python manage.py test apps.sistemas
```

Depende de: `core` (rate limit). Nenhum modelo de banco.
