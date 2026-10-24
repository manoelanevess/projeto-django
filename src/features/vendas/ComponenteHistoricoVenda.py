"""Componentes da página de histórico de vendas."""
from html import escape

from django.http import HttpResponse
from django.utils import timezone

from componentes.LayoutBase import RenderizarLayoutBase
from componentes.BuscaIncremental import ObterScriptBuscaIncremental
from features.produtos.LogicaProduto import FormatarQuantidade, FormatarValorMoeda

from .ApiVenda import BuscarHistoricoVendas
from .ComponentePagamento import RenderizarDivisaoPagamento
from .FormularioHistoricoVenda import FormularioHistoricoVenda, ParametrosFiltrosHistorico
from .LogicaVenda import ConsolidarVendasDeMesesAnteriores
from .models import Venda


RotulosPagamento = dict(Venda.OpcoesFormaPagamento)


def ObterUnidadeResumidaItem(UnidadeVenda):
    return {
        "quilograma": "kg",
        "metro": "m",
        "valor_fixo": "item",
    }.get(UnidadeVenda, "un")


def RenderizarFiltrosHistorico(Formulario):
    Campos = []

    for NomeCampo, Parametro in ParametrosFiltrosHistorico.items():
        Campo = Formulario[NomeCampo]
        IdCampo = f"FiltroVenda{NomeCampo}"
        Atributos = {"id": IdCampo}

        if Campo.errors:
            Atributos.update({"aria-invalid": "true", "aria-describedby": f"{IdCampo}Erro"})

        Entrada = Campo.field.widget.render(Parametro, Campo.value(), attrs=Atributos)
        Erros = " ".join(str(Erro) for Erro in Campo.errors)
        MensagemErro = f'<small class="ErroFiltroVenda" id="{IdCampo}Erro"{"" if Erros else " hidden"}>{escape(Erros)}</small>'
        Campos.append(f"""
            <div class="FiltroHistorico Filtro{NomeCampo}">
                <label for="{IdCampo}">{escape(Campo.label)}</label>
                {Entrada}
                {MensagemErro}
            </div>
        """)

    return "".join(Campos)


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


