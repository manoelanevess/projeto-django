"""Configuração administrativa dos produtos."""
from django.contrib import admin

from .models import LoteEstoque, Produto


@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = (
        "Nome",
        "CodigoBarras",
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
    search_fields = ("Nome", "CodigoBarras", "Categoria", "Marca", "Fornecedor__Nome")


@admin.register(LoteEstoque)
class LoteEstoqueAdmin(admin.ModelAdmin):
    list_display = (
        "Produto",
        "Fornecedor",
        "QuantidadeDisponivel",
        "PrecoCusto",
        "PrecoVenda",
        "Disponivel",
        "Ativo",
        "CriadoEm",
        "DataValidade",
    )
    list_filter = ("Disponivel", "Ativo", "Fornecedor", "DataValidade")
    search_fields = ("Produto__Nome", "Produto__Marca", "Fornecedor__Nome")
