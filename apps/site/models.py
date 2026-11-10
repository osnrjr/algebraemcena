"""Rodízio (round robin) de layouts da página inicial e medição do vídeo de apresentação.

Cada acesso à landing recebe a próxima variação ativa, na ordem definida no painel
(/experimento/, permissão `site.experimento_gerenciar`). Cada acesso vira uma ExibicaoLanding,
que acumula os cliques no vídeo e o tempo assistido enviados pelo navegador.
"""

from django.db import models

from apps.core.models import UUIDModel


class VarianteLanding(models.Model):
    """Um layout da landing. `numero` liga a linha ao bloco do template site/_landing_variantes.html."""

    numero = models.PositiveSmallIntegerField('número', unique=True)
    nome = models.CharField(max_length=80)
    descricao = models.CharField('descrição', max_length=200, blank=True)
    ativa = models.BooleanField(default=True)
    ordem = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['ordem', 'numero']
        verbose_name = 'variação da página inicial'
        verbose_name_plural = 'variações da página inicial'
        permissions = [
            ('experimento_gerenciar', 'Pode gerenciar o rodízio da página inicial e ver as estatísticas'),
        ]

    def __str__(self):
        return f'{self.numero}. {self.nome}'


class RodizioLanding(models.Model):
    """Linha única (pk=1) com o contador global de acessos que decide a próxima variação."""

    contador = models.PositiveBigIntegerField(default=0)

    class Meta:
        verbose_name = 'estado do rodízio'


class ExibicaoLanding(UUIDModel):
    """Um acesso à landing. O UUID vai para a página e autoriza o envio dos eventos do vídeo."""

    variante = models.ForeignKey(VarianteLanding, on_delete=models.PROTECT, related_name='exibicoes')
    criada_em = models.DateTimeField(auto_now_add=True, db_index=True)
    atualizada_em = models.DateTimeField(auto_now=True)
    cliques = models.PositiveIntegerField(default=0)
    segundos_assistidos = models.FloatField(default=0)
    posicao_maxima = models.FloatField('posição máxima (s)', default=0)
    duracao_video = models.FloatField('duração do vídeo (s)', default=0)
    concluiu = models.BooleanField(default=False)

    class Meta:
        ordering = ['-criada_em']
        verbose_name = 'exibição da página inicial'
        verbose_name_plural = 'exibições da página inicial'
