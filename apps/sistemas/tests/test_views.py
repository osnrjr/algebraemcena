from django.core.cache import cache
from django.db import connection
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from apps.sistemas import cores
from apps.sistemas.exemplos_rapidos import parametros


class ResolverViewTests(TestCase):
    def setUp(self):
        cache.clear()
        self.url = reverse('sistemas:resolver')

    def test_pagina_inicial_abre_com_a_matriz_montada(self):
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'id="trace-data"')
        self.assertContains(r, 'Sistema informado')
        self.assertContains(r, '2x + 3y = 4')
        self.assertContains(r, '>Exemplos<')
        self.assertNotContains(r, 'Exemplos do caderno')
        self.assertNotContains(r, 'class="app-toolbar"')

    def test_barra_superior_com_parametros_gerais(self):
        html = self.client.get(self.url).content.decode()
        barra = html[html.index('<nav class="navbar'):html.index('</nav>', html.index('navbar-ferramentas'))]
        for trecho in ('Resolver sistema linear', 'name="metodo"', 'form="form-sistema"', '>2×2<',
                       '>3×3<', 'id="copiar-link"'):
            self.assertIn(trecho, barra)

    def test_equacoes_antes_de_matriz(self):
        html = self.client.get(self.url).content.decode()
        self.assertLess(html.index('for="entrada-equacoes"'), html.index('for="entrada-matriz"'))

    def test_resolucao_por_metodo_recolhida(self):
        r = self.client.get(self.url, parametros([[3, -2, 1], [-1, 3, -2], [1, -4, 1]], [-2, -3, -4]))
        html = r.content.decode()
        for nome in ('Regra de Cramer', 'Escalonamento', 'Resultado'):
            self.assertIn(f'<summary>{nome}', html)
        self.assertNotIn('<details class="metodo" data-secao="cramer" open', html)
        self.assertIn('Soma (+): +9 +4 +4 = 17', html)
        self.assertIn('solucao.txt?', html)

    def test_entrada_por_equacoes_monta_a_matriz(self):
        dados = {'entrada': 'equacoes', 'metodo': 'ambos', 'n': '2',
                 'equacoes': '3x - 2y + z = -2\n-x + 3y - 2z = -3\nx - 4y + z = -4'}
        r = self.client.get(self.url, dados)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'S = {(\u22121, 2, 5)}')
        self.assertContains(r, 'name="a33" value="1"')
        self.assertContains(r, 'class="grade-coeficientes ordem-3"')

    def test_equacoes_invalidas(self):
        r = self.client.get(self.url, {'entrada': 'equacoes', 'n': '2', 'metodo': 'ambos',
                                       'equacoes': '2x + 3 = 4\nx + y = 1'})
        self.assertEqual(r.status_code, 400)
        self.assertContains(r, 'Equação 1', status_code=400)

    def test_resolve_e_embute_trace(self):
        r = self.client.get(self.url, parametros([[2, 3], [-1, 2]], [4, 5]))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'id="trace-data"')
        self.assertContains(r, 'S = {(−1, 2)}')

    def test_resolver_nao_grava_nada(self):
        with CaptureQueriesContext(connection) as consultas:
            self.client.get(self.url, parametros([[1, 2, -1], [2, -1, 3], [3, 1, 2]], [4, 9, 13]))
        escritas = [q for q in consultas.captured_queries
                    if q['sql'].split()[0].upper() in ('INSERT', 'UPDATE', 'DELETE')]
        self.assertEqual(escritas, [])

    def test_entrada_invalida_400_sem_500(self):
        dados = parametros([[2, 3], [-1, 2]], [4, 5])
        dados['a11'] = 'abc'
        r = self.client.get(self.url, dados)
        self.assertEqual(r.status_code, 400)
        self.assertContains(r, 'Use número inteiro', status_code=400)
        r = self.client.get(self.url, {'n': '4'})
        self.assertEqual(r.status_code, 400)

    def test_post_nao_permitido(self):
        self.assertEqual(self.client.post(self.url).status_code, 405)

    @override_settings(RATELIMIT_RESOLVER='2/m')
    def test_rate_limit(self):
        dados = parametros([[2, 3], [-1, 2]], [4, 5])
        self.assertEqual(self.client.get(self.url, dados).status_code, 200)
        self.assertEqual(self.client.get(self.url, dados).status_code, 200)
        r = self.client.get(self.url, dados)
        self.assertEqual(r.status_code, 429)
        self.assertIn('Retry-After', r.headers)

    def test_trace_json(self):
        r = self.client.get(reverse('sistemas:trace'), parametros([[2, 3], [-1, 2]], [4, 5]))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['resultado']['solucao'], ['-1', '2'])
        r = self.client.get(reverse('sistemas:trace'), {'n': '2', 'a11': '1/0'})
        self.assertEqual(r.status_code, 400)

    def test_salvar_txt(self):
        dados = parametros([[3, -2, 1], [-1, 3, -2], [1, -4, 1]], [-2, -3, -4], 'cramer')
        r = self.client.get(reverse('sistemas:solucao_txt'), dados)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r['Content-Type'], 'text/plain; charset=utf-8')
        self.assertIn('attachment; filename="solucao-sistema-3x3.txt"', r['Content-Disposition'])
        texto = r.content.decode()
        for trecho in ('1. SISTEMA', '2. REGRA DE CRAMER', '3. RESULTADO', 'D = 17 \u2212 29 = \u221212',
                       'S = {(\u22121, 2, 5)}', 'L1:  [  3  \u22122   1  ]   3  \u22122'):
            self.assertIn(trecho, texto)
        self.assertNotIn('ESCALONAMENTO', texto)

    def test_salvar_txt_invalido(self):
        r = self.client.get(reverse('sistemas:solucao_txt'), {'n': '2', 'a11': 'abc', 'metodo': 'ambos'})
        self.assertEqual(r.status_code, 400)

    def test_csp_sem_unsafe_inline(self):
        r = self.client.get(self.url, parametros([[2, 3], [-1, 2]], [4, 5]))
        csp = r.headers['Content-Security-Policy']
        self.assertNotIn('unsafe-inline', csp)
        self.assertNotIn('unsafe-eval', csp)
        self.assertIn("frame-ancestors 'none'", csp)
        self.assertNotIn(' style="', r.content.decode())
        self.assertNotIn('onclick=', r.content.decode())


