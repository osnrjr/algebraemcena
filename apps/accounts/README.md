# apps.accounts

Usuário customizado (`accounts.User`, PK UUID), login e logout.

- Login local em `/conta/entrar/` (`accounts:login`), formulário na ordem do Doc ① §16.2, rate limit 5/min por IP.
- Logout só por POST (`accounts:logout`).
- Sem cadastro público: professores entram por convite (PROJECT_SPEC §9.1).

Pendente (M4): perfis/RBAC como dado (matriz), convite de professor, recuperação de senha, MFA para grupos 3 e 4.

Depende de: `core`.
