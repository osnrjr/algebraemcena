# apps.sistemas

Motor de cálculo e resolver público (RF-001 a RF-009; regras em `regras_de_negocio.md`).

## Estrutura

- `engine/` — **Python puro, sem Django** (ADR-001):
  - `numeros.py`: leitura de inteiros, decimais e frações (RN-001) e exibição exata (RN-002).
  - `determinante.py`: produto cruzado 2×2, Sarrus 3×3 com memória de cálculo, substituição de coluna (RN-004 a RN-006).
  - `escalonamento.py`: operações E1–E4, posto, classificação SPD/SPI/SI, forma reduzida e solução geral (RN-008 a RN-010).
  - `trace.py`: `resolver(A, K, metodo, rotulos)` monta o *trace* v1 (RN-013), contrato da web, do Remotion e do Manim.
- `cores.py` — fonte única das cores `--mat-*` (ADR-006); `tokens_css` alimenta o `/tema.css`, `exportar_json` alimenta Remotion/Manim.
- `forms.py` — `SistemaForm` (grade 3×3 + K; usa as n primeiras linhas/colunas).
- `views.py` — `/resolver/` (página) e `/resolver/trace.json` (JSON). Ambos GET, sem gravação, rate limit 30/min por IP.
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