class TemaTests(TestCase):
    def test_tema_css_tem_tokens_de_matematica(self):
        r = self.client.get(reverse('site:tema_css'))
        self.assertEqual(r.status_code, 200)
        corpo = r.content.decode()
        for token in ('--tema-fundo', '--mat-x', '--mat-k', '--mat-pivo-rgb', '--sem-sobre'):
            self.assertIn(token, corpo)

    def test_contraste_das_cores_de_matematica(self):
        for slug, paleta in cores.CORES.items():
            for nome, hexa in paleta.items():
                with self.subTest(tema=slug, cor=nome):
                    self.assertGreaterEqual(cores.contraste(hexa, cores.FUNDOS[slug]),
                                            cores.CONTRASTE_MINIMO[slug])


class PaginasTests(TestCase):
    def test_paginas_publicas(self):
        for nome in ('site:landing', 'site:como_funciona', 'accounts:login', 'accounts:password_reset'):
            with self.subTest(pagina=nome):
                self.assertEqual(self.client.get(reverse(nome)).status_code, 200)

    def test_ordem_do_formulario_de_login(self):
        html = self.client.get(reverse('accounts:login')).content.decode()
        posicoes = [html.index(t) for t in ('name="username"', 'name="password"', '>Entrar</button>',
                                             'Esqueci minha senha')]
        self.assertEqual(posicoes, sorted(posicoes))

    def test_logout_so_por_post(self):
        self.assertEqual(self.client.get(reverse('accounts:logout')).status_code, 405)

    @override_settings(DEBUG=False)
    def test_404_personalizada(self):
        r = self.client.get('/nao-existe/')
        self.assertEqual(r.status_code, 404)
        self.assertContains(r, 'Nenhuma equação aponta para ela', status_code=404)
