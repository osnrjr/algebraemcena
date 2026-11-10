import uuid
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from . import experimento
from .models import ExibicaoLanding, RodizioLanding, VarianteLanding
from .templatetags.experimento_tags import duracao, percentual

NAVEGADOR = {'HTTP_USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/142.0 Safari/537.36'}


def variante_servida(resposta):
    return resposta.context['variante']


class LandingRodizioTests(TestCase):
    def test_rodizio_passa_por_todas_na_ordem_e_recomeca(self):
        vistas = [variante_servida(self.client.get('/', **NAVEGADOR)) for _ in range(7)]
        self.assertEqual(vistas, [1, 2, 3, 4, 5, 1, 2])
        self.assertEqual(ExibicaoLanding.objects.count(), 7)

    def test_ordem_e_ativas_do_painel_valem(self):
        VarianteLanding.objects.filter(numero__in=[1, 2]).update(ativa=False)
        VarianteLanding.objects.filter(numero=5).update(ordem=0)
        vistas = [variante_servida(self.client.get('/', **NAVEGADOR)) for _ in range(4)]
        self.assertEqual(vistas, [5, 3, 4, 5])

    def test_robo_nao_avanca_nem_conta(self):
        for agente in ['Googlebot/2.1', 'curl/8.5', '']:
            self.client.get('/', HTTP_USER_AGENT=agente)
        self.assertEqual(ExibicaoLanding.objects.count(), 0)
        self.assertEqual(RodizioLanding.objects.get(pk=1).contador, 0)

    def test_pagina_leva_o_token_da_exibicao_e_nao_vai_para_cache(self):
        resposta = self.client.get('/', **NAVEGADOR)
        exibicao = ExibicaoLanding.objects.get()
        self.assertContains(resposta, f'data-exibicao="{exibicao.pk}"')
        self.assertContains(resposta, 'js/experimento.js')
        self.assertIn('no-cache', resposta['Cache-Control'])

    def test_sem_variacao_ativa_mostra_a_primeira_sem_registrar(self):
        VarianteLanding.objects.update(ativa=False)
        resposta = self.client.get('/', **NAVEGADOR)
        self.assertEqual(variante_servida(resposta), 1)
        self.assertNotContains(resposta, 'data-exibicao=')

    def test_csp_libera_somente_o_player_do_youtube(self):
        csp = self.client.get('/', **NAVEGADOR)['Content-Security-Policy']
        self.assertIn('frame-src https://www.youtube-nocookie.com', csp)
        self.assertIn('https://www.youtube.com', csp)


class EventoTests(TestCase):
    def setUp(self):
        cache.clear()
        self.exibicao = ExibicaoLanding.objects.create(variante=VarianteLanding.objects.get(numero=3))
        # Simula 10 min na página, para o teto "tempo assistido <= tempo decorrido" não interferir.
        ExibicaoLanding.objects.filter(pk=self.exibicao.pk).update(criada_em=timezone.now() - timedelta(minutes=10))
        self.url = reverse('site:experimento_evento')

    def enviar(self, **dados):
        return self.client.post(self.url, {'token': str(self.exibicao.pk), **dados})

    def test_clique_e_progresso(self):
        self.assertEqual(self.enviar(evento='clique').status_code, 204)
        self.enviar(evento='clique')
        self.enviar(evento='progresso', segundos='90.5', posicao='92', duracao='323')
        self.enviar(evento='progresso', segundos='40', posicao='30', duracao='323')   # atrasado: não diminui
        e = ExibicaoLanding.objects.get()
        self.assertEqual(e.cliques, 2)
        self.assertEqual(e.segundos_assistidos, 90.5)
        self.assertEqual(e.posicao_maxima, 92)
        self.assertEqual(e.duracao_video, 323)
        self.assertFalse(e.concluiu)

    def test_fim_marca_conclusao(self):
        self.enviar(evento='fim', segundos='323', posicao='323', duracao='323')
        self.assertTrue(ExibicaoLanding.objects.get().concluiu)

    def test_tempo_impossivel_e_limitado_ao_tempo_na_pagina(self):
        self.enviar(evento='progresso', segundos='999999', posicao='-5', duracao='99999999')
        e = ExibicaoLanding.objects.get()
        self.assertLessEqual(e.segundos_assistidos, 10 * 60 + 6)
        self.assertEqual(e.posicao_maxima, 0)
        self.assertEqual(e.duracao_video, experimento.DURACAO_MAXIMA)

    def test_token_desconhecido_ou_vencido_nao_altera_nada(self):
        self.assertEqual(self.client.post(self.url, {'token': str(uuid.uuid4()), 'evento': 'clique'}).status_code, 204)
        ExibicaoLanding.objects.filter(pk=self.exibicao.pk).update(criada_em=timezone.now() - timedelta(hours=13))
        self.enviar(evento='clique')
        self.assertEqual(ExibicaoLanding.objects.get().cliques, 0)

    def test_evento_invalido_e_get(self):
        self.assertEqual(self.enviar(evento='hackear').status_code, 400)
        self.assertEqual(self.client.post(self.url, {'evento': 'clique'}).status_code, 400)
        self.assertEqual(self.client.get(self.url).status_code, 405)

    @override_settings(RATELIMIT_EXPERIMENTO='2/m')
    def test_limite_por_ip(self):
        self.enviar(evento='clique')
        self.enviar(evento='clique')
        self.assertEqual(self.enviar(evento='clique').status_code, 429)


