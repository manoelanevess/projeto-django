"""Configuração administrativa dos produtos."""
from django.contrib import admin

from .models import Produto


@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = (
        "Nome",
        "Categoria",
        "Marca",
        "Fornecedor",
        "UnidadeVenda",
        "QuantidadeEstoque",
        "Disponivel",
        "PrecoCusto",
        "PrecoVenda",
        "Ativo",
    )
    list_filter = ("UnidadeVenda", "Disponivel", "Ativo", "Categoria")
    search_fields = ("Nome", "Categoria", "Marca", "Fornecedor__Nome")
