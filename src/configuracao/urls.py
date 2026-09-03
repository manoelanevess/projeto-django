"""Rotas principais da aplicação."""
from django.contrib import admin
from django.urls import path

from features.produtos.ComponenteProduto import ComponenteListaProdutos


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", ComponenteListaProdutos, name="ListaProdutos"),
]
