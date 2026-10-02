"""Componente do painel de indicadores e vendas recentes."""
from html import escape

from django.http import HttpResponse
from django.utils import timezone

from componentes.LayoutBase import RenderizarLayoutBase
from features.produtos.LogicaProduto import FormatarValorMoeda, GerarResumoProdutos
from features.vendas.ApiVenda import BuscarVendasRecentes, ContarVendasHoje


def ComponenteDashboard(Request):
    ResumoProdutos = GerarResumoProdutos()
    VendasRecentes = BuscarVendasRecentes()
    LinhasVendas = "".join(
        f"""
        <tr>
            <td>#{VendaRealizada.id}</td>
            <td>{timezone.localtime(VendaRealizada.CriadaEm).strftime('%d/%m/%Y %H:%M')}</td>
            <td>{escape(VendaRealizada.NomeCliente or 'Não identificado')}</td>
            <td>{escape(VendaRealizada.get_FormaPagamento_display())}</td>
            <td>R$ {FormatarValorMoeda(VendaRealizada.Total)}</td>
        </tr>
        """
        for VendaRealizada in VendasRecentes
    )

    if LinhasVendas:
        HistoricoVendas = f"""
        <section class="PainelTabela" aria-label="Vendas recentes">
            <table>
                <thead>
                    <tr>
                        <th>Venda</th>
                        <th>Data</th>
                        <th>Cliente</th>
                        <th>Pagamento</th>
                        <th>Total</th>
                    </tr>
                </thead>
                <tbody>{LinhasVendas}</tbody>
            </table>
        </section>
        """
    else:
        HistoricoVendas = """
        <section class="EstadoVazio">
            <h2>Nenhuma venda concluída</h2>
            <p>As vendas concluídas aparecerão aqui.</p>
            <a class="BotaoPrimario" href="/carrinho">Abrir carrinho</a>
        </section>
        """

    ConteudoPrincipal = f"""
    <h1>Dashboard</h1>

    <section class="GridIndicadores" aria-label="Indicadores do comércio">
        <article class="CardIndicador" style="--CorDestaque: #2d74d8;">
            <div>
                <strong>Produtos cadastrados</strong>
                <span>{ResumoProdutos["TotalProdutos"]}</span>
            </div>
            <div class="IconeIndicador" aria-hidden="true">QT</div>
        </article>

        <article class="CardIndicador" style="--CorDestaque: #f59f18;">
            <div>
                <strong>Produtos em alerta</strong>
                <span>{ResumoProdutos["TotalEstoqueBaixo"]}</span>
            </div>
            <div class="IconeIndicador" aria-hidden="true">!</div>
        </article>

        <article class="CardIndicador" style="--CorDestaque: #00a889;">
            <div>
                <strong>Vendas hoje</strong>
                <span>{ContarVendasHoje()}</span>
            </div>
            <div class="IconeIndicador" aria-hidden="true">MV</div>
        </article>
    </section>

    <h2>Vendas recentes</h2>
    {HistoricoVendas}
    """

    return HttpResponse(
        RenderizarLayoutBase("Dashboard", ConteudoPrincipal, RotaAtiva="dashboard")
    )
