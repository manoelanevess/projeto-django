"""Componentes da página de continhas dos clientes."""
from html import escape

from django.http import HttpResponse
from django.middleware.csrf import get_token as ObterTokenCsrf
from django.shortcuts import redirect as Redirecionar
from django.utils import timezone
from django.views.decorators.http import require_POST as ExigirPost

from componentes.LayoutBase import RenderizarLayoutBase
from features.produtos.LogicaProduto import FormatarValorMoeda

from .LogicaContaCliente import (
    BuscarContinhasClientes,
    CalcularSaldoConta,
    RegistrarPagamentoContaCliente,
)


ChaveMensagemContaCliente = "MensagemContaCliente"


def DefinirMensagemContaCliente(Request, Texto, Tipo="sucesso"):
    Request.session[ChaveMensagemContaCliente] = {
        "Texto": Texto,
        "Tipo": Tipo,
    }


def ConsumirMensagemContaCliente(Request):
    return Request.session.pop(ChaveMensagemContaCliente, None)


def RenderizarMensagemContaCliente(Mensagem):
    if not Mensagem:
        return ""

    ClasseMensagem = "Erro" if Mensagem["Tipo"] == "erro" else "Sucesso"
    return (
        f'<div class="MensagemOperacao {ClasseMensagem}" role="status">'
        f'{escape(Mensagem["Texto"])}</div>'
    )


def RenderizarLancamentosConta(Conta):
    Lancamentos = list(Conta.Lancamentos.all()[:5])

    if not Lancamentos:
        return '<p class="TextoApoio">Nenhum lançamento registrado.</p>'

    Linhas = []

    for Lancamento in Lancamentos:
        Sinal = "+" if Lancamento.Tipo == Lancamento.COMPRA else "-"
        Venda = (
            f'<a href="/vendas/historico?busca={Lancamento.Venda.id}">'
            f"Venda #{Lancamento.Venda.id}</a>"
            if Lancamento.Venda_id
            else escape(Lancamento.Descricao or "Pagamento")
        )
        Linhas.append(
            f"""
            <tr>
                <td>{timezone.localtime(Lancamento.CriadoEm).strftime('%d/%m/%Y %H:%M')}</td>
                <td>{escape(Lancamento.get_Tipo_display())}</td>
                <td>{Venda}</td>
                <td>{Sinal} R$ {FormatarValorMoeda(Lancamento.Valor)}</td>
            </tr>
            """
        )

    return f"""
    <div class="TabelaLancamentosConta">
        <table>
            <thead>
                <tr>
                    <th>Data</th>
                    <th>Tipo</th>
                    <th>Origem</th>
                    <th>Valor</th>
                </tr>
            </thead>
            <tbody>{''.join(Linhas)}</tbody>
        </table>
    </div>
    """


def RenderizarContinhas(Contas):
    Cartoes = []

    for Conta in Contas:
        Saldo = CalcularSaldoConta(Conta)
        ClasseSaldo = "SaldoAberto" if Saldo > 0 else "SaldoQuitado"
        Cartoes.append(
            f"""
            <article class="ContaCliente">
                <div class="CabecalhoContaCliente">
                    <div>
                        <h2>{escape(Conta.NomeCliente)}</h2>
                        <span>{'Ativa' if Conta.Ativa else 'Inativa'}</span>
                    </div>
                    <strong class="{ClasseSaldo}">R$ {FormatarValorMoeda(Saldo)}</strong>
                </div>

                {RenderizarLancamentosConta(Conta)}

                <form class="FormularioPagamentoConta" method="post" action="/continhas/pagamento">
                    <input type="hidden" name="csrfmiddlewaretoken" value="__TOKEN_CSRF__">
                    <input type="hidden" name="conta" value="{Conta.id}">
                    <label>
                        Valor recebido
                        <input
                            class="CampoFormulario"
                            name="valor"
                            type="text"
                            inputmode="decimal"
                            placeholder="R$ 0,00"
                            required
                        >
                    </label>
                    <label>
                        Observação
                        <input
                            class="CampoFormulario"
                            name="descricao"
                            type="text"
                            maxlength="140"
                            placeholder="Pagamento recebido"
                        >
                    </label>
                    <button class="BotaoPrimario" type="submit">Registrar pagamento</button>
                </form>
            </article>
            """
        )

    if not Cartoes:
        return """
        <section class="EstadoVazio">
            <h2>Nenhuma continha encontrada</h2>
            <p>As compras lançadas na conta do cliente aparecerão aqui.</p>
            <a class="BotaoPrimario" href="/">Abrir atendimento</a>
        </section>
        """

    ConteudoCartoes = "".join(Cartoes)
    return f'<section class="ListaContinhas">{ConteudoCartoes}</section>'


