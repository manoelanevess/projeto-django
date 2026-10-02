"""Configuração administrativa dos produtos."""
from django.contrib import admin

from .models import Produto


@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = (
        "Nome",
        "Categoria",
        "UnidadeVenda",
        "QuantidadeEstoque",
        "PrecoVenda",
        "Ativo",
    )
    list_filter = ("UnidadeVenda", "Ativo", "Categoria")
    search_fields = ("Nome", "Categoria")
