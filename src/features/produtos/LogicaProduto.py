"""Regras de consulta e apresentação da feature de produtos."""
from decimal import Decimal

from .ApiProduto import BuscarProdutos, ObterLotesDisponiveisProduto


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
    ValorTotalCusto = Decimal("0.00")
    ValorTotalVenda = Decimal("0.00")
    ProdutosFormatados = []

    for Produto in ProdutosFiltrados:
        LotesAtivos = getattr(Produto, "LotesAtivos", [])
        LotesDisponiveis = ObterLotesDisponiveisProduto(Produto)
        LoteReferencia = (
            LotesDisponiveis[0]
            if LotesDisponiveis
            else LotesAtivos[0]
            if LotesAtivos
            else None
        )

        if Produto.ControlaQuantidadeEstoque():
            for Lote in LotesAtivos:
                QuantidadeLote = Lote.QuantidadeDisponivel or Decimal("0.000")
                ValorTotalCusto += QuantidadeLote * Lote.PrecoCusto
                ValorTotalVenda += QuantidadeLote * Lote.PrecoVenda

        PrecoCusto = (
            LoteReferencia.PrecoCusto if LoteReferencia else Produto.PrecoCusto
        )
        PrecoVenda = (
            LoteReferencia.PrecoVenda if LoteReferencia else Produto.PrecoVenda
        )
        FornecedorReferencia = (
            LoteReferencia.Fornecedor if LoteReferencia else Produto.Fornecedor
        )
        LotesFormatados = [
            {
                "Id": Lote.id,
                "Numero": Lote.Numero,
                "Fornecedor": Lote.Fornecedor.Nome,
                "Quantidade": Lote.QuantidadeDisponivel,
                "EstoqueDescricao": (
                    Lote.ObterDescricaoEstoque()
                    if Produto.EhControladoPorDisponibilidade()
                    else f"{FormatarQuantidade(Lote.QuantidadeDisponivel)} {Produto.ObterUnidadeResumida()}"
                ),
                "PrecoCusto": Lote.PrecoCusto,
                "PrecoCustoFormatado": FormatarValorMoeda(Lote.PrecoCusto),
                "PrecoVenda": Lote.PrecoVenda,
                "PrecoVendaFormatado": FormatarValorMoeda(Lote.PrecoVenda),
                "Disponivel": Lote.EstaDisponivelParaVenda(),
            }
            for Lote in LotesAtivos
        ]
        ProdutosFormatados.append({
            "Id": Produto.id,
            "Nome": Produto.Nome,
            "Categoria": Produto.Categoria or "Sem categoria",
            "Marca": Produto.Marca or "Sem marca",
            "Fornecedor": FornecedorReferencia.Nome,
            "FornecedorId": FornecedorReferencia.id,
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
            "PrecoCusto": PrecoCusto,
            "PrecoCustoFormatado": FormatarValorMoeda(PrecoCusto),
            "PrecoVenda": PrecoVenda,
            "PrecoVendaFormatado": FormatarValorMoeda(PrecoVenda),
            "Unidade": Produto.ObterUnidadeResumida(),
            "Lotes": LotesFormatados,
            "QuantidadeLotes": len(LotesAtivos),
            "QuantidadeLotesDisponiveis": len(LotesDisponiveis),
        })

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
