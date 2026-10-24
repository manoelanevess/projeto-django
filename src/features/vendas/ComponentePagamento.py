"""Resumo da divisão do pagamento nas vendas atuais e arquivadas."""
from features.produtos.LogicaProduto import FormatarValorMoeda

from .models import Venda


def RenderizarDivisaoPagamento(VendaRealizada):
    if VendaRealizada.FormaPagamento != Venda.PIX_DINHEIRO:
        return ""

    ValorDinheiro = VendaRealizada.Total - VendaRealizada.ValorPix
    return f"""
    <p class="ResumoPagamentoVenda">
        PIX: R$ {FormatarValorMoeda(VendaRealizada.ValorPix)} ·
        Dinheiro: R$ {FormatarValorMoeda(ValorDinheiro)} ·
        Recebido em dinheiro: R$ {FormatarValorMoeda(VendaRealizada.ValorRecebido)} ·
        Troco: R$ {FormatarValorMoeda(VendaRealizada.Troco)}
    </p>
    """
