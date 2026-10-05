"""Acesso aos dados persistidos da feature de produtos."""
from django.db.models import F, Prefetch, Q

from .models import LoteEstoque, Produto


def ObterPrefetchLotesAtivos():
    return Prefetch(
        "LotesEstoque",
        queryset=LoteEstoque.objects.filter(Ativo=True)
        .select_related("Fornecedor")
        .order_by("CriadoEm", "id"),
        to_attr="LotesAtivos",
    )


def ObterLotesDisponiveisProduto(ProdutoVenda):
    Lotes = getattr(ProdutoVenda, "LotesAtivos", None)

    if Lotes is None:
        Lotes = list(
            ProdutoVenda.LotesEstoque.filter(Ativo=True)
            .select_related("Fornecedor")
            .order_by("CriadoEm", "id")
        )

    return [Lote for Lote in Lotes if Lote.EstaDisponivelParaVenda()]


def MontarFiltroProdutosDisponiveis():
    return Q(UnidadeVenda=Produto.QUILOGRAMA, Disponivel=True) | (
        ~Q(UnidadeVenda=Produto.QUILOGRAMA) & Q(QuantidadeEstoque__gt=0)
    )


def BuscarProdutos(Busca="", Estoque="", Categoria="", Fornecedor=""):
    Produtos = (
        Produto.objects.filter(Ativo=True)
        .select_related("Fornecedor")
        .prefetch_related(ObterPrefetchLotesAtivos())
    )

    if Busca:
        Produtos = Produtos.filter(
            Q(Nome__icontains=Busca)
            | Q(Categoria__icontains=Busca)
            | Q(Marca__icontains=Busca)
            | Q(Fornecedor__Nome__icontains=Busca)
            | Q(
                LotesEstoque__Fornecedor__Nome__icontains=Busca,
                LotesEstoque__Ativo=True,
            )
        )

    if Categoria:
        Produtos = Produtos.filter(Categoria__iexact=Categoria)

    if Fornecedor:
        if str(Fornecedor).isdigit():
            Produtos = Produtos.filter(
                Q(Fornecedor_id=Fornecedor)
                | Q(
                    LotesEstoque__Fornecedor_id=Fornecedor,
                    LotesEstoque__Ativo=True,
                )
            )
        else:
            Produtos = Produtos.none()

    if Estoque == "baixo":
        Produtos = Produtos.exclude(UnidadeVenda=Produto.QUILOGRAMA).filter(
            QuantidadeEstoque__lte=F("EstoqueMinimo")
        )
    elif Estoque == "disponivel":
        Produtos = Produtos.filter(MontarFiltroProdutosDisponiveis())
    elif Estoque == "indisponivel":
        Produtos = Produtos.exclude(MontarFiltroProdutosDisponiveis())

    return Produtos.distinct().order_by("Nome")


def BuscarCategoriasProdutos():
    return list(
        Produto.objects.filter(Ativo=True)
        .exclude(Categoria="")
        .order_by("Categoria")
        .values_list("Categoria", flat=True)
        .distinct()
    )


def BuscarProdutosParaVenda(Busca):
    if not Busca:
        return Produto.objects.none()

    return (
        Produto.objects.select_related("Fornecedor")
        .prefetch_related(ObterPrefetchLotesAtivos())
        .filter(
            Q(Nome__icontains=Busca)
            | Q(Categoria__icontains=Busca)
            | Q(Marca__icontains=Busca)
            | Q(Fornecedor__Nome__icontains=Busca)
            | Q(
                LotesEstoque__Fornecedor__Nome__icontains=Busca,
                LotesEstoque__Ativo=True,
            ),
            Ativo=True,
        )
        .filter(MontarFiltroProdutosDisponiveis())
        .distinct()
        .order_by("Nome")[:20]
    )
