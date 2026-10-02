"""Configuração administrativa das vendas."""
from django.contrib import admin

from .models import ItemVenda, Venda


class ItemVendaInline(admin.TabularInline):
    model = ItemVenda
    extra = 0
    can_delete = False
    readonly_fields = (
        "Produto",
        "NomeProduto",
        "UnidadeVenda",
        "Quantidade",
        "PrecoUnitario",
        "Subtotal",
    )


@admin.register(Venda)
class VendaAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "CriadaEm",
        "NomeCliente",
        "FormaPagamento",
        "Total",
        "Troco",
        "Proprietario",
    )
    list_filter = ("FormaPagamento", "CriadaEm")
    search_fields = ("NomeCliente",)
    readonly_fields = (
        "Proprietario",
        "NomeCliente",
        "FormaPagamento",
        "Total",
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
        "Quantidade",
        "PrecoUnitario",
        "Subtotal",
    )
    search_fields = ("NomeProduto", "Venda__NomeCliente")

    def has_add_permission(self, Request):
        return False
