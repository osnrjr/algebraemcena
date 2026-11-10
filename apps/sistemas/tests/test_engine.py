"""Testes do motor (PROJECT_SPEC §11; casos de referência em regras_de_negocio.md §6)."""

import json
from fractions import Fraction

from django.test import SimpleTestCase

from apps.sistemas.engine import ErroEntrada, ler_numero, ler_sistema, resolver
from apps.sistemas.engine.determinante import det, memoria_sarrus, substituir_coluna


def passos(trace, tipo):
    return [p for p in trace['passos'] if p['tipo'] == tipo]


def determinantes(trace):
    return {p['rotulo']: p['valor'] for p in passos(trace, 'determinante')}


class CasosDoCadernoTests(SimpleTestCase):
    def test_2x2_a(self):
        t = resolver([[2, 3], [-1, 2]], [4, 5], 'cramer')
        self.assertEqual(determinantes(t), {'D': '7', 'Dx': '-7', 'Dy': '14'})
        self.assertEqual(t['resultado']['solucao'], ['-1', '2'])
        self.assertEqual(t['resultado']['classificacao'], 'SPD')

    def test_2x2_b(self):
        t = resolver([[23, -1], [15, -1]], [750, -450], 'cramer')
        self.assertEqual(determinantes(t), {'D': '-8', 'Dx': '-1200', 'Dy': '-21600'})
        self.assertEqual(t['resultado']['solucao'], ['150', '2700'])

    def test_2x2_c(self):
        t = resolver([[1, 1], [1, -1]], [43, 11])
        self.assertEqual(determinantes(t)['D'], '-2')
        self.assertEqual(t['resultado']['solucao'], ['27', '16'])

    def test_3x3_sarrus_exemplo_1(self):
        t = resolver([[3, -2, 1], [-1, 3, -2], [1, -4, 1]], [-2, -3, -4], 'cramer')
        self.assertEqual(determinantes(t), {'D': '-12', 'Dx': '12', 'Dy': '-24', 'Dz': '-60'})
        self.assertEqual(t['resultado']['solucao'], ['-1', '2', '5'])
        d = passos(t, 'determinante')[0]
        mais = sum(Fraction(x['produto']) for x in d['diagonais'] if x['sinal'] == '+')
        menos = sum(Fraction(x['produto']) for x in d['diagonais'] if x['sinal'] == '-')
        self.assertEqual((mais, menos), (17, 29))

    def test_3x3_exemplo_2_formulacao_correta(self):
        t = resolver([[1, -1, -3], [1, 3, 1], [-2, 0, 5]], [49, 153, 24], 'cramer')
        self.assertEqual(determinantes(t), {'D': '4', 'Dx': '1692', 'Dy': '-592', 'Dz': '696'})
        self.assertEqual(t['resultado']['solucao'], ['423', '-148', '174'])

    def test_problema_dos_servidores(self):
        t = resolver([[1, 1], [150, 300]], [12, 2550], rotulos=['b', 'a'])
        self.assertEqual(t['resultado']['solucao'], ['7', '5'])

    def test_spi(self):
        t = resolver([[1, 2, -1], [2, -1, 3], [3, 1, 2]], [4, 9, 13])
        r = t['resultado']
        self.assertEqual((r['classificacao'], r['posto_A'], r['posto_AK']), ('SPI', 2, 2))
        self.assertEqual(r['parametros'], ['t'])
        self.assertTrue(passos(t, 'verificacao')[0]['ok'])

    def test_si(self):
        t = resolver([[1, 2, -1], [2, -1, 3], [3, 1, 2]], [4, 9, 10])
        r = t['resultado']
        self.assertEqual((r['classificacao'], r['posto_A'], r['posto_AK']), ('SI', 2, 3))
        self.assertEqual(r['conjunto'], 'S = ∅')
        escalonada = passos(t, 'forma_escalonada')[0]
        self.assertIn('contradicao', [l['papel'] for l in escalonada['linhas']])

    def test_d_zero_com_todos_dj_zero_nao_e_spi(self):
        A = [[1, 1, 1]] * 3
        K = [1, 2, 3]
        for j in range(3):
            self.assertEqual(det(substituir_coluna(A, j, K)), 0)
        t = resolver(A, K, 'cramer')
        self.assertEqual(t['resultado']['classificacao'], 'SI')
        self.assertEqual(len(passos(t, 'aviso')), 1)


