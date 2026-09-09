"""Camada de lógica inicial da feature de produtos."""
from .ApiProduto import BuscarProdutosIniciais


def FiltrarProdutos(Produtos, Busca="", Estoque=""):
    ProdutosFiltrados = Produtos

    if Busca:
        TermoBusca = Busca.lower()
        ProdutosFiltrados = [
            Produto
            for Produto in ProdutosFiltrados
            if TermoBusca in Produto["Nome"].lower()
            or TermoBusca in Produto["Categoria"].lower()
        ]

    if Estoque == "baixo":
        ProdutosFiltrados = [
            Produto
            for Produto in ProdutosFiltrados
            if Produto["Quantidade"] <= Produto["EstoqueMinimo"]
        ]

    return ProdutosFiltrados


def GerarResumoProdutos(Busca="", Estoque=""):
    Produtos = BuscarProdutosIniciais()
    ProdutosFiltrados = FiltrarProdutos(Produtos, Busca, Estoque)
    TotalItens = sum(Produto["Quantidade"] for Produto in ProdutosFiltrados)
    ProdutosEstoqueBaixo = [
        Produto
        for Produto in ProdutosFiltrados
        if Produto["Quantidade"] <= Produto["EstoqueMinimo"]
    ]
    CustoTotal = sum(
        Produto["Quantidade"] * Produto["ValorUnitario"]
        for Produto in ProdutosFiltrados
    )

    return {
        "Produtos": ProdutosFiltrados,
        "TotalProdutos": len(ProdutosFiltrados),
        "TotalItens": TotalItens,
        "TotalEstoqueBaixo": len(ProdutosEstoqueBaixo),
        "CustoTotal": CustoTotal,
    }
