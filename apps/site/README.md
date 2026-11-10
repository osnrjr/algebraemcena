# apps.site

Landing (`/`), "Como funciona" (`/como-funciona/`) e tema (`/tema.css`).

## Landing em rodízio e vídeo de apresentação (RF-016, RN-025 a RN-027)

- `site/_landing_variantes.html`: os 5 layouts (bloco por `variante`); o resto da página é comum.
- `site/_player_video.html` + `static/js/player-video.js` + `static/css/player-video.css`: player
  do YouTube (youtube-nocookie) com controles próprios; o id vem de `VIDEO_APRESENTACAO_ID`.
- `experimento.py`: rodízio (`proxima_variante`), eventos (`registrar_evento`) e agregados.
- Modelos: `VarianteLanding` (número, nome, ativa, ordem), `RodizioLanding` (contador global),
  `ExibicaoLanding` (um acesso: cliques, segundos assistidos, posição máxima, duração, concluiu).
- `static/js/experimento.js`: envia clique/progresso/fim por `sendBeacon`.
- Painel `/experimento/` e prévias `/experimento/previa/<n>/`: `site.experimento_gerenciar`
  (superusuário tem). Para dar acesso a outra pessoa: admin → usuário → permissões →
  "Pode gerenciar o rodízio da página inicial e ver as estatísticas".
- Nova variação: bloco no template + linha em `VarianteLanding` (migração de dados).

- `temas.py`: presets habilitados (T05, T08, T09; padrão T08 via `TEMA_PADRAO`), geração do CSS de tokens `--tema-*`.
- Extensões de tokens por `settings.TEMA_EXTENSOES` (ex.: `apps.sistemas.cores.tokens_css` emite `--mat-*`, ADR-006).
- `context_processors.tema`: contrato do PROJECT_SPEC Anexo A.5; nunca levanta exceção.

Pendente (M6): tema configurável no banco (`site.tema_editar`), visibilidade pública (`site.visibilidade_publica`), perguntas frequentes, onboarding.

Depende de: `core`.