class CramerTests(SimpleTestCase):
    def test_dz_mantem_colunas_no_lugar(self):
        A = [[1, 2, 3], [4, 5, 6], [7, 8, 10]]
        K = [11, 12, 13]
        self.assertEqual(substituir_coluna(A, 2, K), [[1, 2, 11], [4, 5, 12], [7, 8, 13]])

    def test_papeis_da_coluna_substituida(self):
        t = resolver([[2, 3], [-1, 2]], [4, 5], 'cramer')
        dx, dy = passos(t, 'substituir_coluna')
        self.assertEqual(dx['papeis'], ['k', 'y'])
        self.assertEqual(dy['papeis'], ['x', 'k'])
        self.assertEqual(dy['matriz'], [['2', '4'], ['-1', '5']])

    def test_sarrus_repete_duas_colunas(self):
        valor, diagonais, estendida, _ = memoria_sarrus([[Fraction(v) for v in l] for l in
                                                        [[3, -2, 1], [-1, 3, -2], [1, -4, 1]]])
        self.assertEqual(valor, -12)
        self.assertEqual(len(estendida[0]), 5)
        self.assertEqual(len(diagonais), 6)


class EscalonamentoTests(SimpleTestCase):
    def test_spd_por_escalonamento_coincide_com_cramer(self):
        t = resolver([[3, -2, 1], [-1, 3, -2], [1, -4, 1]], [-2, -3, -4], 'escalonamento')
        self.assertEqual(t['resultado']['solucao'], ['-1', '2', '5'])
        self.assertTrue(passos(t, 'operacao_elementar'))

    def test_pivo_preferido_e_um(self):
        t = resolver([[3, -2, 1], [-1, 3, -2], [1, -4, 1]], [-2, -3, -4], 'escalonamento')
        primeira = passos(t, 'operacao_elementar')[0]
        self.assertEqual(primeira['operacao']['codigo'], 'E1')

    def test_e4_evita_fracoes_na_ida(self):
        t = resolver([[2, 3], [3, 5]], [1, 2], 'escalonamento')
        op = passos(t, 'operacao_elementar')[0]
        self.assertEqual(op['operacao']['codigo'], 'E4')
        self.assertEqual(op['notacao'], 'L2 ← 2·L2 − 3·L1')
        self.assertEqual(t['resultado']['solucao'], ['-1', '1'])


class ResultadoTests(SimpleTestCase):
    def test_fracao_exata(self):
        t = resolver([[3, 0], [0, 3]], [1, 2])
        self.assertEqual(t['resultado']['solucao'], ['1/3', '2/3'])

    def test_verificacao_sempre_ok(self):
        sistemas = [
            ([[2, 3], [-1, 2]], [4, 5]),
            ([['1/2', '0,25'], [3, '-1,5']], ['7/4', 0]),
            ([[1, -1, -3], [1, 3, 1], [-2, '', 5]], [49, 153, 24]),
            ([[0, 1, 2], [1, 0, 3], [4, -3, 8]], [1, 2, 3]),
        ]
        for A, K in sistemas:
            for metodo in ('cramer', 'escalonamento', 'ambos'):
                with self.subTest(A=A, metodo=metodo):
                    t = resolver(A, K, metodo)
                    verificacao = passos(t, 'verificacao')
                    self.assertTrue(verificacao and verificacao[0]['ok'])

    def test_deterministico_e_serializavel(self):
        a = resolver([[1, 2, -1], [2, -1, 3], [3, 1, 2]], [4, 9, 13])
        b = resolver([['1', '2', '-1'], ['2', '-1', '3'], ['3', '1', '2']], ['4', '9', '13'])
        self.assertEqual(a, b)
        self.assertEqual(json.loads(json.dumps(a)), a)
        self.assertEqual(a['versao'], 1)

    def test_ids_sequenciais(self):
        t = resolver([[2, 3], [-1, 2]], [4, 5])
        self.assertEqual([p['id'] for p in t['passos']], list(range(1, len(t['passos']) + 1)))


