"""Consultas de vendas concluídas para outras features."""
from django.utils import timezone

from .models import Venda


def ContarVendasHoje(Proprietario=None):
    VendasHoje = Venda.objects.filter(CriadaEm__date=timezone.localdate())

    if Proprietario is not None:
        VendasHoje = VendasHoje.filter(Proprietario=Proprietario)

    return VendasHoje.count()


def BuscarVendasRecentes(Limite=5, Proprietario=None):
    VendasRecentes = Venda.objects.select_related("Proprietario").prefetch_related(
        "Itens"
    )

    if Proprietario is not None:
        VendasRecentes = VendasRecentes.filter(Proprietario=Proprietario)

    return VendasRecentes[:Limite]
