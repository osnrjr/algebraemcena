# apps.site

Landing (`/`), "Como funciona" (`/como-funciona/`) e tema (`/tema.css`).

- `temas.py`: presets habilitados (T05, T08, T09; padrão T08 via `TEMA_PADRAO`), geração do CSS de tokens `--tema-*`.
- Extensões de tokens por `settings.TEMA_EXTENSOES` (ex.: `apps.sistemas.cores.tokens_css` emite `--mat-*`, ADR-006).
- `context_processors.tema`: contrato do PROJECT_SPEC Anexo A.5; nunca levanta exceção.

Pendente (M6): tema configurável no banco (`site.tema_editar`), visibilidade pública (`site.visibilidade_publica`), perguntas frequentes, onboarding.

Depende de: `core`.
