"""Camada de lógica inicial da feature de dashboard."""
from features.produtos.LogicaProduto import GerarResumoProdutos

from .ApiDashboard import BuscarAtalhosDashboard


def GerarDadosDashboard():
    ResumoProdutos = GerarResumoProdutos()

    return {
        "ResumoProdutos": ResumoProdutos,
        "Atalhos": BuscarAtalhosDashboard(),
    }
