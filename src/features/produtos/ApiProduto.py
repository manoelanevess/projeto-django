"""Acesso aos dados persistidos da feature de produtos."""
from django.db.models import F, Q

from .models import Produto


def MontarFiltroProdutosDisponiveis():
    return Q(UnidadeVenda=Produto.QUILOGRAMA, Disponivel=True) | (
        ~Q(UnidadeVenda=Produto.QUILOGRAMA) & Q(QuantidadeEstoque__gt=0)
    )


def BuscarProdutos(Busca="", Estoque="", Categoria="", Fornecedor=""):
    Produtos = Produto.objects.filter(Ativo=True).select_related("Fornecedor")

    if Busca:
        Produtos = Produtos.filter(
            Q(Nome__icontains=Busca)
            | Q(Categoria__icontains=Busca)
            | Q(Marca__icontains=Busca)
            | Q(Fornecedor__Nome__icontains=Busca)
        )

    if Categoria:
        Produtos = Produtos.filter(Categoria__iexact=Categoria)

    if Fornecedor:
        if str(Fornecedor).isdigit():
            Produtos = Produtos.filter(Fornecedor_id=Fornecedor)
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

    return Produtos.order_by("Nome")


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
        Produto.objects.select_related("Fornecedor").filter(
            Q(Nome__icontains=Busca)
            | Q(Categoria__icontains=Busca)
            | Q(Marca__icontains=Busca)
            | Q(Fornecedor__Nome__icontains=Busca),
            Ativo=True,
        )
        .filter(MontarFiltroProdutosDisponiveis())
        .order_by("Nome")[:20]
    )
