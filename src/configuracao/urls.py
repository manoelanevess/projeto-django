"""Rotas principais da aplicação."""
from django.contrib import admin
from django.contrib.auth.decorators import login_required as ExigirLogin
from django.urls import path

from componentes.ComponenteErro import ComponentePaginaNaoEncontrada
from features.estoque.ComponenteEstoque import ComponenteEstoque
from features.fornecedor.ComponenteFornecedor import ComponenteFornecedores
from features.pagina_principal.ComponentePaginaPrincipal import ComponentePaginaPrincipal
from features.produtos.ComponenteProduto import ComponenteListaProdutos
from features.usuarios.ComponenteUsuario import ComponenteLogin, ComponenteLogout
from features.vendas.ComponenteCarrinho import (
    ComponenteAdicionarItem,
    ComponenteCancelarCarrinho,
    ComponenteCarrinho,
    ComponenteConcluirCompra,
    ComponenteRemoverItem,
    ComponenteRenomearCarrinho,
)


ProtegerComponente = ExigirLogin(login_url="Login")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", ProtegerComponente(ComponentePaginaPrincipal), name="PaginaPrincipal"),
    path("login", ComponenteLogin, name="Login"),
    path("logout", ComponenteLogout, name="Logout"),
    path("carrinho", ProtegerComponente(ComponenteCarrinho), name="Carrinho"),
    path(
        "carrinho/adicionar",
        ProtegerComponente(ComponenteAdicionarItem),
        name="AdicionarItemCarrinho",
    ),
    path(
        "carrinho/remover",
        ProtegerComponente(ComponenteRemoverItem),
        name="RemoverItemCarrinho",
    ),
    path(
        "carrinho/cancelar",
        ProtegerComponente(ComponenteCancelarCarrinho),
        name="CancelarCarrinho",
    ),
    path(
        "carrinho/concluir",
        ProtegerComponente(ComponenteConcluirCompra),
        name="ConcluirCompra",
    ),
    path(
        "carrinho/nome",
        ProtegerComponente(ComponenteRenomearCarrinho),
        name="RenomearCarrinho",
    ),
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
