"""Modelos persistidos da feature de produtos."""
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models


class Produto(models.Model):
    UNIDADE = "unidade"
    QUILOGRAMA = "quilograma"

    OpcoesUnidadeVenda = [
        (UNIDADE, "Unidade"),
        (QUILOGRAMA, "Quilograma"),
    ]

    Nome = models.CharField(max_length=120, unique=True)
    Categoria = models.CharField(max_length=80, blank=True)
    UnidadeVenda = models.CharField(
        max_length=12,
        choices=OpcoesUnidadeVenda,
        default=UNIDADE,
    )
    QuantidadeEstoque = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        default=Decimal("0.000"),
        validators=[MinValueValidator(Decimal("0.000"))],
    )
    EstoqueMinimo = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        default=Decimal("0.000"),
        validators=[MinValueValidator(Decimal("0.000"))],
    )
    PrecoVenda = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    Ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ["Nome"]
        verbose_name = "produto"
        verbose_name_plural = "produtos"

    def __str__(self):
        return self.Nome

    def clean(self):
        super().clean()

        if (
            self.UnidadeVenda == self.UNIDADE
            and self.QuantidadeEstoque % 1 != 0
        ):
            raise ValidationError(
                {"QuantidadeEstoque": "Produtos por unidade exigem quantidade inteira."}
            )

        if self.UnidadeVenda == self.UNIDADE and self.EstoqueMinimo % 1 != 0:
            raise ValidationError(
                {"EstoqueMinimo": "Produtos por unidade exigem estoque mínimo inteiro."}
            )

    def ObterUnidadeResumida(self):
        if self.UnidadeVenda == self.QUILOGRAMA:
            return "kg"

        return "un"
