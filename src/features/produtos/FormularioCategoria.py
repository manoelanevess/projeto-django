"""Cadastro de categorias e seleção das opções já disponíveis."""
from django import forms

from componentes.NomesCadastro import NormalizarNomeCadastro

from .ApiProduto import BuscarCategoriasProdutos
from .models import CategoriaProduto


class CampoCategoriaProduto(forms.ChoiceField):
    def to_python(self, value):
        return NormalizarNomeCadastro(super().to_python(value))

    def prepare_value(self, value):
        return NormalizarNomeCadastro(value)


def CriarCampoCategoriaProduto():
    return CampoCategoriaProduto(
        label="Categoria",
        choices=[("", "Selecione uma categoria"), *[(Nome, Nome) for Nome in BuscarCategoriasProdutos()]],
        widget=forms.Select(attrs={"class": "CampoFormulario"}),
        error_messages={
            "required": "Selecione a categoria do produto.",
            "invalid_choice": "Selecione uma categoria cadastrada. Use o + no filtro do estoque para adicionar outra.",
        },
    )


class FormularioCategoriaProduto(forms.ModelForm):
    class Meta:
        model = CategoriaProduto
        fields = ["Nome"]
        labels = {"Nome": "Nome da categoria"}
        widgets = {"Nome": forms.TextInput(attrs={
            "class": "CampoFormulario", "placeholder": "Ex.: Bebidas Sem Álcool",
        })}

    def clean_Nome(self):
        Nome = NormalizarNomeCadastro(self.cleaned_data["Nome"])
        if not Nome:
            raise forms.ValidationError("Informe o nome da categoria.")
        if len(Nome) > 80:
            raise forms.ValidationError("Use no máximo 80 caracteres.")
        if Nome in BuscarCategoriasProdutos():
            raise forms.ValidationError("Esta categoria já está cadastrada.")
        return Nome
