"""Componentes da página de histórico de vendas."""
from html import escape

from django.db.models import Q
from django.http import HttpResponse
from django.utils import timezone

from componentes.LayoutBase import RenderizarLayoutBase
from features.produtos.LogicaProduto import FormatarQuantidade, FormatarValorMoeda

from .LogicaVenda import ConsolidarVendasDeMesesAnteriores
from .models import RegistroVendaAntiga, Venda


RotulosPagamento = dict(Venda.OpcoesFormaPagamento)


def ObterUnidadeResumidaItem(UnidadeVenda):
    return {
        "quilograma": "kg",
        "metro": "m",
        "valor_fixo": "item",
    }.get(UnidadeVenda, "un")


def BuscarVendasAtuais(Proprietario, Busca=""):
    Vendas = Venda.objects.filter(Proprietario=Proprietario).prefetch_related("Itens")

    if Busca:
        Filtro = Q(NomeCliente__icontains=Busca) | Q(Itens__NomeProduto__icontains=Busca)

        if Busca.isdigit():
            Filtro |= Q(id=int(Busca))

        Vendas = Vendas.filter(Filtro).distinct()

    return Vendas.order_by("-CriadaEm")[:100]


def BuscarRegistrosVendasAntigas(Proprietario, Busca=""):
    Registros = RegistroVendaAntiga.objects.filter(
        Proprietario=Proprietario
    ).prefetch_related("Itens")

    if Busca:
        Filtro = Q(NomeCliente__icontains=Busca) | Q(Itens__NomeProduto__icontains=Busca)

        if Busca.isdigit():
            Filtro |= Q(VendaOriginalId=int(Busca))

        Registros = Registros.filter(Filtro).distinct()

    return Registros.order_by("-CriadaEm")[:100]


def RenderizarItensHistorico(Itens):
    Linhas = []

    for ItemVenda in Itens:
        Unidade = ObterUnidadeResumidaItem(ItemVenda.UnidadeVenda)
        Linhas.append(
            f"""
            <li>
                <strong>{escape(ItemVenda.NomeProduto)}</strong>
                <span>{FormatarQuantidade(ItemVenda.Quantidade)} {Unidade} × R$ {FormatarValorMoeda(ItemVenda.PrecoUnitario)}</span>
                <b>R$ {FormatarValorMoeda(ItemVenda.Subtotal)}</b>
            </li>
            """
        )

    if not Linhas:
        return '<p class="TextoApoio">Nenhum item registrado.</p>'

    return f'<ul class="ListaItensHistorico">{"".join(Linhas)}</ul>'


def RenderizarTabelaHistorico(VendasAtuais, RegistrosAntigos):
    Linhas = []

    for VendaAtual in VendasAtuais:
        IdDetalhes = f"VendaAtual{VendaAtual.id}"
        Linhas.append(
            f"""
            <tr class="LinhaHistoricoVenda" data-detalhe-venda="{IdDetalhes}">
                <td>
                    <button class="BotaoDetalhesVenda" type="button" aria-expanded="false" aria-controls="{IdDetalhes}">
                        <span aria-hidden="true">+</span>
                    </button>
                    <strong>#{VendaAtual.id}</strong>
                </td>
                <td>{timezone.localtime(VendaAtual.CriadaEm).strftime('%d/%m/%Y %H:%M')}</td>
                <td>{escape(VendaAtual.NomeCliente or 'Não identificado')}</td>
                <td>{escape(VendaAtual.get_FormaPagamento_display())}</td>
                <td>R$ {FormatarValorMoeda(VendaAtual.Total)}</td>
                <td>Atual</td>
            </tr>
            <tr class="LinhaDetalhesVenda" id="{IdDetalhes}" hidden>
                <td colspan="6">
                    <div class="ConteudoDetalhesVenda">
                        <strong>Itens da venda</strong>
                        {RenderizarItensHistorico(VendaAtual.Itens.all())}
                    </div>
                </td>
            </tr>
            """
        )

    for RegistroAntigo in RegistrosAntigos:
        IdDetalhes = f"VendaAntiga{RegistroAntigo.id}"
        Linhas.append(
            f"""
            <tr class="LinhaHistoricoVenda" data-detalhe-venda="{IdDetalhes}">
                <td>
                    <button class="BotaoDetalhesVenda" type="button" aria-expanded="false" aria-controls="{IdDetalhes}">
                        <span aria-hidden="true">+</span>
                    </button>
                    <strong>#{RegistroAntigo.VendaOriginalId}</strong>
                </td>
                <td>{timezone.localtime(RegistroAntigo.CriadaEm).strftime('%d/%m/%Y %H:%M')}</td>
                <td>{escape(RegistroAntigo.NomeCliente or 'Não identificado')}</td>
                <td>{escape(RotulosPagamento.get(RegistroAntigo.FormaPagamento, RegistroAntigo.FormaPagamento))}</td>
                <td>R$ {FormatarValorMoeda(RegistroAntigo.Total)}</td>
                <td>Arquivada</td>
            </tr>
            <tr class="LinhaDetalhesVenda" id="{IdDetalhes}" hidden>
                <td colspan="6">
                    <div class="ConteudoDetalhesVenda">
                        <strong>Itens preservados</strong>
                        {RenderizarItensHistorico(RegistroAntigo.Itens.all())}
                    </div>
                </td>
            </tr>
            """
        )

    if not Linhas:
        return """
        <section class="EstadoVazio">
            <h2>Nenhuma venda encontrada</h2>
            <p>As vendas concluídas e arquivadas aparecerão aqui.</p>
            <a class="BotaoPrimario" href="/">Abrir atendimento</a>
        </section>
        """

    return f"""
    <section class="PainelTabela TabelaHistoricoVendas" aria-label="Histórico de vendas">
        <table>
            <thead>
                <tr>
                    <th>Venda</th>
                    <th>Data</th>
                    <th>Cliente</th>
                    <th>Pagamento</th>
                    <th>Total</th>
                    <th>Situação</th>
                </tr>
            </thead>
            <tbody>{''.join(Linhas)}</tbody>
        </table>
    </section>
    <script>
        (() => {{
            document.querySelectorAll("[data-detalhe-venda]").forEach((LinhaVenda) => {{
                LinhaVenda.addEventListener("click", () => {{
                    const DetalhesVenda = document.getElementById(LinhaVenda.dataset.detalheVenda);
                    const BotaoDetalhes = LinhaVenda.querySelector(".BotaoDetalhesVenda");
                    const VaiAbrir = DetalhesVenda.hidden;
                    DetalhesVenda.hidden = !VaiAbrir;
                    BotaoDetalhes.setAttribute("aria-expanded", String(VaiAbrir));
                    BotaoDetalhes.querySelector("span").textContent = VaiAbrir ? "-" : "+";
                }});
            }});
        }})();
    </script>
    """


