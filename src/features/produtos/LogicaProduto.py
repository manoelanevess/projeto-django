"""Regras de consulta e apresentação da feature de produtos."""
from decimal import Decimal

from .ApiProduto import BuscarProdutos


def FormatarQuantidade(Quantidade):
    if Quantidade is None:
        return ""

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


def GerarResumoProdutos(Busca="", Estoque="", Categoria="", Fornecedor=""):
    ProdutosFiltrados = list(
        BuscarProdutos(Busca, Estoque, Categoria, Fornecedor)
    )
    TotalItens = sum(
        (
            Produto.QuantidadeEstoque
            for Produto in ProdutosFiltrados
            if Produto.ControlaQuantidadeEstoque()
            and Produto.QuantidadeEstoque is not None
        ),
        Decimal("0.000"),
    )
    ProdutosEstoqueBaixo = [
        Produto
        for Produto in ProdutosFiltrados
        if Produto.EstaComEstoqueBaixo()
    ]
    ProdutosDisponiveis = [
        Produto
        for Produto in ProdutosFiltrados
        if Produto.EstaDisponivelParaVenda()
    ]
    ValorTotalCusto = sum(
        (
            Produto.QuantidadeEstoque * Produto.PrecoCusto
            for Produto in ProdutosFiltrados
            if Produto.ControlaQuantidadeEstoque()
            and Produto.QuantidadeEstoque is not None
        ),
        Decimal("0.00"),
    )
    ValorTotalVenda = sum(
        (
            Produto.QuantidadeEstoque * Produto.PrecoVenda
            for Produto in ProdutosFiltrados
            if Produto.ControlaQuantidadeEstoque()
            and Produto.QuantidadeEstoque is not None
        ),
        Decimal("0.00"),
    )
    ProdutosFormatados = [
        {
            "Id": Produto.id,
            "Nome": Produto.Nome,
            "Categoria": Produto.Categoria or "Sem categoria",
            "Marca": Produto.Marca or "Sem marca",
            "Fornecedor": Produto.Fornecedor.Nome,
            "FornecedorId": Produto.Fornecedor_id,
            "UnidadeVenda": Produto.UnidadeVenda,
            "TipoVenda": Produto.get_UnidadeVenda_display(),
            "ControlaQuantidade": Produto.ControlaQuantidadeEstoque(),
            "Disponivel": Produto.EstaDisponivelParaVenda(),
            "EstoqueBaixo": Produto.EstaComEstoqueBaixo(),
            "EstoqueDescricao": (
                Produto.ObterDescricaoEstoque()
                if Produto.EhControladoPorDisponibilidade()
                else f"{FormatarQuantidade(Produto.QuantidadeEstoque)} {Produto.ObterUnidadeResumida()}"
            ),
            "Quantidade": Produto.QuantidadeEstoque,
            "QuantidadeFormatada": FormatarQuantidade(Produto.QuantidadeEstoque),
            "EstoqueMinimo": Produto.EstoqueMinimo,
            "EstoqueMinimoFormatado": FormatarQuantidade(Produto.EstoqueMinimo),
            "PrecoCusto": Produto.PrecoCusto,
            "PrecoCustoFormatado": FormatarValorMoeda(Produto.PrecoCusto),
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
        "ProdutosEstoqueBaixo": [
            ProdutoFormatado
            for ProdutoFormatado in ProdutosFormatados
            if ProdutoFormatado["EstoqueBaixo"]
        ],
        "ValorTotalCusto": ValorTotalCusto,
        "ValorTotalCustoFormatado": FormatarValorMoeda(ValorTotalCusto),
        "ValorTotalVenda": ValorTotalVenda,
        "ValorTotalVendaFormatado": FormatarValorMoeda(ValorTotalVenda),
    }
