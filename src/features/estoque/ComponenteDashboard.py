"""Componente do painel de indicadores, alertas e vendas recentes."""
from html import escape

from django.http import HttpResponse
from django.utils import timezone

from componentes.LayoutBase import RenderizarLayoutBase
from features.produtos.LogicaProduto import FormatarValorMoeda, GerarResumoProdutos
from features.vendas.ApiVenda import BuscarVendasRecentes
from features.vendas.LogicaVenda import (
    ConsolidarVendasDeMesesAnteriores,
    ObterResumoFinanceiro,
)


def RenderizarProdutosEmAlerta(ProdutosEstoqueBaixo):
    if not ProdutosEstoqueBaixo:
        return """
        <section class="EstadoVazio EstadoEstoqueSaudavel">
            <h2>Nenhum produto com estoque baixo</h2>
            <p>Todos os produtos com quantidade controlada estão acima do mínimo.</p>
        </section>
        """

    Linhas = "".join(
        f"""
        <tr>
            <td><strong>{escape(ProdutoEstoque['Nome'])}</strong></td>
            <td>{escape(ProdutoEstoque['Marca'])}</td>
            <td>{escape(ProdutoEstoque['Fornecedor'])}</td>
            <td>{escape(ProdutoEstoque['EstoqueDescricao'])}</td>
            <td>{escape(ProdutoEstoque['EstoqueMinimoFormatado'])} {escape(ProdutoEstoque['Unidade'])}</td>
            <td>R$ {escape(ProdutoEstoque['PrecoCustoFormatado'])}</td>
            <td>R$ {escape(ProdutoEstoque['PrecoVendaFormatado'])}</td>
            <td>
                <a class="LinkEditarProduto" href="/estoque/{ProdutoEstoque['Id']}/editar">
                    Ajustar
                </a>
            </td>
        </tr>
        """
        for ProdutoEstoque in ProdutosEstoqueBaixo
    )

    return f"""
    <section class="PainelTabela TabelaAlertas" aria-label="Produtos com estoque baixo">
        <table>
            <thead>
                <tr>
                    <th>Produto</th>
                    <th>Marca</th>
                    <th>Fornecedor</th>
                    <th>Estoque atual</th>
                    <th>Estoque mínimo</th>
                    <th>Preço de custo</th>
                    <th>Preço de venda</th>
                    <th><span class="SomenteLeitorTela">Ações</span></th>
                </tr>
            </thead>
            <tbody>{Linhas}</tbody>
        </table>
    </section>
    """


def RenderizarVendasRecentes(VendasRecentes):
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

    if not LinhasVendas:
        return """
        <section class="EstadoVazio">
            <h2>Nenhuma venda concluída neste mês</h2>
            <p>As vendas concluídas aparecerão aqui.</p>
            <a class="BotaoPrimario" href="/carrinho">Abrir carrinho</a>
        </section>
        """

    return f"""
    <section class="PainelTabela" aria-label="Vendas recentes">
        <table>
            <thead>
                <tr>
                    <th>Venda</th>
                    <th>Data</th>
                    <th>Cliente</th>
                    <th>Pagamento</th>
                    <th>Total da compra</th>
                </tr>
            </thead>
            <tbody>{LinhasVendas}</tbody>
        </table>
    </section>
    """


def ComponenteDashboard(Request):
    ConsolidarVendasDeMesesAnteriores()
    ResumoProdutos = GerarResumoProdutos()
    ResumoFinanceiro = ObterResumoFinanceiro(Request.user)
    ProdutosEmAlerta = RenderizarProdutosEmAlerta(
        ResumoProdutos["ProdutosEstoqueBaixo"]
    )
    HistoricoVendas = RenderizarVendasRecentes(
        BuscarVendasRecentes(Proprietario=Request.user)
    )

    ConteudoPrincipal = f"""
    <style>
        .GridIndicadoresDashboard {{ margin-top: 18px; }}
        .CardIndicadorFinanceiro span {{ font-size: 22px; }}
        .TituloSecaoDashboard {{ margin: 28px 0 12px; }}
        .TituloSecaoDashboard h2 {{ margin: 0; }}
        .TabelaAlertas {{ overflow-x: auto; }}
        .TabelaAlertas table {{ min-width: 940px; }}
        .LinkEditarProduto {{ color: #056da8; font-weight: 700; text-decoration: none; }}
        .LinkEditarProduto:hover,
        .LinkEditarProduto:focus-visible {{ text-decoration: underline; }}
        .EstadoEstoqueSaudavel {{ border-left: 4px solid #00a889; }}
    </style>

    <h1>Dashboard</h1>

    <section class="GridIndicadores GridIndicadoresDashboard" aria-label="Indicadores do comércio">
        <article class="CardIndicador" style="--CorDestaque: #2d74d8;">
            <div>
                <strong>Produtos cadastrados</strong>
                <span>{ResumoProdutos["TotalProdutos"]}</span>
            </div>
            <div class="IconeIndicador" aria-hidden="true">QT</div>
        </article>

        <article class="CardIndicador CardIndicadorFinanceiro" style="--CorDestaque: #1769aa;">
            <div>
                <strong>Valor do estoque</strong>
                <span>R$ {ResumoProdutos["ValorTotalCustoFormatado"]}</span>
            </div>
            <div class="IconeIndicador" aria-hidden="true">R$</div>
        </article>

        <article class="CardIndicador" style="--CorDestaque: #f59f18;">
            <div>
                <strong>Produtos com estoque baixo</strong>
                <span>{ResumoProdutos["TotalEstoqueBaixo"]}</span>
            </div>
            <div class="IconeIndicador" aria-hidden="true">!</div>
        </article>

        <article class="CardIndicador CardIndicadorFinanceiro" style="--CorDestaque: #00a889;">
            <div>
                <strong>Lucro hoje</strong>
                <span>R$ {FormatarValorMoeda(ResumoFinanceiro["LucroHoje"])}</span>
            </div>
            <div class="IconeIndicador" aria-hidden="true">D</div>
        </article>

        <article class="CardIndicador CardIndicadorFinanceiro" style="--CorDestaque: #14866d;">
            <div>
                <strong>Lucro no mês</strong>
                <span>R$ {FormatarValorMoeda(ResumoFinanceiro["LucroMes"])}</span>
            </div>
            <div class="IconeIndicador" aria-hidden="true">M</div>
        </article>

        <article class="CardIndicador CardIndicadorFinanceiro" style="--CorDestaque: #536a7a;">
            <div>
                <strong>Lucro no ano</strong>
                <span>R$ {FormatarValorMoeda(ResumoFinanceiro["LucroAno"])}</span>
            </div>
            <div class="IconeIndicador" aria-hidden="true">A</div>
        </article>
    </section>

    <div class="TituloSecaoDashboard">
        <h2>Produtos com estoque baixo</h2>
    </div>
    {ProdutosEmAlerta}

    <div class="TituloSecaoDashboard">
        <h2>Vendas recentes</h2>
    </div>
    {HistoricoVendas}
    """

    return HttpResponse(
        RenderizarLayoutBase("Dashboard", ConteudoPrincipal, RotaAtiva="dashboard")
    )
