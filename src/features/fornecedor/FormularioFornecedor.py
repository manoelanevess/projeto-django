"""Formulário de cadastro e edição de fornecedores."""
from django import forms

from .models import Fornecedor


class FormularioFornecedor(forms.ModelForm):
    class Meta:
        model = Fornecedor
        fields = ["Nome", "Telefone", "Email", "Cidade"]
        widgets = {
            "Nome": forms.TextInput(
                attrs={"class": "CampoFormulario", "autofocus": True}
            ),
            "Telefone": forms.TextInput(
                attrs={"class": "CampoFormulario", "placeholder": "(00) 00000-0000"}
            ),
            "Email": forms.EmailInput(attrs={"class": "CampoFormulario"}),
            "Cidade": forms.TextInput(attrs={"class": "CampoFormulario"}),
        }

    def LimparTexto(self, NomeCampo):
        return " ".join(str(self.cleaned_data.get(NomeCampo, "")).split())

    def clean_Nome(self):
        Nome = self.LimparTexto("Nome")
        FornecedoresIguais = Fornecedor.objects.filter(Nome__iexact=Nome)

        if self.instance.pk:
            FornecedoresIguais = FornecedoresIguais.exclude(pk=self.instance.pk)

        if FornecedoresIguais.exists():
            raise forms.ValidationError("Já existe um fornecedor com este nome.")

        return Nome

    def clean_Telefone(self):
        return self.LimparTexto("Telefone")

    def clean_Email(self):
        return self.cleaned_data.get("Email", "").strip().lower()

    def clean_Cidade(self):
        return self.LimparTexto("Cidade")