def ComponenteContinhasClientes(Request):
    Busca = Request.GET.get("busca", "").strip()
    Contas = BuscarContinhasClientes(Request.user, Busca)
    Mensagem = ConsumirMensagemContaCliente(Request)
    ConteudoContinhas = RenderizarContinhas(Contas).replace(
        "__TOKEN_CSRF__",
        escape(ObterTokenCsrf(Request)),
    )

    ConteudoPrincipal = f"""
    <style>
        .CabecalhoContinhas {{
            margin-bottom: 18px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 16px;
        }}
        .CabecalhoContinhas h1 {{ margin: 0; }}
        .ListaContinhas {{ display: grid; gap: 16px; }}
        .ContaCliente {{
            padding: 18px;
            border: 1px solid #d6e0e6;
            border-radius: 6px;
            background: #ffffff;
            box-shadow: 0 10px 22px rgba(31, 49, 61, 0.08);
        }}
        .CabecalhoContaCliente {{
            margin-bottom: 14px;
            display: flex;
            align-items: baseline;
            justify-content: space-between;
            gap: 16px;
        }}
        .CabecalhoContaCliente h2 {{ margin: 0 0 4px; font-size: 20px; }}
        .CabecalhoContaCliente span,
        .TextoApoio {{ color: #667482; font-size: 13px; }}
        .CabecalhoContaCliente strong {{ font-size: 24px; }}
        .SaldoAberto {{ color: #a65b00; }}
        .SaldoQuitado {{ color: #14866d; }}
        .TabelaLancamentosConta {{ overflow-x: auto; }}
        .TabelaLancamentosConta table {{
            box-shadow: none;
            border: 1px solid #d9e2ec;
        }}
        .TabelaLancamentosConta td:last-child {{ font-weight: 700; }}
        .FormularioPagamentoConta {{
            margin-top: 14px;
            display: grid;
            grid-template-columns: minmax(140px, 190px) minmax(220px, 1fr) auto;
            gap: 10px;
            align-items: end;
        }}
        .FormularioPagamentoConta label {{
            display: grid;
            gap: 6px;
            color: #52616f;
            font-size: 12px;
            font-weight: 700;
        }}
        .MensagemOperacao {{
            margin-bottom: 18px;
            padding: 12px 14px;
            border-left: 4px solid;
            border-radius: 4px;
        }}
        .MensagemOperacao.Sucesso {{ border-color: #14866d; color: #0c614f; background: #e7f7f2; }}
        .MensagemOperacao.Erro {{ border-color: #c53b32; color: #8b241e; background: #fff0ef; }}
        @media (max-width: 760px) {{
            .CabecalhoContinhas {{ align-items: stretch; flex-direction: column; }}
            .FormularioPagamentoConta {{ grid-template-columns: 1fr; }}
        }}
    </style>

    <div class="CabecalhoContinhas">
        <h1>Continhas dos clientes</h1>
        <a class="BotaoSecundario" href="/">Abrir atendimento</a>
    </div>

    <form class="BarraFiltros" method="get" action="/continhas" id="FormularioBuscaContinhas">
        <input
            id="BuscaContaCliente"
            class="CampoFormulario"
            type="search"
            name="busca"
            value="{escape(Busca)}"
            placeholder="Nome do cliente"
            aria-label="Pesquisar continhas por cliente"
            autocomplete="off"
        >
    </form>

    {RenderizarMensagemContaCliente(Mensagem)}
    <p class="MensagemOperacao Erro" id="ErroBuscaContinhas" role="status" hidden>
        Não foi possível pesquisar agora. Tente novamente.
    </p>
    <div id="ResultadosContinhas" aria-live="polite">
        {ConteudoContinhas}
    </div>

    <script>
        (() => {{
            const Formulario = document.getElementById("FormularioBuscaContinhas");
            const CampoBusca = document.getElementById("BuscaContaCliente");
            const AreaResultados = document.getElementById("ResultadosContinhas");
            const ErroBusca = document.getElementById("ErroBuscaContinhas");
            let TemporizadorBusca;
            let ControleBusca;

            const AtualizarBuscaNaUrl = (Busca) => {{
                const Endereco = new URL(window.location.href);
                if (Busca) Endereco.searchParams.set("busca", Busca);
                else Endereco.searchParams.delete("busca");
                window.history.replaceState(null, "", Endereco.toString());
                return Endereco;
            }};

            const PesquisarContinhas = async () => {{
                if (ControleBusca) ControleBusca.abort();
                ControleBusca = new AbortController();
                const ControleAtual = ControleBusca;
                const Endereco = AtualizarBuscaNaUrl(CampoBusca.value.trim());
                AreaResultados.setAttribute("aria-busy", "true");
                ErroBusca.hidden = true;

                try {{
                    const Resposta = await fetch(Endereco, {{
                        credentials: "same-origin",
                        signal: ControleAtual.signal,
                    }});
                    if (!Resposta.ok) throw new Error("Falha ao pesquisar continhas");

                    const Documento = new DOMParser().parseFromString(
                        await Resposta.text(),
                        "text/html",
                    );
                    const NovosResultados = Documento.getElementById("ResultadosContinhas");
                    if (!NovosResultados) throw new Error("Resultados indisponíveis");
                    if (ControleBusca !== ControleAtual) return;
                    AreaResultados.replaceChildren(...NovosResultados.childNodes);
                }} catch (Erro) {{
                    if (Erro.name !== "AbortError" && ControleBusca === ControleAtual) {{
                        ErroBusca.hidden = false;
                    }}
                }} finally {{
                    if (ControleBusca === ControleAtual) {{
                        AreaResultados.removeAttribute("aria-busy");
                    }}
                }}
            }};

            CampoBusca.addEventListener("input", () => {{
                clearTimeout(TemporizadorBusca);
                if (ControleBusca) ControleBusca.abort();
                AtualizarBuscaNaUrl(CampoBusca.value.trim());
                TemporizadorBusca = window.setTimeout(PesquisarContinhas, 160);
            }});

            Formulario.addEventListener("submit", (Evento) => {{
                Evento.preventDefault();
                clearTimeout(TemporizadorBusca);
                PesquisarContinhas();
            }});
        }})();
    </script>
    """

    return HttpResponse(
        RenderizarLayoutBase(
            "Continhas dos clientes",
            ConteudoPrincipal,
            RotaAtiva="continhas",
        )
    )


@ExigirPost
def ComponenteRegistrarPagamentoContaCliente(Request):
    try:
        Conta = RegistrarPagamentoContaCliente(
            Request.user,
            Request.POST.get("conta"),
            Request.POST.get("valor"),
            Request.POST.get("descricao", ""),
        )
        DefinirMensagemContaCliente(
            Request,
            f"Pagamento registrado para {Conta.NomeCliente}.",
        )
    except ValueError as Erro:
        DefinirMensagemContaCliente(Request, str(Erro), Tipo="erro")

    return Redirecionar("/continhas")
