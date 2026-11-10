from django import forms
from django.forms import BaseModelFormSet, modelformset_factory

from .models import VarianteLanding


class VarianteForm(forms.ModelForm):
    ordem = forms.IntegerField(min_value=1, max_value=99, label='Ordem',
                               widget=forms.NumberInput(attrs={'class': 'form-control form-control-sm ordem-input'}))
    ativa = forms.BooleanField(required=False, label='Ativa',
                               widget=forms.CheckboxInput(attrs={'class': 'form-check-input', 'role': 'switch'}))

    class Meta:
        model = VarianteLanding
        fields = ['ordem', 'ativa']


class BaseVariantesFormSet(BaseModelFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return
        if not any(f.cleaned_data.get('ativa') for f in self.forms):
            raise forms.ValidationError('Deixe pelo menos uma variação ativa: a página inicial precisa de um layout.')


VariantesFormSet = modelformset_factory(VarianteLanding, form=VarianteForm, formset=BaseVariantesFormSet, extra=0,
                                        can_delete=False)
