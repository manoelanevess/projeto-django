"""Camada de lógica inicial da feature de produtos."""
from .ApiProduto import BuscarProdutosIniciais


def GerarResumoProdutos():
    Produtos = BuscarProdutosIniciais()
    TotalItens = sum(Produto["Quantidade"] for Produto in Produtos)

    return {
        "Produtos": Produtos,
        "TotalProdutos": len(Produtos),
        "TotalItens": TotalItens,
    }