def ComponenteHistoricoVendas(Request):
    ConsolidarVendasDeMesesAnteriores()
    Busca = Request.GET.get("busca", "").strip()
    VendasAtuais = BuscarVendasAtuais(Request.user, Busca)
    RegistrosAntigos = BuscarRegistrosVendasAntigas(Request.user, Busca)
    TabelaHistorico = RenderizarTabelaHistorico(VendasAtuais, RegistrosAntigos)

    ConteudoPrincipal = f"""
    <style>
        .CabecalhoHistorico {{
            margin-bottom: 18px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 16px;
        }}
        .CabecalhoHistorico h1 {{ margin: 0; }}
        .TabelaHistoricoVendas {{ overflow-x: auto; }}
        .TabelaHistoricoVendas table {{ min-width: 860px; }}
        .LinhaHistoricoVenda {{ cursor: pointer; }}
        .LinhaHistoricoVenda:hover td {{ background: #f4f9fc; }}
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
        .LinhaDetalhesVenda td {{ padding: 0; background: #f7fafc; }}
        .ConteudoDetalhesVenda {{ padding: 16px 22px 18px 58px; }}
        .ConteudoDetalhesVenda > strong {{ color: #43576a; font-size: 13px; }}
        .ListaItensHistorico {{
            margin: 10px 0 0;
            padding: 0;
            list-style: none;
        }}
        .ListaItensHistorico li {{
            display: grid;
            grid-template-columns: minmax(180px, 1fr) minmax(210px, auto) 110px;
            gap: 18px;
            padding: 9px 0;
            border-top: 1px solid #dce6ed;
            align-items: center;
        }}
        .ListaItensHistorico span,
        .TextoApoio {{ color: #667482; }}
        .ListaItensHistorico b {{ text-align: right; color: #26313d; }}
        @media (max-width: 760px) {{
            .CabecalhoHistorico {{ align-items: stretch; flex-direction: column; }}
        }}
    </style>

    <div class="CabecalhoHistorico">
        <h1>Histórico de vendas</h1>
        <a class="BotaoSecundario" href="/">Abrir atendimento</a>
    </div>

    <form class="BarraFiltros" method="get" action="/vendas/historico">
        <input
            class="CampoFormulario"
            type="search"
            name="busca"
            value="{escape(Busca)}"
            placeholder="Cliente, produto ou número da venda"
            aria-label="Pesquisar no histórico de vendas"
        >
        <button class="BotaoPrimario" type="submit">Pesquisar</button>
    </form>

    {TabelaHistorico}
    """

    return HttpResponse(
        RenderizarLayoutBase(
            "Histórico de vendas",
            ConteudoPrincipal,
            RotaAtiva="historico-vendas",
        )
    )
