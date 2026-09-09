"""Rotas principais da aplicação."""
from django.contrib import admin
from django.urls import path

from componentes.ComponenteErro import ComponentePaginaNaoEncontrada
from features.dashboard.ComponenteDashboard import ComponenteDashboard
from features.estoque.ComponenteEstoque import ComponenteEstoque
from features.fornecedor.ComponenteFornecedor import ComponenteFornecedores
from features.produtos.ComponenteProduto import ComponenteListaProdutos
from features.usuarios.ComponenteUsuario import ComponenteLogin


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", ComponenteDashboard, name="Dashboard"),
    path("login", ComponenteLogin, name="Login"),
    path("produtos", ComponenteListaProdutos, name="ListaProdutos"),
    path("estoque", ComponenteEstoque, name="Estoque"),
    path("fornecedores", ComponenteFornecedores, name="Fornecedores"),
    path("<path:CaminhoNaoEncontrado>", ComponentePaginaNaoEncontrada, name="PaginaNaoEncontrada"),
]

handler404 = ComponentePaginaNaoEncontrada