def RenderizarTabelaHistorico(VendasAtuais, RegistrosAntigos, FiltrosAtivos=False):
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
                        {RenderizarDivisaoPagamento(VendaAtual)}
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
                        {RenderizarDivisaoPagamento(RegistroAntigo)}
                        <strong>Itens preservados</strong>
                        {RenderizarItensHistorico(RegistroAntigo.Itens.all())}
                    </div>
                </td>
            </tr>
            """
        )

    if not Linhas:
        Mensagem = (
            "Nenhuma venda corresponde aos filtros selecionados."
            if FiltrosAtivos else "As vendas concluídas e arquivadas aparecerão aqui."
        )
        Acao = (
            '<a class="BotaoSecundario" href="/vendas/historico">Limpar filtros</a>'
            if FiltrosAtivos else '<a class="BotaoPrimario" href="/">Abrir atendimento</a>'
        )
        return f"""
        <section class="EstadoVazio">
            <h2>Nenhuma venda encontrada</h2>
            <p>{Mensagem}</p>
            {Acao}
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
    """


def ComponenteHistoricoVendas(Request):
    ConsolidarVendasDeMesesAnteriores()
    Formulario = FormularioHistoricoVenda({
        NomeCampo: Request.GET.get(Parametro, "").strip()
        for NomeCampo, Parametro in ParametrosFiltrosHistorico.items()
    })

    if Formulario.is_valid():
        VendasAtuais, RegistrosAntigos = BuscarHistoricoVendas(
            Request.user, Formulario.cleaned_data
        )
        TabelaHistorico = RenderizarTabelaHistorico(
            VendasAtuais, RegistrosAntigos, any(Formulario.cleaned_data.values())
        )
    else:
        TabelaHistorico = '<p class="AvisoFiltrosVenda" role="status">Corrija os filtros para consultar as vendas.</p>'

    CamposFiltros = RenderizarFiltrosHistorico(Formulario)

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
        .BarraFiltrosHistorico {{
            display: grid;
            grid-template-columns: minmax(0, 1fr) minmax(0, 1fr) repeat(2, minmax(150px, 0.7fr));
            align-items: start;
            gap: 14px;
        }}
        .FiltroHistorico {{ display: grid; gap: 6px; min-width: 0; }}
        .FiltroHistorico label {{ font-size: 13px; font-weight: 700; color: #43576a; }}
        .FiltroBusca {{ grid-column: span 2; }}
        .BarraFiltrosHistorico .CampoFormulario {{ width: 100%; min-width: 0; }}
        .AcoesFiltrosHistorico {{
            grid-column: span 2;
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            padding-top: 21px;
        }}
        .ErroFiltroVenda {{ color: #b42318; line-height: 1.4; }}
        .AvisoFiltrosVenda {{ color: #b42318; }}
        .TabelaHistoricoVendas {{ overflow-x: auto; max-width: 100%; }}
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
        @media (max-width: 960px) {{
            .BarraFiltrosHistorico {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
            .AcoesFiltrosHistorico {{ padding-top: 0; }}
        }}
        @media (max-width: 760px) {{
            .CabecalhoHistorico {{ align-items: stretch; flex-direction: column; }}
        }}
        @media (max-width: 420px) {{
            .BarraFiltrosHistorico {{ grid-template-columns: minmax(0, 1fr); }}
            .FiltroBusca, .AcoesFiltrosHistorico {{ grid-column: auto; }}
        }}
    </style>

    <div class="CabecalhoHistorico">
        <h1>Histórico de vendas</h1>
        <a class="BotaoSecundario" href="/">Abrir atendimento</a>
    </div>

    <form class="BarraFiltros BarraFiltrosHistorico" id="FormularioBuscaVendas" method="get" action="/vendas/historico">
        {CamposFiltros}
        <div class="AcoesFiltrosHistorico">
            <button class="BotaoPrimario" type="submit">Filtrar</button>
            <a class="BotaoSecundario" href="/vendas/historico">Limpar filtros</a>
        </div>
    </form>

    <p id="ErroBuscaVendas" class="AvisoFiltrosVenda" role="status" hidden>Não foi possível pesquisar agora. Tente novamente.</p>
    <div id="ResultadosVendas" aria-live="polite">
        {TabelaHistorico}
    </div>
    <script>
        (() => {{
            const Formulario = document.getElementById("FormularioBuscaVendas");
            document.getElementById("ResultadosVendas").addEventListener("click", (Evento) => {{
                const LinhaVenda = Evento.target.closest("[data-detalhe-venda]");
                if (!LinhaVenda) return;
                const DetalhesVenda = document.getElementById(LinhaVenda.dataset.detalheVenda);
                const BotaoDetalhes = LinhaVenda.querySelector(".BotaoDetalhesVenda");
                const VaiAbrir = DetalhesVenda.hidden;
                DetalhesVenda.hidden = !VaiAbrir;
                BotaoDetalhes.setAttribute("aria-expanded", String(VaiAbrir));
                BotaoDetalhes.querySelector("span").textContent = VaiAbrir ? "-" : "+";
            }});
            Formulario.addEventListener("busca-incremental-atualizada", (Evento) => {{
                const Documento = Evento.detail.Documento;
                Formulario.querySelectorAll("input, select").forEach((Campo) => {{
                    const NovoCampo = Documento.getElementById(Campo.id);
                    const Erro = document.getElementById(`${{Campo.id}}Erro`);
                    const NovoErro = Documento.getElementById(`${{Campo.id}}Erro`);
                    if (!NovoCampo || !Erro || !NovoErro) return;
                    Erro.textContent = NovoErro.textContent;
                    Erro.hidden = NovoErro.hidden;
                    ["aria-invalid", "aria-describedby"].forEach((Atributo) => {{
                        if (NovoCampo.hasAttribute(Atributo)) Campo.setAttribute(Atributo, NovoCampo.getAttribute(Atributo));
                        else Campo.removeAttribute(Atributo);
                    }});
                }});
            }});
        }})();
    </script>
    """

    return HttpResponse(
        RenderizarLayoutBase(
            "Histórico de vendas",
            ConteudoPrincipal + ObterScriptBuscaIncremental(
                "FormularioBuscaVendas", "FiltroVendaBusca", "ResultadosVendas", "ErroBuscaVendas",
            ),
            RotaAtiva="historico-vendas",
            Request=Request,
        )
    )
