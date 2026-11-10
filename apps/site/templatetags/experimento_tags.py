from django import template

register = template.Library()


@register.filter
def duracao(segundos):
    """3725.4 -> '1:02:05'; 65 -> '1:05'; None -> '—'."""
    if segundos is None:
        return '—'
    s = int(round(segundos))
    h, resto = divmod(s, 3600)
    m, s = divmod(resto, 60)
    return f'{h}:{m:02d}:{s:02d}' if h else f'{m}:{s:02d}'


@register.filter
def percentual(fracao):
    """0.4567 -> '45,7%'; None -> '—'."""
    if fracao is None:
        return '—'
    return f'{fracao * 100:.1f}%'.replace('.', ',')
