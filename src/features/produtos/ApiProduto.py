"""Acesso aos dados persistidos da feature de produtos."""
from django.db.models import F, Q

from .models import Produto


def BuscarProdutos(Busca="", Estoque=""):
    Produtos = Produto.objects.filter(Ativo=True)

    if Busca:
        Produtos = Produtos.filter(
            Q(Nome__icontains=Busca) | Q(Categoria__icontains=Busca)
        )

    if Estoque == "baixo":
        Produtos = Produtos.filter(QuantidadeEstoque__lte=F("EstoqueMinimo"))

    return Produtos.order_by("Nome")


def BuscarProdutosParaVenda(Busca):
    if not Busca:
        return Produto.objects.none()

    return (
        Produto.objects.filter(
            Q(Nome__icontains=Busca) | Q(Categoria__icontains=Busca),
            Ativo=True,
            QuantidadeEstoque__gt=0,
        )
        .order_by("Nome")[:20]
    )