class EstatisticasTests(TestCase):
    def test_agregados_por_variacao(self):
        v1 = VarianteLanding.objects.get(numero=1)
        ExibicaoLanding.objects.create(variante=v1)                                    # sem play
        ExibicaoLanding.objects.create(variante=v1, cliques=2, segundos_assistidos=161.5, duracao_video=323)
        ExibicaoLanding.objects.create(variante=v1, cliques=1, segundos_assistidos=400, duracao_video=323,
                                       concluiu=True)                                   # replay: % limitado a 100
        linhas = {l['variante'].numero: l for l in experimento.estatisticas()}
        l1 = linhas[1]
        self.assertEqual((l1['exibicoes'], l1['com_play'], l1['cliques'], l1['concluiram']), (3, 2, 3, 1))
        self.assertAlmostEqual(l1['taxa_play'], 2 / 3)
        self.assertAlmostEqual(l1['segundos'], 561.5)
        self.assertAlmostEqual(l1['segundos_por_play'], 280.75)
        self.assertAlmostEqual(l1['percentual_medio'], 0.75)                           # (50% + 100%) / 2
        self.assertEqual(linhas[2]['exibicoes'], 0)
        self.assertIsNone(linhas[2]['percentual_medio'])
        total = experimento.total(list(linhas.values()))
        self.assertEqual(total['exibicoes'], 3)
        self.assertAlmostEqual(total['percentual_medio'], 0.75)

    def test_periodo(self):
        v = VarianteLanding.objects.get(numero=2)
        antiga = ExibicaoLanding.objects.create(variante=v)
        ExibicaoLanding.objects.filter(pk=antiga.pk).update(criada_em=timezone.now() - timedelta(days=40))
        ExibicaoLanding.objects.create(variante=v)
        _, desde = experimento.inicio_do_periodo('30d')
        self.assertEqual({l['variante'].numero: l['exibicoes'] for l in experimento.estatisticas(desde)}[2], 1)
        self.assertEqual(experimento.inicio_do_periodo('qualquer')[0], 'tudo')

    def test_filtros(self):
        self.assertEqual(duracao(3725.4), '1:02:05')
        self.assertEqual(duracao(65), '1:05')
        self.assertEqual(duracao(None), '—')
        self.assertEqual(percentual(0.4567), '45,7%')


class PainelTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.sem_permissao = User.objects.create_user('professor', password=None)
        self.gestor = User.objects.create_user('gestor', password=None)
        self.gestor.user_permissions.add(Permission.objects.get(codename='experimento_gerenciar'))
        self.url = reverse('site:experimento')

    def dados(self, ordens, ativas):
        variantes = list(VarianteLanding.objects.order_by('ordem', 'numero'))
        dados = {'form-TOTAL_FORMS': '5', 'form-INITIAL_FORMS': '5', 'form-MIN_NUM_FORMS': '0', 'form-MAX_NUM_FORMS': '1000'}
        for i, v in enumerate(variantes):
            dados[f'form-{i}-id'] = v.pk
            dados[f'form-{i}-ordem'] = ordens[v.numero]
            if v.numero in ativas:
                dados[f'form-{i}-ativa'] = 'on'
        return dados

    def test_anonimo_vai_para_o_login_e_sem_permissao_recebe_403(self):
        resposta = self.client.get(self.url)
        self.assertRedirects(resposta, f"{reverse('accounts:login')}?next={self.url}", fetch_redirect_response=False)
        self.client.force_login(self.sem_permissao)
        self.assertEqual(self.client.get(self.url).status_code, 403)
        self.assertEqual(self.client.get(reverse('site:experimento_previa', args=[1])).status_code, 403)

    def test_painel_mostra_estatisticas_e_proximo(self):
        ExibicaoLanding.objects.create(variante=VarianteLanding.objects.get(numero=4), cliques=1,
                                       segundos_assistidos=60, duracao_video=323)
        self.client.force_login(self.gestor)
        resposta = self.client.get(self.url, {'periodo': '7d'})
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'Faixa de cinema')
        self.assertContains(resposta, '1:00')
        self.assertContains(resposta, 'Próximo acesso: 1. Ao lado do título')

    def test_salvar_ordem_e_ativas(self):
        self.client.force_login(self.gestor)
        resposta = self.client.post(self.url, self.dados({1: 5, 2: 4, 3: 3, 4: 2, 5: 1}, ativas={5, 3}))
        self.assertEqual(resposta.status_code, 302)
        self.assertEqual([v.numero for v in experimento.ordenadas_ativas()], [5, 3])

    def test_nao_deixa_desativar_todas(self):
        self.client.force_login(self.gestor)
        resposta = self.client.post(self.url, self.dados({n: n for n in range(1, 6)}, ativas=set()))
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'pelo menos uma variação ativa')
        self.assertEqual(len(experimento.ordenadas_ativas()), 5)

    def test_previa_nao_conta_nem_avanca(self):
        self.client.force_login(self.gestor)
        resposta = self.client.get(reverse('site:experimento_previa', args=[4]), **NAVEGADOR)
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.context['variante'], 4)
        self.assertNotContains(resposta, 'data-exibicao=')
        self.assertEqual(ExibicaoLanding.objects.count(), 0)
        self.assertEqual(RodizioLanding.objects.get(pk=1).contador, 0)
        self.assertEqual(self.client.get(reverse('site:experimento_previa', args=[9])).status_code, 404)

    def test_link_do_menu_so_para_quem_tem_permissao(self):
        self.client.force_login(self.sem_permissao)
        self.assertNotContains(self.client.get(reverse('site:como_funciona')), self.url)
        self.client.force_login(self.gestor)
        self.assertContains(self.client.get(reverse('site:como_funciona')), self.url)
