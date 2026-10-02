"""Configuração administrativa dos fornecedores."""
from django.contrib import admin

from .models import Fornecedor


@admin.register(Fornecedor)
class FornecedorAdmin(admin.ModelAdmin):
    list_display = ("Nome", "Telefone", "Email", "Cidade", "Ativo")
    list_filter = ("Ativo", "Cidade")
    search_fields = ("Nome", "Telefone", "Email", "Cidade")
