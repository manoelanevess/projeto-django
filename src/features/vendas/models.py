"""Modelos persistidos das vendas concluídas."""
from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from features.produtos.models import LoteEstoque, Produto


class Venda(models.Model):
    DINHEIRO = "dinheiro"
    PIX = "pix"
    CONTA_CLIENTE = "conta_cliente"

    OpcoesFormaPagamento = [
        (DINHEIRO, "Dinheiro"),
        (PIX, "PIX"),
        (CONTA_CLIENTE, "Conta do cliente"),
    ]

    Proprietario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="VendasRealizadas",
    )
    NomeCliente = models.CharField(max_length=80, blank=True)
    ContaCliente = models.ForeignKey(
        "ContaCliente",
        on_delete=models.PROTECT,
        related_name="Vendas",
        null=True,
        blank=True,
    )
    FormaPagamento = models.CharField(max_length=20, choices=OpcoesFormaPagamento)
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


class ContaCliente(models.Model):
    Proprietario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="ContinhasClientes",
    )
    NomeCliente = models.CharField(max_length=80)
    Ativa = models.BooleanField(default=True)
    CriadaEm = models.DateTimeField(auto_now_add=True)
    AtualizadaEm = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["NomeCliente"]
        constraints = [
            models.UniqueConstraint(
                fields=["Proprietario", "NomeCliente"],
                name="ContaClienteUnicaPorProprietario",
            )
        ]
        verbose_name = "continha de cliente"
        verbose_name_plural = "continhas de clientes"

    def __str__(self):
        return self.NomeCliente


class LancamentoContaCliente(models.Model):
    COMPRA = "compra"
    PAGAMENTO = "pagamento"

    OpcoesTipo = [
        (COMPRA, "Compra"),
        (PAGAMENTO, "Pagamento"),
    ]

    Conta = models.ForeignKey(
        ContaCliente,
        on_delete=models.CASCADE,
        related_name="Lancamentos",
    )
    Venda = models.ForeignKey(
        Venda,
        on_delete=models.SET_NULL,
        related_name="LancamentosConta",
        null=True,
        blank=True,
    )
    Tipo = models.CharField(max_length=12, choices=OpcoesTipo)
    Descricao = models.CharField(max_length=140, blank=True)
    Valor = models.DecimalField(max_digits=12, decimal_places=2)
    CriadoEm = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-CriadoEm", "-id"]
        verbose_name = "lançamento de continha"
        verbose_name_plural = "lançamentos de continhas"

    def __str__(self):
        return f"{self.Conta.NomeCliente} - {self.get_Tipo_display()} - R$ {self.Valor}"


class RegistroVendaAntiga(models.Model):
    Proprietario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="RegistrosVendasAntigas",
    )
    VendaOriginalId = models.PositiveIntegerField()
    NomeCliente = models.CharField(max_length=80, blank=True)
    FormaPagamento = models.CharField(max_length=20)
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
    CriadaEm = models.DateTimeField()
    ConsolidadaEm = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-CriadaEm"]
        constraints = [
            models.UniqueConstraint(
                fields=["Proprietario", "VendaOriginalId"],
                name="RegistroVendaAntigaUnico",
            )
        ]
        verbose_name = "registro de venda antiga"
        verbose_name_plural = "registros de vendas antigas"

    def __str__(self):
        return f"Venda antiga #{self.VendaOriginalId} - R$ {self.Total}"


class ItemRegistroVendaAntiga(models.Model):
    Registro = models.ForeignKey(
        RegistroVendaAntiga,
        on_delete=models.CASCADE,
        related_name="Itens",
    )
    NomeProduto = models.CharField(max_length=120)
    UnidadeVenda = models.CharField(max_length=12)
    Quantidade = models.DecimalField(max_digits=12, decimal_places=3)
    PrecoUnitario = models.DecimalField(max_digits=10, decimal_places=2)
    Subtotal = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        ordering = ["id"]
        verbose_name = "item de venda antiga"
        verbose_name_plural = "itens de vendas antigas"

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
