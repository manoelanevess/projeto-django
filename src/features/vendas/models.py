"""Modelos persistidos das vendas concluídas."""
from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from features.produtos.models import LoteEstoque, Produto


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
    Lucro = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )
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
    Lote = models.ForeignKey(
        LoteEstoque,
        on_delete=models.SET_NULL,
        related_name="ItensVendidos",
        null=True,
        blank=True,
    )
    NomeProduto = models.CharField(max_length=120)
    UnidadeVenda = models.CharField(max_length=12)
    Quantidade = models.DecimalField(max_digits=12, decimal_places=3)
    CustoUnitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    PrecoUnitario = models.DecimalField(max_digits=10, decimal_places=2)
    Subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    Lucro = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    class Meta:
        ordering = ["id"]
        verbose_name = "item da venda"
        verbose_name_plural = "itens da venda"

    def __str__(self):
        return f"{self.NomeProduto} - {self.Quantidade}"


class ResumoVendaMensal(models.Model):
    Proprietario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="ResumosVendasMensais",
    )
    Ano = models.PositiveSmallIntegerField()
    Mes = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)]
    )
    QuantidadeVendas = models.PositiveIntegerField(default=0)
    TotalVendido = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    Lucro = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    class Meta:
        ordering = ["-Ano", "-Mes"]
        constraints = [
            models.UniqueConstraint(
                fields=["Proprietario", "Ano", "Mes"],
                name="ResumoVendaMensalUnico",
            )
        ]
        verbose_name = "resumo mensal de vendas"
        verbose_name_plural = "resumos mensais de vendas"

    def __str__(self):
        return f"{self.Mes:02d}/{self.Ano} - R$ {self.TotalVendido}"
