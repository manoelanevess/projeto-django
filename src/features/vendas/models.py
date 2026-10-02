"""Modelos persistidos das vendas concluídas."""
from decimal import Decimal

from django.conf import settings
from django.db import models

from features.produtos.models import Produto


class Venda(models.Model):
    DINHEIRO = "dinheiro"
    PIX = "pix"

    OpcoesFormaPagamento = [
        (DINHEIRO, "Dinheiro"),
        (PIX, "PIX"),
    ]

    Proprietario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="VendasRealizadas",
    )
    NomeCliente = models.CharField(max_length=80, blank=True)
    FormaPagamento = models.CharField(max_length=10, choices=OpcoesFormaPagamento)
    Total = models.DecimalField(max_digits=12, decimal_places=2)
    ValorRecebido = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )
    Troco = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    CriadaEm = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-CriadaEm"]
        verbose_name = "venda"
        verbose_name_plural = "vendas"

    def __str__(self):
        return f"Venda #{self.pk} - R$ {self.Total}"


class ItemVenda(models.Model):
    Venda = models.ForeignKey(
        Venda,
        on_delete=models.CASCADE,
        related_name="Itens",
    )
    Produto = models.ForeignKey(
        Produto,
        on_delete=models.PROTECT,
        related_name="ItensVendidos",
    )
    NomeProduto = models.CharField(max_length=120)
    UnidadeVenda = models.CharField(max_length=12)
    Quantidade = models.DecimalField(max_digits=12, decimal_places=3)
    PrecoUnitario = models.DecimalField(max_digits=10, decimal_places=2)
    Subtotal = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        ordering = ["id"]
        verbose_name = "item da venda"
        verbose_name_plural = "itens da venda"

    def __str__(self):
        return f"{self.NomeProduto} - {self.Quantidade}"
