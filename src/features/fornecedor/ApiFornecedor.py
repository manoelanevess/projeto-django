"""Acesso aos dados persistidos da feature de fornecedores."""
from django.db.models import Q

from .models import Fornecedor


def BuscarFornecedores(Busca="", SomenteAtivos=True):
    Fornecedores = Fornecedor.objects.all()

    if SomenteAtivos:
        Fornecedores = Fornecedores.filter(Ativo=True)

    if Busca:
        Fornecedores = Fornecedores.filter(
            Q(Nome__icontains=Busca)
            | Q(Telefone__icontains=Busca)
            | Q(Email__icontains=Busca)
            | Q(Cidade__icontains=Busca)
        )

    return Fornecedores.order_by("Nome")


def BuscarFornecedoresAtivos():
    return BuscarFornecedores()


def BuscarFornecedoresParaFiltroEstoque():
    return (
        Fornecedor.objects.filter(Q(Ativo=True) | Q(Produtos__Ativo=True))
        .distinct()
        .order_by("Nome")
    )
