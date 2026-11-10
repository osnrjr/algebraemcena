# apps.core

Utilitários transversais, sem regra de negócio.

- `models.UUIDModel`: base abstrata com PK UUIDv4 (Doc ① §10.4).
- `ratelimit`: rate limit por IP com o cache do Django (`limitar_por_ip(escopo, 'RATELIMIT_*')`), resposta 429 com `Retry-After`.

Depende de: nada.
