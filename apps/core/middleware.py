"""Cabeçalhos de segurança que o Django não envia sozinho (Doc ① §14).

Permissions-Policy: desliga os recursos do navegador que o produto não usa (câmera, microfone,
localização, pagamento…) e libera só o necessário — a própria página e o player do YouTube
(youtube-nocookie) para tela cheia, autoplay após o clique, mídia protegida e picture-in-picture.
A política vem de `settings.PERMISSIONS_POLICY` ({recurso: [origens]}; lista vazia = bloqueado).
"""

from django.conf import settings


def montar_permissions_policy(politica):
    """{'camera': [], 'fullscreen': ['self', 'https://x']} -> 'camera=(), fullscreen=(self "https://x")'."""
    partes = []
    for recurso, origens in politica.items():
        valores = ' '.join(o if o in ('self', '*') else f'"{o}"' for o in origens)
        partes.append(f'{recurso}=({valores})')
    return ', '.join(partes)


class PermissionsPolicyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        politica = getattr(settings, 'PERMISSIONS_POLICY', None)
        self.valor = montar_permissions_policy(politica) if politica else ''

    def __call__(self, request):
        resposta = self.get_response(request)
        if self.valor and 'Permissions-Policy' not in resposta:
            resposta['Permissions-Policy'] = self.valor
        return resposta
