"""Regras de consulta e apresentação da feature de produtos."""
from decimal import Decimal

from .ApiProduto import BuscarProdutos


def FormatarQuantidade(Quantidade):
    QuantidadeDecimal = Decimal(Quantidade)

    if QuantidadeDecimal % 1 == 0:
        return str(int(QuantidadeDecimal))

    return format(QuantidadeDecimal, ".3f").rstrip("0").rstrip(".").replace(".", ",")


def FormatarValorMoeda(Valor):
    return (
        f"{Decimal(Valor):,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


def GerarResumoProdutos(Busca="", Estoque=""):
    ProdutosFiltrados = list(BuscarProdutos(Busca, Estoque))
    TotalItens = sum(
        (Produto.QuantidadeEstoque for Produto in ProdutosFiltrados),
        Decimal("0.000"),
    )
    ProdutosEstoqueBaixo = [
        Produto
        for Produto in ProdutosFiltrados
        if Produto.QuantidadeEstoque <= Produto.EstoqueMinimo
    ]
    ProdutosDisponiveis = [
        Produto
        for Produto in ProdutosFiltrados
        if Produto.QuantidadeEstoque > 0
    ]
    CustoTotal = sum(
        (
            Produto.QuantidadeEstoque * Produto.PrecoVenda
            for Produto in ProdutosFiltrados
        ),
        Decimal("0.00"),
    )
    ProdutosFormatados = [
        {
            "Id": Produto.id,
            "Nome": Produto.Nome,
            "Categoria": Produto.Categoria or "Sem categoria",
            "Quantidade": Produto.QuantidadeEstoque,
            "QuantidadeFormatada": FormatarQuantidade(Produto.QuantidadeEstoque),
            "EstoqueMinimo": Produto.EstoqueMinimo,
            "EstoqueMinimoFormatado": FormatarQuantidade(Produto.EstoqueMinimo),
            "PrecoVenda": Produto.PrecoVenda,
            "PrecoVendaFormatado": FormatarValorMoeda(Produto.PrecoVenda),
            "Unidade": Produto.ObterUnidadeResumida(),
        }
        for Produto in ProdutosFiltrados
    ]

    return {
        "Produtos": ProdutosFormatados,
        "TotalProdutos": len(ProdutosFiltrados),
        "TotalProdutosDisponiveis": len(ProdutosDisponiveis),
        "TotalItens": TotalItens,
        "TotalItensFormatado": FormatarQuantidade(TotalItens),
        "TotalEstoqueBaixo": len(ProdutosEstoqueBaixo),
        "CustoTotal": CustoTotal,
    }