class EntradaTests(SimpleTestCase):
    def test_formatos_aceitos(self):
        casos = {'4': 4, '-450': -450, '+3': 3, '31,5': Fraction(63, 2), '0.25': Fraction(1, 4),
                 '-7/2': Fraction(-7, 2), '−3': -3, '': 0, '  2 ': 2, ',5': Fraction(1, 2)}
        for texto, esperado in casos.items():
            with self.subTest(texto=texto):
                self.assertEqual(ler_numero(texto), esperado)

    def test_formatos_recusados(self):
        for texto in ['abc', '2+3', '1e3', '3/0', '1/-2', '0,1234567', '2000000', '1/2000000', 'x']:
            with self.subTest(texto=texto):
                with self.assertRaises(ErroEntrada):
                    ler_numero(texto)

    def test_ordem_invalida(self):
        with self.assertRaises(ErroEntrada):
            resolver([[1, 2, 3, 4]] * 4, [1, 2, 3, 4])
        with self.assertRaises(ErroEntrada):
            resolver([[1, 2], [3, 4]], [1, 2], 'magica')


class DiagonaisTests(SimpleTestCase):
    def test_contribuicoes_como_no_caderno(self):
        t = resolver([[3, -2, 1], [-1, 3, -2], [1, -4, 1]], [-2, -3, -4], 'cramer')
        d = passos(t, 'determinante')[0]
        mais = [x['contribuicao'] for x in d['diagonais'] if x['sinal'] == '+']
        menos = [x['contribuicao'] for x in d['diagonais'] if x['sinal'] == '-']
        self.assertEqual(mais, ['9', '4', '4'])
        self.assertEqual(menos, ['-3', '-24', '-2'])
        self.assertEqual((d['soma_mais'], d['soma_menos'], d['valor']), ('17', '-29', '-12'))

    def test_contribuicoes_2x2(self):
        t = resolver([[2, 3], [-1, 2]], [4, 5], 'cramer')
        d = passos(t, 'determinante')[0]
        self.assertEqual([x['contribuicao'] for x in d['diagonais']], ['4', '3'])
        self.assertEqual((d['soma_mais'], d['soma_menos']), ('4', '3'))


class EquacoesTests(SimpleTestCase):
    def test_sistema_2x2(self):
        A, K = ler_sistema('2x + 3y = 4\n-x + 2y = 5')
        self.assertEqual((A, K), ([[2, 3], [-1, 2]], [4, 5]))

    def test_sistema_3x3_com_variacoes(self):
        texto = '3x − 2y + z = −2; -X + 3*y - 2z = -3\n x - 4y + z = -4'
        A, K = ler_sistema(texto)
        self.assertEqual(A, [[3, -2, 1], [-1, 3, -2], [1, -4, 1]])
        self.assertEqual(K, [-2, -3, -4])

    def test_fracoes_decimais_ordem_livre_e_variavel_ausente(self):
        A, K = ler_sistema('(3/4)x + 0,5y = 1/2\ny + 2x + x = 3')
        self.assertEqual(A, [[Fraction(3, 4), Fraction(1, 2)], [3, 1]])
        self.assertEqual(K, [Fraction(1, 2), 3])
        A, _ = ler_sistema('x - y - 3z = 49\nx + 3y + z = 153\n-2x + 5z = 24')
        self.assertEqual(A[2], [-2, 0, 5])

    def test_erros(self):
        casos = ['', '2x + 3y = 4', '2x + 3y = 4\nx = 1\nx=2\nx=3', '2x + 3 = 4\nx + y = 1',
                 '2x -- y = 1\nx + y = 2', '2x + 3y = 4\nx + z = 1', '2x + y\nx + y = 1',
                 '2x + y = a\nx + y = 1', '2x = 1 = 2\nx + y = 1', '()x + y = 1\nx + y = 2']
        for texto in casos:
            with self.subTest(texto=texto):
                with self.assertRaises(ErroEntrada):
                    ler_sistema(texto)

    def test_mensagem_indica_a_equacao(self):
        with self.assertRaisesMessage(ErroEntrada, 'Equação 2'):
            ler_sistema('x + y = 1\nx + w = 2')
