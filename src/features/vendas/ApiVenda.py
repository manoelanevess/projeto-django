"""Consultas de vendas concluídas para outras features."""
from django.utils import timezone

from .models import Venda


def ContarVendasHoje():
    return Venda.objects.filter(CriadaEm__date=timezone.localdate()).count()


def BuscarVendasRecentes(Limite=5):
    return Venda.objects.select_related("Proprietario").all()[:Limite]
