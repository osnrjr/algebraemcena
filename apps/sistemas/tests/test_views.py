from django.core.cache import cache
from django.db import connection
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from apps.sistemas import cores
from apps.sistemas.exemplos_rapidos import exemplo_3x3_linha3, parametros


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

    def test_exemplo_3x3_linha3_e_atributo_data_na_grade(self):
        esperado = {'a31': '1', 'a32': '-4', 'a33': '1', 'k3': '-4'}
        self.assertEqual(exemplo_3x3_linha3(), esperado)
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'data-exemplo-l3=')
        self.assertContains(r, '&quot;a31&quot;: &quot;1&quot;')
        self.assertContains(r, '&quot;k3&quot;: &quot;-4&quot;')

    def test_botao_resolver_com_id_e_rotulo(self):
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'id="btn-resolver"')
        self.assertContains(r, 'class="rotulo-resolver"')

    def test_elementos_de_travamento_e_limpeza_de_resolucao(self):
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'id="status-travado"')
        self.assertContains(r, 'id="btn-parar"')
        self.assertContains(r, 'id="cena-placeholder"')
        self.assertContains(r, 'id="conta-placeholder"')
        self.assertContains(r, 'abas-entrada')

    def test_resolucao_por_metodo_recolhida(self):
        r = self.client.get(self.url, parametros([[3, -2, 1], [-1, 3, -2], [1, -4, 1]], [-2, -3, -4]))
        html = r.content.decode()
        self.assertContains(r, 'id="btn-parar"')
        self.assertContains(r, 'id="btn-cena-parar"')
        self.assertContains(r, 'class="metodo-passo-corpo"')
        self.assertContains(r, 'role="button"')
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

    def test_incognitas_com_outras_letras(self):
        """RN-022: a, b, c funcionam como x, y, z; a grade, o link e o .txt seguem as letras."""
        dados = {'entrada': 'equacoes', 'metodo': 'ambos',
                 'equacoes': '3a - 2b + c = -2\n-a + 3b - 2c = -3\na - 4b + c = -4'}
        r = self.client.get(self.url, dados)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'S = {(\u22121, 2, 5)}')
        self.assertContains(r, '<span class="col-x-texto">a</span>')
        self.assertContains(r, 'data-incognitas="a,b,c"')
        self.assertContains(r, 'name="incognitas" value="a,b,c"')
        self.assertContains(r, 'incognitas=a%2Cb%2Cc')
        self.assertContains(r, 'Coeficiente de b na equação 1')
        txt = self.client.get(reverse('sistemas:solucao_txt'), dados).content.decode()
        self.assertIn('a = Da / D', txt)
        self.assertNotIn('Dx', txt)

    def test_modo_matriz_mantem_as_letras(self):
        dados = parametros([[2, 3], [-1, 2]], [4, 5])
        dados.update({'entrada': 'matriz', 'incognitas': 'm,n,o'})
        r = self.client.get(self.url, {k: str(v) for k, v in dados.items()})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['trace']['entrada']['rotulos'], ['m', 'n'])
        self.assertContains(r, '<span class="col-y-texto">n</span>')

    def test_incognitas_invalidas_voltam_para_x_y_z(self):
        dados = parametros([[2, 3], [-1, 2]], [4, 5])
        dados.update({'entrada': 'matriz', 'incognitas': '<script>'})
        r = self.client.get(self.url, {k: str(v) for k, v in dados.items()})
        self.assertEqual(r.context['trace']['entrada']['rotulos'], ['x', 'y'])

    def test_link_por_equacoes_sem_ordem(self):
        dados = {'entrada': 'equacoes', 'metodo': 'cramer', 'equacoes': '2x+3y=4\n-x+2y=5'}
        r = self.client.get(self.url, dados)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'S = {(\u22121, 2)}')
        self.assertEqual(self.client.get(reverse('sistemas:trace'), dados).status_code, 200)
        self.assertEqual(self.client.get(reverse('sistemas:solucao_txt'), dados).status_code, 200)

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


class ApresentacaoFormalViewTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_txt_traz_a_forma_formal_e_o_resumo(self):
        dados = {'entrada': 'equacoes', 'metodo': 'escalonamento',
                 'equacoes': 'x + 2y - z = 4\n2x - y + 3z = 9\n3x + y + 2z = 13'}
        txt = self.client.get(reverse('sistemas:solucao_txt'), dados).content.decode()
        self.assertIn('Classificação: SPI (infinitas soluções)    S = {(22/5 − z, −1/5 + z, z) | z ∈ ℝ}', txt)
        self.assertIn('ou S = {(22/5 − t, −1/5 + t, t) | t ∈ ℝ}', txt)
        self.assertIn('tal que z pertence aos reais', txt)
        self.assertIn('► SPI — Infinitas: S = {(f(z), g(z), z) | z ∈ ℝ}', txt)
        self.assertIn('· SI — Nenhuma: S = { } ou S = ∅', txt)

    def test_pagina_mostra_a_leitura_no_bloco_resultado(self):
        r = self.client.get(reverse('sistemas:resolver'))
        self.assertContains(r, 'O conjunto solução tem um único par ordenado (x, y): x = −1 e y = 2.')
