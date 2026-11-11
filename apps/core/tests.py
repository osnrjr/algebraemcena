from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings

from apps.core.middleware import PermissionsPolicyMiddleware, montar_permissions_policy

NAVEGADOR = {'HTTP_USER_AGENT': 'Mozilla/5.0 (X11; Linux x86_64) Chrome/142.0 Safari/537.36'}


class PermissionsPolicyTests(SimpleTestCase):
    def test_formato_do_cabecalho(self):
        valor = montar_permissions_policy({'camera': [], 'fullscreen': ['self', 'https://player.exemplo']})
        self.assertEqual(valor, 'camera=(), fullscreen=(self "https://player.exemplo")')

    def test_nao_sobrescreve_cabecalho_definido_pela_view(self):
        from django.http import HttpResponse

        def view(request):
            resposta = HttpResponse()
            resposta['Permissions-Policy'] = 'camera=(self)'
            return resposta
        resposta = PermissionsPolicyMiddleware(view)(RequestFactory().get('/'))
        self.assertEqual(resposta['Permissions-Policy'], 'camera=(self)')


class CabecalhosDeSegurancaTests(TestCase):
    """Os seis cabeçalhos avaliados para nota A+ (securityheaders.com)."""

    def test_permissions_policy_bloqueia_recursos_e_libera_so_o_player(self):
        politica = self.client.get('/', **NAVEGADOR)['Permissions-Policy']
        for bloqueado in ('camera=()', 'microphone=()', 'geolocation=()', 'payment=()', 'usb=()'):
            self.assertIn(bloqueado, politica)
        for liberado in ('autoplay', 'fullscreen', 'encrypted-media', 'picture-in-picture'):
            self.assertIn(f'{liberado}=(self "https://www.youtube-nocookie.com")', politica)
        self.assertIn('clipboard-write=(self)', politica)

    def test_demais_cabecalhos(self):
        resposta = self.client.get('/', **NAVEGADOR)
        self.assertIn('Content-Security-Policy', resposta)
        self.assertEqual(resposta['X-Frame-Options'], 'DENY')
        self.assertEqual(resposta['X-Content-Type-Options'], 'nosniff')
        self.assertEqual(resposta['Referrer-Policy'], 'same-origin')

    @override_settings(SECURE_HSTS_SECONDS=31536000, SECURE_HSTS_INCLUDE_SUBDOMAINS=True, SECURE_SSL_REDIRECT=False)
    def test_hsts_de_um_ano_com_subdominios_em_https(self):
        resposta = self.client.get('/', secure=True, **NAVEGADOR)
        self.assertEqual(resposta['Strict-Transport-Security'], 'max-age=31536000; includeSubDomains')
