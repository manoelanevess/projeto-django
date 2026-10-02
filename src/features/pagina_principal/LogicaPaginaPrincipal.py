"""Composição dos dados da Página Principal."""
from features.produtos.LogicaProduto import GerarResumoProdutos
from features.vendas.LogicaCarrinho import MontarResumosCarrinhos

from .ApiPaginaPrincipal import BuscarAtalhosOperacionais


def GerarDadosPaginaPrincipal(Request, BuscaEstoque=""):
    return {
        "ResumoProdutos": GerarResumoProdutos(),
        "ConsultaEstoque": GerarResumoProdutos(Busca=BuscaEstoque),
        "ResumosCarrinhos": MontarResumosCarrinhos(Request),
        "Atalhos": BuscarAtalhosOperacionais(),
    }
