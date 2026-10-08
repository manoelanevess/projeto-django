"""Configuração administrativa das vendas."""
from django.contrib import admin

from .models import (
    ContaCliente,
    ItemRegistroVendaAntiga,
    ItemVenda,
    LancamentoContaCliente,
    RegistroVendaAntiga,
    Venda,
)


class ItemVendaInline(admin.TabularInline):
    model = ItemVenda
    extra = 0
    can_delete = False
    readonly_fields = (
        "Produto",
        "Lote",
        "NomeProduto",
        "UnidadeVenda",
        "Quantidade",
        "CustoUnitario",
        "PrecoUnitario",
        "Subtotal",
        "Lucro",
    )


@admin.register(Venda)
class VendaAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "CriadaEm",
        "NomeCliente",
        "ContaCliente",
        "FormaPagamento",
        "Total",
        "Lucro",
        "Troco",
        "Proprietario",
    )
    list_filter = ("FormaPagamento", "CriadaEm")
    search_fields = ("NomeCliente",)
    readonly_fields = (
        "Proprietario",
        "NomeCliente",
        "ContaCliente",
        "FormaPagamento",
        "Total",
        "Lucro",
        "ValorRecebido",
        "Troco",
        "CriadaEm",
    )
    inlines = (ItemVendaInline,)

    def has_add_permission(self, Request):
        return False


@admin.register(ItemVenda)
class ItemVendaAdmin(admin.ModelAdmin):
    list_display = (
        "Venda",
        "NomeProduto",
        "Lote",
        "Quantidade",
        "CustoUnitario",
        "PrecoUnitario",
        "Subtotal",
        "Lucro",
    )
    search_fields = ("NomeProduto", "Venda__NomeCliente")

    def has_add_permission(self, Request):
        return False


@admin.register(ContaCliente)
class ContaClienteAdmin(admin.ModelAdmin):
    list_display = ("NomeCliente", "Proprietario", "Ativa", "CriadaEm")
    list_filter = ("Ativa", "CriadaEm")
    search_fields = ("NomeCliente", "Proprietario__username")


@admin.register(LancamentoContaCliente)
class LancamentoContaClienteAdmin(admin.ModelAdmin):
    list_display = ("Conta", "Tipo", "Valor", "Venda", "CriadoEm")
    list_filter = ("Tipo", "CriadoEm")
    search_fields = ("Conta__NomeCliente", "Descricao")


class ItemRegistroVendaAntigaInline(admin.TabularInline):
    model = ItemRegistroVendaAntiga
    extra = 0
    can_delete = False
    readonly_fields = (
        "NomeProduto",
        "UnidadeVenda",
        "Quantidade",
        "PrecoUnitario",
        "Subtotal",
    )


@admin.register(RegistroVendaAntiga)
class RegistroVendaAntigaAdmin(admin.ModelAdmin):
    list_display = (
        "VendaOriginalId",
        "CriadaEm",
        "NomeCliente",
        "FormaPagamento",
        "Total",
        "Proprietario",
    )
    list_filter = ("FormaPagamento", "CriadaEm", "ConsolidadaEm")
    search_fields = ("NomeCliente", "VendaOriginalId")
    readonly_fields = (
        "Proprietario",
        "VendaOriginalId",
        "NomeCliente",
        "FormaPagamento",
        "Total",
        "Lucro",
        "ValorRecebido",
        "Troco",
        "CriadaEm",
        "ConsolidadaEm",
    )
    inlines = (ItemRegistroVendaAntigaInline,)

    def has_add_permission(self, Request):
        return False


@admin.register(ItemRegistroVendaAntiga)
class ItemRegistroVendaAntigaAdmin(admin.ModelAdmin):
    list_display = (
        "Registro",
        "NomeProduto",
        "Quantidade",
        "PrecoUnitario",
        "Subtotal",
    )
    search_fields = ("NomeProduto", "Registro__NomeCliente")

    def has_add_permission(self, Request):
        return False
