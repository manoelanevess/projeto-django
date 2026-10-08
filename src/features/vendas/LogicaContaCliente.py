"""Regras das continhas de clientes."""
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django.db.models import Q, Sum

from .models import ContaCliente, LancamentoContaCliente


Centavo = Decimal("0.01")


def NormalizarNomeCliente(NomeCliente):
    Nome = " ".join(str(NomeCliente or "").split())

    if len(Nome) > 80:
        raise ValueError("O nome do cliente deve ter no máximo 80 caracteres.")

    if not Nome:
        raise ValueError("Informe o nome do cliente.")

    return Nome


def ConverterValorConta(Valor):
    try:
        ValorDecimal = Decimal(str(Valor).strip().replace(",", "."))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError("Informe um valor válido.") from None

    if ValorDecimal <= 0:
        raise ValueError("O valor deve ser maior que zero.")

    return ValorDecimal.quantize(Centavo, rounding=ROUND_HALF_UP)


def CalcularSaldoConta(Conta):
    Totais = Conta.Lancamentos.aggregate(
        Compras=Sum("Valor", filter=Q(Tipo=LancamentoContaCliente.COMPRA)),
        Pagamentos=Sum("Valor", filter=Q(Tipo=LancamentoContaCliente.PAGAMENTO)),
    )
    Compras = Totais["Compras"] or Decimal("0.00")
    Pagamentos = Totais["Pagamentos"] or Decimal("0.00")
    return (Compras - Pagamentos).quantize(Centavo, rounding=ROUND_HALF_UP)


def BuscarContinhasClientes(Proprietario, Busca=""):
    Contas = ContaCliente.objects.filter(Proprietario=Proprietario).prefetch_related(
        "Lancamentos",
        "Lancamentos__Venda",
    )

    if Busca:
        Contas = Contas.filter(NomeCliente__icontains=Busca)

    return Contas.order_by("NomeCliente")


def RegistrarPagamentoContaCliente(Proprietario, ContaId, ValorInformado, Descricao=""):
    try:
        Conta = ContaCliente.objects.get(pk=ContaId, Proprietario=Proprietario)
    except (ContaCliente.DoesNotExist, TypeError, ValueError):
        raise ValueError("Continha não encontrada.") from None

    Valor = ConverterValorConta(ValorInformado)
    DescricaoLimpa = " ".join(str(Descricao or "").split())[:140]

    LancamentoContaCliente.objects.create(
        Conta=Conta,
        Tipo=LancamentoContaCliente.PAGAMENTO,
        Descricao=DescricaoLimpa or "Pagamento recebido",
        Valor=Valor,
    )

    return Conta
