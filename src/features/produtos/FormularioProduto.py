"""Formulário de cadastro e edição de produtos."""
from decimal import Decimal

from django import forms
from django.db.models import Q

from features.fornecedor.models import Fornecedor

from .models import Produto


class FormularioProduto(forms.ModelForm):
    class Meta:
        model = Produto
        fields = [
            "Nome",
            "Categoria",
            "Marca",
            "Fornecedor",
            "UnidadeVenda",
            "PrecoCusto",
            "PrecoVenda",
            "QuantidadeEstoque",
            "EstoqueMinimo",
            "Disponivel",
        ]
        widgets = {
            "Nome": forms.TextInput(
                attrs={"class": "CampoFormulario", "autofocus": True}
            ),
            "Categoria": forms.TextInput(attrs={"class": "CampoFormulario"}),
            "Marca": forms.TextInput(attrs={"class": "CampoFormulario"}),
            "Fornecedor": forms.Select(attrs={"class": "CampoFormulario"}),
            "UnidadeVenda": forms.Select(attrs={"class": "CampoFormulario"}),
            "PrecoCusto": forms.NumberInput(
                attrs={"class": "CampoFormulario", "min": "0", "step": "0.01"}
            ),
            "PrecoVenda": forms.NumberInput(
                attrs={"class": "CampoFormulario", "min": "0.01", "step": "0.01"}
            ),
            "QuantidadeEstoque": forms.NumberInput(
                attrs={"class": "CampoFormulario", "min": "0", "step": "0.001"}
            ),
            "EstoqueMinimo": forms.NumberInput(
                attrs={"class": "CampoFormulario", "min": "0", "step": "0.001"}
            ),
            "Disponivel": forms.CheckboxInput(attrs={"class": "CampoCheckbox"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["Categoria"].required = True
        self.fields["Fornecedor"].required = True
        self.fields["Fornecedor"].empty_label = "Selecione um fornecedor"
        self.fields["PrecoCusto"].required = True
        self.fields["QuantidadeEstoque"].required = False
        self.fields["EstoqueMinimo"].required = False

        if not self.instance.pk:
            self.fields["PrecoCusto"].initial = None
            self.initial["PrecoCusto"] = None

        FiltroFornecedores = Q(Ativo=True)

        if self.instance.pk and self.instance.Fornecedor_id:
            FiltroFornecedores |= Q(pk=self.instance.Fornecedor_id)

        self.fields["Fornecedor"].queryset = Fornecedor.objects.filter(
            FiltroFornecedores
        ).order_by("Nome")

    def LimparTexto(self, NomeCampo):
        return " ".join(str(self.cleaned_data.get(NomeCampo, "")).split())

    def clean_Nome(self):
        Nome = self.LimparTexto("Nome")
        ProdutosIguais = Produto.objects.filter(Nome__iexact=Nome)

        if self.instance.pk:
            ProdutosIguais = ProdutosIguais.exclude(pk=self.instance.pk)

        if ProdutosIguais.exists():
            raise forms.ValidationError("Já existe um produto com este nome.")

        return Nome

    def clean_Categoria(self):
        Categoria = self.LimparTexto("Categoria")

        if not Categoria:
            raise forms.ValidationError("Informe a categoria do produto.")

        return Categoria

    def clean_Marca(self):
        return self.LimparTexto("Marca")

    def clean(self):
        DadosLimpos = super().clean()
        UnidadeVenda = DadosLimpos.get("UnidadeVenda")
        QuantidadeEstoque = DadosLimpos.get("QuantidadeEstoque")
        EstoqueMinimo = DadosLimpos.get("EstoqueMinimo")

        if UnidadeVenda == Produto.QUILOGRAMA:
            DadosLimpos["QuantidadeEstoque"] = None
            DadosLimpos["EstoqueMinimo"] = None
            return DadosLimpos

        if QuantidadeEstoque is None:
            self.add_error("QuantidadeEstoque", "Informe a quantidade disponível.")

        if EstoqueMinimo is None:
            self.add_error("EstoqueMinimo", "Informe o estoque mínimo.")

        if UnidadeVenda in {Produto.UNIDADE, Produto.VALOR_FIXO}:
            if QuantidadeEstoque is not None and QuantidadeEstoque % Decimal("1"):
                self.add_error(
                    "QuantidadeEstoque",
                    "Este tipo de venda exige quantidade inteira.",
                )

            if EstoqueMinimo is not None and EstoqueMinimo % Decimal("1"):
                self.add_error(
                    "EstoqueMinimo",
                    "Este tipo de venda exige estoque mínimo inteiro.",
                )

        return DadosLimpos
