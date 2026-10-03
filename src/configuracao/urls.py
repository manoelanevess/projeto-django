"""Rotas principais da aplicação."""
from django.contrib import admin
from django.contrib.auth.decorators import login_required as ExigirLogin
from django.urls import path

from componentes.ComponenteErro import ComponentePaginaNaoEncontrada
from features.estoque.ComponenteDashboard import ComponenteDashboard
from features.estoque.ComponenteEstoque import ComponenteEstoque
from features.fornecedor.ComponenteFornecedor import (
    ComponenteExcluirFornecedor,
    ComponenteFornecedores,
    ComponenteFormularioFornecedor,
)
from features.pagina_principal.ComponentePaginaPrincipal import ComponentePaginaPrincipal
from features.produtos.ComponenteProduto import (
    ComponenteExcluirProduto,
    ComponenteFormularioProduto,
    ComponenteRedirecionarProdutos,
)
from features.usuarios.ComponenteUsuario import ComponenteLogin, ComponenteLogout
from features.vendas.ComponenteCarrinho import (
    ComponenteAdicionarItem,
    ComponenteCancelarCarrinho,
    ComponenteCarrinho,
    ComponenteConcluirCompra,
    ComponentePesquisarProdutos,
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
        "carrinho/pesquisar",
        ProtegerComponente(ComponentePesquisarProdutos),
        name="PesquisarProdutosCarrinho",
    ),
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
        ProtegerComponente(ComponenteRedirecionarProdutos),
        name="ListaProdutos",
    ),
    path("estoque", ProtegerComponente(ComponenteEstoque), name="Estoque"),
    path(
        "dashboard",
        ProtegerComponente(ComponenteDashboard),
        name="Dashboard",
    ),
    path(
        "estoque/novo",
        ProtegerComponente(ComponenteFormularioProduto),
        name="AdicionarProduto",
    ),
    path(
        "estoque/<int:ProdutoId>/editar",
        ProtegerComponente(ComponenteFormularioProduto),
        name="EditarProduto",
    ),
    path(
        "estoque/<int:ProdutoId>/excluir",
        ProtegerComponente(ComponenteExcluirProduto),
        name="ExcluirProduto",
    ),
    path(
        "fornecedores",
        ProtegerComponente(ComponenteFornecedores),
        name="Fornecedores",
    ),
    path(
        "fornecedores/novo",
        ProtegerComponente(ComponenteFormularioFornecedor),
        name="AdicionarFornecedor",
    ),
    path(
        "fornecedores/<int:FornecedorId>/editar",
        ProtegerComponente(ComponenteFormularioFornecedor),
        name="EditarFornecedor",
    ),
    path(
        "fornecedores/<int:FornecedorId>/excluir",
        ProtegerComponente(ComponenteExcluirFornecedor),
        name="ExcluirFornecedor",
    ),
    path(
        "<path:CaminhoNaoEncontrado>",
        ProtegerComponente(ComponentePaginaNaoEncontrada),
        name="PaginaNaoEncontrada",
    ),
]

handler404 = ComponentePaginaNaoEncontrada
