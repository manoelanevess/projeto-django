"""Modelos persistidos da feature de produtos."""
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models


class Produto(models.Model):
    UNIDADE = "unidade"
    QUILOGRAMA = "quilograma"
    METRO = "metro"
    VALOR_FIXO = "valor_fixo"

    OpcoesUnidadeVenda = [
        (UNIDADE, "Unidade"),
        (QUILOGRAMA, "Quilograma"),
        (METRO, "Metro"),
        (VALOR_FIXO, "Preço fixo"),
    ]

    Nome = models.CharField(max_length=120, unique=True)
    Categoria = models.CharField(max_length=80, blank=True)
    Marca = models.CharField(max_length=80, blank=True)
    Fornecedor = models.ForeignKey(
        "fornecedor.Fornecedor",
        on_delete=models.PROTECT,
        related_name="Produtos",
    )
    UnidadeVenda = models.CharField(
        max_length=12,
        choices=OpcoesUnidadeVenda,
        default=UNIDADE,
    )
    QuantidadeEstoque = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        default=Decimal("0.000"),
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.000"))],
    )
    EstoqueMinimo = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        default=Decimal("0.000"),
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.000"))],
    )
    PrecoCusto = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    PrecoVenda = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    Disponivel = models.BooleanField(default=True)
    Ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ["Nome"]
        verbose_name = "produto"
        verbose_name_plural = "produtos"

    def __str__(self):
        return self.Nome

    def clean(self):
        super().clean()

        if self.EhControladoPorDisponibilidade():
            self.QuantidadeEstoque = None
            self.EstoqueMinimo = None
            return

        if self.QuantidadeEstoque is None:
            raise ValidationError(
                {"QuantidadeEstoque": "Informe a quantidade disponível."}
            )

        if self.EstoqueMinimo is None:
            raise ValidationError(
                {"EstoqueMinimo": "Informe o estoque mínimo."}
            )

        if (
            self.ExigeQuantidadeInteira()
            and self.QuantidadeEstoque % 1 != 0
        ):
            raise ValidationError(
                {"QuantidadeEstoque": "Este tipo de venda exige quantidade inteira."}
            )

        if self.ExigeQuantidadeInteira() and self.EstoqueMinimo % 1 != 0:
            raise ValidationError(
                {"EstoqueMinimo": "Este tipo de venda exige estoque mínimo inteiro."}
            )

    def EhControladoPorDisponibilidade(self):
        return self.UnidadeVenda == self.QUILOGRAMA

    def ControlaQuantidadeEstoque(self):
        return not self.EhControladoPorDisponibilidade()

    def ExigeQuantidadeInteira(self):
        return self.UnidadeVenda in {self.UNIDADE, self.VALOR_FIXO}

    def EstaDisponivelParaVenda(self):
        if self.EhControladoPorDisponibilidade():
            return self.Disponivel

        return self.QuantidadeEstoque is not None and self.QuantidadeEstoque > 0

    def EstaComEstoqueBaixo(self):
        return (
            self.ControlaQuantidadeEstoque()
            and self.QuantidadeEstoque is not None
            and self.EstoqueMinimo is not None
            and self.QuantidadeEstoque <= self.EstoqueMinimo
        )

    def ObterUnidadeResumida(self):
        if self.UnidadeVenda == self.QUILOGRAMA:
            return "kg"

        if self.UnidadeVenda == self.METRO:
            return "m"

        if self.UnidadeVenda == self.VALOR_FIXO:
            return "item"

        return "un"

    def ObterDescricaoEstoque(self):
        if self.EhControladoPorDisponibilidade():
            return "Disponível" if self.Disponivel else "Indisponível"

        return f"{self.QuantidadeEstoque} {self.ObterUnidadeResumida()}"

    def ObterPassoVenda(self):
        return "1" if self.ExigeQuantidadeInteira() else "0.001"

    def ObterQuantidadeInicialVenda(self):
        if self.UnidadeVenda == self.QUILOGRAMA:
            return "0.100"

        return "1"

    def ObterRotuloQuantidadeVenda(self):
        if self.UnidadeVenda == self.QUILOGRAMA:
            return "Peso (kg)"

        if self.UnidadeVenda == self.METRO:
            return "Comprimento (m)"

        return "Quantidade"
