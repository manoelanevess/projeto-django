"""Rotas principais da aplicação."""
from django.contrib import admin
from django.contrib.auth.decorators import login_required as ExigirLogin
from django.urls import path

from componentes.ComponenteErro import ComponentePaginaNaoEncontrada
from features.dashboard.ComponenteDashboard import ComponenteDashboard
from features.estoque.ComponenteEstoque import ComponenteEstoque
from features.fornecedor.ComponenteFornecedor import ComponenteFornecedores
from features.produtos.ComponenteProduto import ComponenteListaProdutos
from features.usuarios.ComponenteUsuario import ComponenteLogin, ComponenteLogout


ProtegerComponente = ExigirLogin(login_url="Login")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", ProtegerComponente(ComponenteDashboard), name="Dashboard"),
    path("login", ComponenteLogin, name="Login"),
    path("logout", ComponenteLogout, name="Logout"),
    path(
        "produtos",
        ProtegerComponente(ComponenteListaProdutos),
        name="ListaProdutos",
    ),
    path("estoque", ProtegerComponente(ComponenteEstoque), name="Estoque"),
    path(
        "fornecedores",
        ProtegerComponente(ComponenteFornecedores),
        name="Fornecedores",
    ),
    path(
        "<path:CaminhoNaoEncontrado>",
        ProtegerComponente(ComponentePaginaNaoEncontrada),
        name="PaginaNaoEncontrada",
    ),
]

handler404 = ComponentePaginaNaoEncontrada
