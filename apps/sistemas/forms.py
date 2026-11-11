from django import forms

import re
import string

from .engine import METODOS, ErroEntrada, ler_numero, ler_sistema_com_incognitas
from .engine.equacoes import LIMITE_TEXTO

ORDENS = [('2', '2×2'), ('3', '3×3')]
ENTRADAS = [('matriz', 'Matriz'), ('equacoes', 'Equações')]
NOMES_METODO = {'ambos': 'Cramer e escalonamento', 'cramer': 'Regra de Cramer',
                'escalonamento': 'Escalonamento'}
VARIAVEIS = ['x', 'y', 'z']
_RE_INCOGNITAS = re.compile(r'^[a-z](,[a-z]){0,2}$')


def completar_incognitas(letras, total=3):
    """Completa a lista de incógnitas até `total` letras (para a grade 3×3), sem repetir.

    Só x, y, z: completa com x, y, z. Outras letras: com as próximas do alfabeto (a, b → c).
    """
    letras = [l for l in (letras or []) if l][:total]
    if set(letras) <= set(VARIAVEIS):
        candidatas = VARIAVEIS + list(string.ascii_lowercase)
    else:
        inicio = string.ascii_lowercase.index(max(letras)) + 1
        candidatas = list(string.ascii_lowercase[inicio:] + string.ascii_lowercase)
    for letra in candidatas:
        if len(letras) >= total:
            break
        if letra not in letras:
            letras.append(letra)
    return letras


def ler_incognitas(texto):
    """'a,b,c' -> ['a', 'b', 'c']; vazio ou inválido -> x, y, z (o campo é oculto: não há erro a mostrar)."""
    texto = (texto or '').replace(' ', '').lower()
    if not _RE_INCOGNITAS.match(texto):
        return list(VARIAVEIS)
    letras = texto.split(',')
    return completar_incognitas(letras) if len(set(letras)) == len(letras) else list(VARIAVEIS)


class SistemaForm(forms.Form):
    """Sistema informado pela matriz (grade 3×3 + K) ou pelas equações (RF-001, RN-001, RN-022)."""

    entrada = forms.ChoiceField(label='Informar por', choices=ENTRADAS, initial='matriz', required=False)
    # Opcional: no modo Equações a ordem vem do número de equações; no modo Matriz, ausente vale 2.
    n = forms.ChoiceField(label='Ordem', choices=ORDENS, initial='2', required=False)
    metodo = forms.ChoiceField(label='Método', choices=[(m, NOMES_METODO[m]) for m in METODOS],
                               initial='ambos')
    equacoes = forms.CharField(
        label='Equações', required=False, max_length=LIMITE_TEXTO,
        widget=forms.Textarea(attrs={'class': 'form-control equacoes', 'rows': 3, 'spellcheck': 'false',
                                     'autocomplete': 'off',
                                     'placeholder': '2x + 3y = 4\n-x + 2y = 5'}),
    )
    # Letras das incógnitas (RN-022), ex.: 'a,b,c'. Vêm das equações e seguem no modo Matriz e no link.
    incognitas = forms.CharField(required=False, widget=forms.HiddenInput)   # validado em ler_incognitas

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.letras = ler_incognitas(self.data.get('incognitas') if self.is_bound else '')
        for i in range(1, 4):
            for j in range(1, 4):
                self.fields[f'a{i}{j}'] = self._campo(
                    f'Coeficiente de {self.letras[j - 1]} na equação {i}')
            self.fields[f'k{i}'] = self._campo(f'Termo independente da equação {i}')
        for nome in ('n', 'metodo'):
            self.fields[nome].widget.attrs['class'] = 'form-select'
        # O método fica na barra superior, fora do <form>: o atributo HTML `form` o vincula ao formulário.
        self.fields['metodo'].widget.attrs.update({'class': 'form-select form-select-sm', 'form': 'form-sistema'})

    @staticmethod
    def _campo(rotulo):
        return forms.CharField(
            label=rotulo, required=False, max_length=20,
            widget=forms.TextInput(attrs={'class': 'form-control coef', 'autocomplete': 'off',
                                          'inputmode': 'text', 'aria-label': rotulo}),
        )

    def clean(self):
        dados = super().clean()
        if dados.get('entrada') == 'equacoes':
            try:
                A, K, incognitas = ler_sistema_com_incognitas(dados.get('equacoes'))
            except ErroEntrada as erro:
                self.add_error('equacoes', str(erro))
                return dados
        else:
            dados['entrada'] = 'matriz'
            n = int(dados.get('n') or 2)
            A = [[self._ler(f'a{i}{j}') for j in range(1, n + 1)] for i in range(1, n + 1)]
            K = [self._ler(f'k{i}') for i in range(1, n + 1)]
            incognitas = self.letras[:n]
        dados['A'], dados['K'], dados['ordem'] = A, K, len(A)
        dados['incognitas'] = incognitas
        return dados

    def _ler(self, nome):
        try:
            return ler_numero(self.cleaned_data.get(nome, ''))
        except ErroEntrada as erro:
            self.add_error(nome, str(erro))
            return None

    def grade(self):
        """Linhas de BoundFields para o template: [(i, [a_i1, a_i2, a_i3], k_i)]."""
        return [(i, [self[f'a{i}{j}'] for j in range(1, 4)], self[f'k{i}']) for i in range(1, 4)]


def dados_de_exibicao(dados, A, K, equacoes, incognitas):
    """Dados para redesenhar o formulário com a grade e as equações preenchidas pelo sistema lido."""
    novos = dados.copy()
    novos['n'] = str(len(A))
    novos['incognitas'] = ','.join(completar_incognitas(incognitas))
    for i, linha in enumerate(A, start=1):
        for j, valor in enumerate(linha, start=1):
            novos[f'a{i}{j}'] = str(valor)
        novos[f'k{i}'] = str(K[i - 1])
    if novos.get('entrada') != 'equacoes' or not novos.get('equacoes'):
        novos['equacoes'] = '\n'.join(equacoes)
    return novos
