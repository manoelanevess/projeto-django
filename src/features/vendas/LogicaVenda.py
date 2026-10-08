"""Regras financeiras e de retenção do histórico de vendas."""
from collections import defaultdict
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from .models import (
    ItemRegistroVendaAntiga,
    RegistroVendaAntiga,
    ResumoVendaMensal,
    Venda,
)


HoraInicioDiaComercial = 7


def SomarCampo(Queryset, Campo):
    return Queryset.aggregate(Valor=Sum(Campo))["Valor"] or Decimal("0.00")


def NormalizarDataHoraReferencia(DataReferencia=None):
    FusoHorario = timezone.get_current_timezone()

    if DataReferencia is None:
        return timezone.localtime()

    if isinstance(DataReferencia, datetime):
        if timezone.is_naive(DataReferencia):
            DataReferencia = timezone.make_aware(DataReferencia, FusoHorario)
        return timezone.localtime(DataReferencia, FusoHorario)

    return timezone.make_aware(
        datetime.combine(DataReferencia, time(hour=12)),
        FusoHorario,
    )


def ObterIntervaloDiaComercial(DataReferencia=None):
    DataHoraLocal = NormalizarDataHoraReferencia(DataReferencia)
    DiaComercial = DataHoraLocal.date()

    if DataHoraLocal.hour < HoraInicioDiaComercial:
        DiaComercial -= timedelta(days=1)

    InicioDiaComercial = timezone.make_aware(
        datetime.combine(DiaComercial, time(hour=HoraInicioDiaComercial)),
        timezone.get_current_timezone(),
    )
    FimDiaComercial = InicioDiaComercial + timedelta(days=1)
    return InicioDiaComercial, FimDiaComercial


def ConsolidarVendasDeMesesAnteriores(DataReferencia=None):
    Hoje = DataReferencia or timezone.localdate()
    InicioMesAtual = date(Hoje.year, Hoje.month, 1)
    VendasAntigas = list(
        Venda.objects.filter(CriadaEm__date__lt=InicioMesAtual)
        .select_related("Proprietario")
        .prefetch_related("Itens")
    )

    if not VendasAntigas:
        return 0

    IdentificadoresVendas = [VendaAntiga.id for VendaAntiga in VendasAntigas]
    TotaisPorMes = defaultdict(
        lambda: {
            "QuantidadeVendas": 0,
            "TotalVendido": Decimal("0.00"),
            "Lucro": Decimal("0.00"),
            "Vendas": [],
        }
    )

    for VendaAntiga in VendasAntigas:
        DataVenda = timezone.localtime(VendaAntiga.CriadaEm)
        Chave = (
            VendaAntiga.Proprietario_id,
            DataVenda.year,
            DataVenda.month,
        )
        TotaisPorMes[Chave]["QuantidadeVendas"] += 1
        TotaisPorMes[Chave]["TotalVendido"] += VendaAntiga.Total
        TotaisPorMes[Chave]["Lucro"] += VendaAntiga.Lucro
        TotaisPorMes[Chave]["Vendas"].append(VendaAntiga.id)

    with transaction.atomic():
        RegistrosExistentes = set(
            RegistroVendaAntiga.objects.select_for_update()
            .filter(VendaOriginalId__in=IdentificadoresVendas)
            .values_list("VendaOriginalId", flat=True)
        )
        NovosItensAntigos = []

        for VendaAntiga in VendasAntigas:
            if VendaAntiga.id in RegistrosExistentes:
                continue

            RegistroAntigo = RegistroVendaAntiga.objects.create(
                Proprietario=VendaAntiga.Proprietario,
                VendaOriginalId=VendaAntiga.id,
                NomeCliente=VendaAntiga.NomeCliente,
                FormaPagamento=VendaAntiga.FormaPagamento,
                Total=VendaAntiga.Total,
                Lucro=VendaAntiga.Lucro,
                ValorRecebido=VendaAntiga.ValorRecebido,
                Troco=VendaAntiga.Troco,
                CriadaEm=VendaAntiga.CriadaEm,
            )

            for ItemAntigo in VendaAntiga.Itens.all():
                NovosItensAntigos.append(
                    ItemRegistroVendaAntiga(
                        Registro=RegistroAntigo,
                        NomeProduto=ItemAntigo.NomeProduto,
                        UnidadeVenda=ItemAntigo.UnidadeVenda,
                        Quantidade=ItemAntigo.Quantidade,
                        PrecoUnitario=ItemAntigo.PrecoUnitario,
                        Subtotal=ItemAntigo.Subtotal,
                    )
                )

        if NovosItensAntigos:
            ItemRegistroVendaAntiga.objects.bulk_create(NovosItensAntigos)

        for (ProprietarioId, Ano, Mes), Totais in TotaisPorMes.items():
            Resumo, _ = ResumoVendaMensal.objects.select_for_update().get_or_create(
                Proprietario_id=ProprietarioId,
                Ano=Ano,
                Mes=Mes,
            )
            Resumo.QuantidadeVendas += Totais["QuantidadeVendas"]
            Resumo.TotalVendido += Totais["TotalVendido"]
            Resumo.Lucro += Totais["Lucro"]
            Resumo.save(
                update_fields=["QuantidadeVendas", "TotalVendido", "Lucro"]
            )
            Venda.objects.filter(id__in=Totais["Vendas"]).delete()

    return len(VendasAntigas)


def ObterResumoFinanceiro(Proprietario, DataReferencia=None):
    DataHoraLocal = NormalizarDataHoraReferencia(DataReferencia)
    Hoje = DataHoraLocal.date()
    InicioDiaComercial, FimDiaComercial = ObterIntervaloDiaComercial(
        DataHoraLocal
    )
    VendasProprietario = Venda.objects.filter(Proprietario=Proprietario)
    VendasHoje = VendasProprietario.filter(
        CriadaEm__gte=InicioDiaComercial,
        CriadaEm__lt=FimDiaComercial,
    )
    VendasMes = VendasProprietario.filter(
        CriadaEm__year=Hoje.year,
        CriadaEm__month=Hoje.month,
    )
    VendasAno = VendasProprietario.filter(CriadaEm__year=Hoje.year)
    ResumosAno = ResumoVendaMensal.objects.filter(
        Proprietario=Proprietario,
        Ano=Hoje.year,
    )

    LucroHoje = SomarCampo(VendasHoje, "Lucro")
    LucroMes = SomarCampo(VendasMes, "Lucro")
    LucroAno = SomarCampo(VendasAno, "Lucro") + SomarCampo(ResumosAno, "Lucro")
    TotalVendidoHoje = SomarCampo(VendasHoje, "Total")
    TotalVendidoMes = SomarCampo(VendasMes, "Total")
    TotalVendidoAno = SomarCampo(VendasAno, "Total") + SomarCampo(
        ResumosAno,
        "TotalVendido",
    )

    return {
        "LucroHoje": LucroHoje,
        "LucroMes": LucroMes,
        "LucroAno": LucroAno,
        "TotalVendidoHoje": TotalVendidoHoje,
        "TotalVendidoMes": TotalVendidoMes,
        "TotalVendidoAno": TotalVendidoAno,
        "CustoProdutosHoje": TotalVendidoHoje - LucroHoje,
        "CustoProdutosMes": TotalVendidoMes - LucroMes,
        "CustoProdutosAno": TotalVendidoAno - LucroAno,
    }
