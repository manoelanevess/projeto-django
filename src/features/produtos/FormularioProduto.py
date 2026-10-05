"""Formulário de cadastro e edição de produtos."""
from decimal import Decimal

from django import forms
from django.db import transaction
from django.db.models import Q

from features.fornecedor.models import Fornecedor

from .models import LoteEstoque, Produto


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


class FormularioEdicaoProduto(forms.ModelForm):
    class Meta:
        model = Produto
        fields = [
            "Nome",
            "Categoria",
            "Marca",
            "UnidadeVenda",
            "EstoqueMinimo",
        ]
        widgets = {
            "Nome": forms.TextInput(
                attrs={"class": "CampoFormulario", "autofocus": True}
            ),
            "Categoria": forms.TextInput(attrs={"class": "CampoFormulario"}),
            "Marca": forms.TextInput(attrs={"class": "CampoFormulario"}),
            "UnidadeVenda": forms.Select(attrs={"class": "CampoFormulario"}),
            "EstoqueMinimo": forms.NumberInput(
                attrs={"class": "CampoFormulario", "min": "0", "step": "0.001"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["Categoria"].required = True
        self.fields["EstoqueMinimo"].required = False
        self.fields["UnidadeVenda"].disabled = True

    def LimparTexto(self, NomeCampo):
        return " ".join(str(self.cleaned_data.get(NomeCampo, "")).split())

    def clean_Nome(self):
        Nome = self.LimparTexto("Nome")
        ProdutosIguais = Produto.objects.filter(Nome__iexact=Nome).exclude(
            pk=self.instance.pk
        )

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
        UnidadeVenda = self.instance.UnidadeVenda
        EstoqueMinimo = DadosLimpos.get("EstoqueMinimo")

        if UnidadeVenda == Produto.QUILOGRAMA:
            DadosLimpos["EstoqueMinimo"] = None
            return DadosLimpos

        if EstoqueMinimo is None:
            self.add_error("EstoqueMinimo", "Informe o estoque mínimo.")
        elif UnidadeVenda in {Produto.UNIDADE, Produto.VALOR_FIXO}:
            if EstoqueMinimo % Decimal("1"):
                self.add_error(
                    "EstoqueMinimo",
                    "Este tipo de venda exige estoque mínimo inteiro.",
                )

        return DadosLimpos


class FormularioLoteEstoque(forms.Form):
    Fornecedor = forms.ModelChoiceField(
        queryset=Fornecedor.objects.none(),
        empty_label="Selecione um fornecedor",
        widget=forms.Select(attrs={"class": "CampoFormulario"}),
    )
    PrecoCusto = forms.DecimalField(
        min_value=Decimal("0.00"),
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(
            attrs={"class": "CampoFormulario", "min": "0", "step": "0.01"}
        ),
    )
    PrecoVenda = forms.DecimalField(
        min_value=Decimal("0.01"),
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(
            attrs={"class": "CampoFormulario", "min": "0.01", "step": "0.01"}
        ),
    )
    QuantidadeEntrada = forms.DecimalField(
        required=False,
        min_value=Decimal("0.001"),
        max_digits=12,
        decimal_places=3,
        widget=forms.NumberInput(
            attrs={"class": "CampoFormulario", "min": "0.001", "step": "0.001"}
        ),
    )
    Disponivel = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={"class": "CampoCheckbox"}),
    )

    def __init__(self, *args, ProdutoVenda, **kwargs):
        super().__init__(*args, **kwargs)
        self.ProdutoVenda = ProdutoVenda
        self.fields["Fornecedor"].queryset = Fornecedor.objects.filter(
            Ativo=True
        ).order_by("Nome")

        if ProdutoVenda.ExigeQuantidadeInteira():
            self.fields["QuantidadeEntrada"].widget.attrs["step"] = "1"
            self.fields["QuantidadeEntrada"].widget.attrs["min"] = "1"

    def clean(self):
        DadosLimpos = super().clean()
        Quantidade = DadosLimpos.get("QuantidadeEntrada")

        if self.ProdutoVenda.EhControladoPorDisponibilidade():
            DadosLimpos["QuantidadeEntrada"] = None
            return DadosLimpos

        if Quantidade is None:
            self.add_error(
                "QuantidadeEntrada",
                "Informe a quantidade recebida.",
            )
        elif self.ProdutoVenda.ExigeQuantidadeInteira() and Quantidade % Decimal("1"):
            self.add_error(
                "QuantidadeEntrada",
                "Este tipo de venda exige quantidade inteira.",
            )

        return DadosLimpos

    @transaction.atomic
    def CriarLote(self):
        Quantidade = self.cleaned_data["QuantidadeEntrada"]
        LoteCriado = LoteEstoque.objects.create(
            Produto=self.ProdutoVenda,
            Fornecedor=self.cleaned_data["Fornecedor"],
            QuantidadeInicial=Quantidade,
            QuantidadeDisponivel=Quantidade,
            PrecoCusto=self.cleaned_data["PrecoCusto"],
            PrecoVenda=self.cleaned_data["PrecoVenda"],
            Disponivel=(
                self.cleaned_data["Disponivel"]
                if self.ProdutoVenda.EhControladoPorDisponibilidade()
                else True
            ),
        )
        self.ProdutoVenda.SincronizarResumoLotes()
        return LoteCriado
