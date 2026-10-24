"""Consultas de vendas concluídas para outras features."""
from django.db.models import Q
from django.utils import timezone

from .LogicaVenda import ObterIntervaloDiaComercial
from .models import RegistroVendaAntiga, Venda


def ContarVendasHoje(Proprietario=None):
    VendasHoje = Venda.objects.filter(CriadaEm__date=timezone.localdate())

    if Proprietario is not None:
        VendasHoje = VendasHoje.filter(Proprietario=Proprietario)

    return VendasHoje.count()


def BuscarVendasRecentes(Limite=5, Proprietario=None):
    InicioDiaComercial, FimDiaComercial = ObterIntervaloDiaComercial()
    VendasRecentes = Venda.objects.filter(
        CriadaEm__gte=InicioDiaComercial,
        CriadaEm__lt=FimDiaComercial,
    ).select_related("Proprietario").prefetch_related(
        "Itens"
    )

    if Proprietario is not None:
        VendasRecentes = VendasRecentes.filter(Proprietario=Proprietario)

    return VendasRecentes[:Limite]


def FiltrarVendasHistorico(Vendas, Filtros, CampoNumero):
    Busca = Filtros.get("Busca", "")

    if Busca:
        FiltroBusca = Q(NomeCliente__icontains=Busca) | Q(Itens__NomeProduto__icontains=Busca)

        if Busca.isdecimal():
            FiltroBusca |= Q(**{CampoNumero: int(Busca)})

        Vendas = Vendas.filter(FiltroBusca).distinct()

    if Filtros.get("DataInicial"):
        Vendas = Vendas.filter(CriadaEm__date__gte=Filtros["DataInicial"])

    if Filtros.get("DataFinal"):
        Vendas = Vendas.filter(CriadaEm__date__lte=Filtros["DataFinal"])

    if Filtros.get("Pagamento"):
        Vendas = Vendas.filter(FormaPagamento=Filtros["Pagamento"])

    return Vendas.order_by("-CriadaEm", "-id")[:100]


def BuscarHistoricoVendas(Proprietario, Filtros):
    Vendas = Venda.objects.filter(Proprietario=Proprietario).prefetch_related("Itens")
    Registros = RegistroVendaAntiga.objects.filter(
        Proprietario=Proprietario
    ).prefetch_related("Itens")

    if Filtros.get("Situacao") == "atual":
        Registros = Registros.none()
    elif Filtros.get("Situacao") == "arquivada":
        Vendas = Vendas.none()

    return (
        FiltrarVendasHistorico(Vendas, Filtros, "id"),
        FiltrarVendasHistorico(Registros, Filtros, "VendaOriginalId"),
    )
