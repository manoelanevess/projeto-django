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
from features.produtos.ComponenteCatalogoProduto import ComponenteComplementarCodigo, ComponenteConsultarCatalogoProduto, ComponentePesquisarCodigoWeb
from features.produtos.ComponenteCategoria import ComponenteFormularioCategoriaProduto
from features.produtos.ComponenteProduto import (
    ComponenteAtualizarDataLote,
    ComponenteAtualizarValidadeLote,
    ComponenteEncerrarLote,
    ComponenteExcluirLote,
    ComponenteExcluirProduto,
    ComponenteFormularioProduto,
    ComponenteLerCodigoEstoque,
    ComponenteRedirecionarProdutos,
)
from features.usuarios.ComponenteUsuario import ComponenteLogin, ComponenteLogout
from features.usuarios.ComponenteConfiguracao import ComponenteConfiguracoes, ComponenteFotoPerfil
from features.vendas.ComponenteCarrinho import (
    ComponenteAbrirCarrinho,
    ComponenteAdicionarItem,
    ComponenteCancelarCarrinho,
    ComponenteCarrinho,
    ComponenteConcluirCompra,
    ComponenteFecharCarrinho,
    ComponentePesquisarProdutos,
    ComponenteRemoverItem,
    ComponenteRenomearCarrinho,
)
from features.vendas.ComponenteContaCliente import (
    ComponenteContinhasClientes,
    ComponenteExcluirContaCliente,
    ComponenteRegistrarPagamentoContaCliente,
)
from features.vendas.ComponenteHistoricoVenda import ComponenteHistoricoVendas
from features.vendas.ComponenteLeitorCodigoBarras import ComponenteLerCodigoCarrinho


ProtegerComponente = ExigirLogin(login_url="Login")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", ProtegerComponente(ComponentePaginaPrincipal), name="PaginaPrincipal"),
    path("login", ComponenteLogin, name="Login"),
    path("logout", ComponenteLogout, name="Logout"),
    path("configuracoes", ProtegerComponente(ComponenteConfiguracoes), name="Configuracoes"),
    path("configuracoes/foto-perfil", ProtegerComponente(ComponenteFotoPerfil), name="FotoPerfil"),
    path("carrinho", ProtegerComponente(ComponenteCarrinho), name="Carrinho"),
    path("carrinho/abrir", ProtegerComponente(ComponenteAbrirCarrinho), name="AbrirCarrinho"),
    path("carrinho/fechar", ProtegerComponente(ComponenteFecharCarrinho), name="FecharCarrinho"),
    path("carrinho/ler-codigo", ProtegerComponente(ComponenteLerCodigoCarrinho), name="LerCodigoCarrinho"),
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
        "vendas/historico",
        ProtegerComponente(ComponenteHistoricoVendas),
        name="HistoricoVendas",
    ),
    path(
        "continhas",
        ProtegerComponente(ComponenteContinhasClientes),
        name="ContinhasClientes",
    ),
    path(
        "continhas/pagamento",
        ProtegerComponente(ComponenteRegistrarPagamentoContaCliente),
        name="RegistrarPagamentoContaCliente",
    ),
    path(
        "continhas/<int:ContaId>/excluir",
        ProtegerComponente(ComponenteExcluirContaCliente),
        name="ExcluirContaCliente",
    ),
    path(
        "produtos",
        ProtegerComponente(ComponenteRedirecionarProdutos),
        name="ListaProdutos",
    ),
    path("estoque", ProtegerComponente(ComponenteEstoque), name="Estoque"),
    path("estoque/categorias/nova", ProtegerComponente(ComponenteFormularioCategoriaProduto), name="AdicionarCategoriaProduto"),
    path("estoque/ler-codigo", ProtegerComponente(ComponenteLerCodigoEstoque), name="LerCodigoEstoque"),
    path("estoque/pesquisar-codigo-web", ProtegerComponente(ComponentePesquisarCodigoWeb), name="PesquisarCodigoWeb"),
    path("estoque/complementar-codigo", ProtegerComponente(ComponenteComplementarCodigo), name="ComplementarCodigo"),
    path(
        "estoque/consultar-codigo",
        ProtegerComponente(ComponenteConsultarCatalogoProduto),
        name="ConsultarCatalogoProduto",
    ),
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
        "estoque/<int:ProdutoId>/lotes/<int:LoteId>/data",
        ProtegerComponente(ComponenteAtualizarDataLote),
        name="AtualizarDataLoteEstoque",
    ),
    path(
        "estoque/<int:ProdutoId>/lotes/<int:LoteId>/validade",
        ProtegerComponente(ComponenteAtualizarValidadeLote),
        name="AtualizarValidadeLoteEstoque",
    ),
    path(
        "estoque/<int:ProdutoId>/lotes/<int:LoteId>/excluir",
        ProtegerComponente(ComponenteExcluirLote),
        name="ExcluirLoteEstoque",
    ),
    path(
        "estoque/<int:ProdutoId>/lotes/<int:LoteId>/encerrar",
        ProtegerComponente(ComponenteEncerrarLote),
        name="EncerrarLoteEstoque",
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
