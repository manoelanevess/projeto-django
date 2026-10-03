"""Componente do painel de indicadores, alertas e vendas recentes."""
from html import escape

from django.http import HttpResponse
from django.utils import timezone

from componentes.LayoutBase import RenderizarLayoutBase
from features.produtos.LogicaProduto import (
    FormatarQuantidade,
    FormatarValorMoeda,
    GerarResumoProdutos,
)
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


def ObterUnidadeResumidaItem(UnidadeVenda):
    return {
        "quilograma": "kg",
        "metro": "m",
        "valor_fixo": "item",
    }.get(UnidadeVenda, "un")


def RenderizarItensVenda(VendaRealizada):
    Itens = "".join(
        f"""
        <li>
            <strong>{escape(ItemVenda.NomeProduto)}</strong>
            <span>{FormatarQuantidade(ItemVenda.Quantidade)} {ObterUnidadeResumidaItem(ItemVenda.UnidadeVenda)} × R$ {FormatarValorMoeda(ItemVenda.PrecoUnitario)}</span>
            <b>R$ {FormatarValorMoeda(ItemVenda.Subtotal)}</b>
        </li>
        """
        for ItemVenda in VendaRealizada.Itens.all()
    )

    if Itens:
        return f'<ul class="ListaItensVenda">{Itens}</ul>'

    return '<p class="VendaSemItens">Nenhum item registrado nesta venda.</p>'


