from django.db import migrations

VARIANTES = [
    (1, 'Ao lado do título', 'O player ocupa o lugar do cartão de exemplo no topo, ao lado do texto.'),
    (2, 'Destaque sob o título', 'Texto centralizado e o player grande logo abaixo, ainda no topo.'),
    (3, 'Seção dedicada', 'Topo como antes; seção “Veja a álgebra entrar em cena” com o roteiro ao lado do player.'),
    (4, 'Faixa de cinema', 'Faixa de ponta a ponta logo após o topo, com o player largo.'),
    (5, 'Cartão + janela', 'Miniatura discreta sob os botões; o vídeo abre numa janela sobre a página.'),
]


def criar(apps, schema_editor):
    Variante = apps.get_model('site', 'VarianteLanding')
    Rodizio = apps.get_model('site', 'RodizioLanding')
    for numero, nome, descricao in VARIANTES:
        Variante.objects.update_or_create(numero=numero, defaults={
            'nome': nome, 'descricao': descricao, 'ativa': True, 'ordem': numero})
    Rodizio.objects.get_or_create(pk=1)


def remover(apps, schema_editor):
    apps.get_model('site', 'VarianteLanding').objects.filter(numero__in=[v[0] for v in VARIANTES]).delete()
    apps.get_model('site', 'RodizioLanding').objects.filter(pk=1).delete()


class Migration(migrations.Migration):
    dependencies = [('site', '0001_experimento_landing')]
    operations = [migrations.RunPython(criar, remover)]