def RenderizarVendasRecentes(VendasRecentes):
    LinhasVendas = []

    for VendaRealizada in VendasRecentes:
        IdDetalhes = f"DetalhesVenda{VendaRealizada.id}"
        LinhasVendas.append(
            f"""
            <tr class="LinhaVendaRecente" data-detalhe-venda="{IdDetalhes}">
                <td>
                    <button
                        class="BotaoDetalhesVenda"
                        type="button"
                        aria-expanded="false"
                        aria-controls="{IdDetalhes}"
                        aria-label="Mostrar itens da venda #{VendaRealizada.id}"
                        title="Mostrar itens da venda"
                    ><span aria-hidden="true">+</span></button>
                    <strong>#{VendaRealizada.id}</strong>
                </td>
                <td>{timezone.localtime(VendaRealizada.CriadaEm).strftime('%d/%m/%Y %H:%M')}</td>
                <td>{escape(VendaRealizada.NomeCliente or 'Não identificado')}</td>
                <td>{escape(VendaRealizada.get_FormaPagamento_display())}</td>
                <td>R$ {FormatarValorMoeda(VendaRealizada.Total)}</td>
            </tr>
            <tr class="LinhaDetalhesVenda" id="{IdDetalhes}" hidden>
                <td colspan="5">
                    <div class="ConteudoDetalhesVenda">
                        <strong>Itens da venda</strong>
                        {RenderizarItensVenda(VendaRealizada)}
                    </div>
                </td>
            </tr>
            """
        )

    LinhasVendas = "".join(LinhasVendas)

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
    <script>
        (() => {{
            const LinhasVenda = document.querySelectorAll("[data-detalhe-venda]");

            function AlternarDetalhesVenda(LinhaVenda) {{
                const IdDetalhes = LinhaVenda.dataset.detalheVenda;
                const DetalhesVenda = document.getElementById(IdDetalhes);
                const BotaoDetalhes = LinhaVenda.querySelector(".BotaoDetalhesVenda");
                const VaiAbrir = DetalhesVenda.hidden;

                DetalhesVenda.hidden = !VaiAbrir;
                BotaoDetalhes.setAttribute("aria-expanded", String(VaiAbrir));
                BotaoDetalhes.setAttribute(
                    "aria-label",
                    `${{VaiAbrir ? "Ocultar" : "Mostrar"}} itens da venda`,
                );
                BotaoDetalhes.title = VaiAbrir
                    ? "Ocultar itens da venda"
                    : "Mostrar itens da venda";
                BotaoDetalhes.querySelector("span").textContent = VaiAbrir ? "-" : "+";
            }}

            LinhasVenda.forEach((LinhaVenda) => {{
                LinhaVenda.addEventListener("click", () => {{
                    AlternarDetalhesVenda(LinhaVenda);
                }});
            }});
        }})();
    </script>
    """


def RenderizarResultadoFinanceiro(ResumoFinanceiro):
    Periodos = [
        (
            "Hoje",
            ResumoFinanceiro["TotalVendidoHoje"],
            ResumoFinanceiro["CustoProdutosHoje"],
            ResumoFinanceiro["LucroHoje"],
        ),
        (
            "Mês",
            ResumoFinanceiro["TotalVendidoMes"],
            ResumoFinanceiro["CustoProdutosMes"],
            ResumoFinanceiro["LucroMes"],
        ),
        (
            "Ano",
            ResumoFinanceiro["TotalVendidoAno"],
            ResumoFinanceiro["CustoProdutosAno"],
            ResumoFinanceiro["LucroAno"],
        ),
    ]
    Linhas = "".join(
        f"""
        <tr>
            <th scope="row">{Periodo}</th>
            <td class="ValorEntrada">R$ {FormatarValorMoeda(Entrada)}</td>
            <td class="ValorCusto">R$ {FormatarValorMoeda(Custo)}</td>
            <td class="ValorLucroProdutos">R$ {FormatarValorMoeda(Lucro)}</td>
        </tr>
        """
        for Periodo, Entrada, Custo, Lucro in Periodos
    )

    return f"""
    <section class="PainelResultadoFinanceiro" aria-labelledby="TituloResultadoFinanceiro">
        <div class="CabecalhoResultadoFinanceiro">
            <h2 id="TituloResultadoFinanceiro">Entradas, custos e lucro dos produtos</h2>
        </div>
        <div class="TabelaResultadoFinanceiro">
            <table>
                <thead>
                    <tr>
                        <th>Período</th>
                        <th>Entradas das vendas</th>
                        <th>Custo dos produtos vendidos</th>
                        <th>Lucro dos produtos</th>
                    </tr>
                </thead>
                <tbody>{Linhas}</tbody>
            </table>
        </div>
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
    ResultadoFinanceiro = RenderizarResultadoFinanceiro(ResumoFinanceiro)

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
        .PainelResultadoFinanceiro {{
            margin-top: 24px;
            overflow: hidden;
            border-left: 4px solid #1769aa;
            border-radius: 6px;
            background: #fff;
            box-shadow: 0 10px 24px rgba(34, 54, 74, 0.08);
        }}
        .CabecalhoResultadoFinanceiro {{ padding: 18px 22px 12px; }}
        .CabecalhoResultadoFinanceiro h2 {{ margin: 0; font-size: 20px; }}
        .TabelaResultadoFinanceiro {{ overflow-x: auto; }}
        .TabelaResultadoFinanceiro table {{ width: 100%; border-collapse: collapse; }}
        .TabelaResultadoFinanceiro th,
        .TabelaResultadoFinanceiro td {{ padding: 12px 22px; text-align: left; }}
        .TabelaResultadoFinanceiro thead th {{
            background: #f4f8fb;
            color: #486175;
            font-size: 12px;
            text-transform: uppercase;
        }}
        .TabelaResultadoFinanceiro tbody tr + tr {{ border-top: 1px solid #dce6ed; }}
        .ValorEntrada {{ color: #1769aa; font-weight: 700; }}
        .ValorCusto {{ color: #a65b00; font-weight: 700; }}
        .ValorLucroProdutos {{ color: #087f6a; font-weight: 800; }}
        .LinhaVendaRecente {{ cursor: pointer; }}
        .LinhaVendaRecente:hover td {{ background: #f4f9fc; }}
        .BotaoDetalhesVenda {{
            width: 28px;
            height: 28px;
            margin-right: 8px;
            border: 1px solid #b9d7e8;
            border-radius: 5px;
            color: #056da8;
            background: #e8f5fc;
            font-size: 18px;
            font-weight: 700;
            line-height: 1;
            cursor: pointer;
        }}
        .BotaoDetalhesVenda:focus-visible {{ outline: 2px solid #056da8; outline-offset: 2px; }}
        .LinhaDetalhesVenda td {{ padding: 0; background: #f7fafc; }}
        .ConteudoDetalhesVenda {{ padding: 16px 22px 18px 58px; }}
        .ConteudoDetalhesVenda > strong {{ color: #43576a; font-size: 13px; }}
        .ListaItensVenda {{ margin: 10px 0 0; padding: 0; list-style: none; }}
        .ListaItensVenda li {{
            display: grid;
            grid-template-columns: minmax(180px, 1fr) minmax(210px, auto) 110px;
            gap: 18px;
            padding: 9px 0;
            border-top: 1px solid #dce6ed;
            align-items: center;
        }}
        .ListaItensVenda span {{ color: #617181; }}
        .ListaItensVenda b {{ text-align: right; color: #26313d; }}
        .VendaSemItens {{ margin: 10px 0 0; color: #667482; }}
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
                <strong>Faturamento hoje</strong>
                <span>R$ {FormatarValorMoeda(ResumoFinanceiro["TotalVendidoHoje"])}</span>
            </div>
            <div class="IconeIndicador" aria-hidden="true">D</div>
        </article>

        <article class="CardIndicador CardIndicadorFinanceiro" style="--CorDestaque: #14866d;">
            <div>
                <strong>Faturamento no mês</strong>
                <span>R$ {FormatarValorMoeda(ResumoFinanceiro["TotalVendidoMes"])}</span>
            </div>
            <div class="IconeIndicador" aria-hidden="true">M</div>
        </article>

        <article class="CardIndicador CardIndicadorFinanceiro" style="--CorDestaque: #536a7a;">
            <div>
                <strong>Faturamento no ano</strong>
                <span>R$ {FormatarValorMoeda(ResumoFinanceiro["TotalVendidoAno"])}</span>
            </div>
            <div class="IconeIndicador" aria-hidden="true">A</div>
        </article>
    </section>

    {ResultadoFinanceiro}

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
