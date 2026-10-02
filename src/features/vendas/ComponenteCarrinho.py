"""Componentes do fluxo de atendimento e carrinho de compras."""
from html import escape
from urllib.parse import urlencode

from django.http import HttpResponse
from django.middleware.csrf import get_token as ObterTokenCsrf
from django.shortcuts import redirect as Redirecionar
from django.urls import reverse as ObterRota
from django.views.decorators.http import require_POST as ExigirPost

from componentes.LayoutBase import RenderizarLayoutBase
from features.produtos.ApiProduto import BuscarProdutosParaVenda
from features.produtos.LogicaProduto import FormatarQuantidade, FormatarValorMoeda

from .LogicaCarrinho import (
    AdicionarProdutoAoCarrinho,
    ConcluirVenda,
    DefinirNomeCarrinho,
    LimparCarrinho,
    MontarResumosCarrinhos,
    RemoverProdutoDoCarrinho,
    ValidarNumeroCarrinho,
)


ChaveMensagemCarrinho = "MensagemCarrinho"


def ObterNumeroCarrinhoSeguro(Valor):
    try:
        return ValidarNumeroCarrinho(Valor)
    except ValueError:
        return "1"


def ObterNumeroCarrinhoDaAcao(Request):
    try:
        return ValidarNumeroCarrinho(Request.POST.get("carrinho"))
    except ValueError as Erro:
        DefinirMensagem(Request, str(Erro), Tipo="erro")
        return None


def DefinirMensagem(Request, Texto, Tipo="sucesso"):
    Request.session[ChaveMensagemCarrinho] = {
        "Texto": Texto,
        "Tipo": Tipo,
    }


def ConsumirMensagem(Request):
    return Request.session.pop(ChaveMensagemCarrinho, None)


def RedirecionarParaCarrinho(NumeroCarrinho, Busca=""):
    Parametros = {"carrinho": NumeroCarrinho}

    if Busca:
        Parametros["busca"] = Busca

    return Redirecionar(f"{ObterRota('Carrinho')}?{urlencode(Parametros)}")


def RedirecionarAposAcao(Request, NumeroCarrinho, Busca=""):
    if Request.POST.get("retorno") != "pagina-principal":
        return RedirecionarParaCarrinho(NumeroCarrinho, Busca)

    CarrinhosAbertos = []

    for NumeroInformado in Request.POST.get("carrinhos_abertos", "").split(","):
        try:
            NumeroValido = ValidarNumeroCarrinho(NumeroInformado)
        except ValueError:
            continue

        if NumeroValido not in CarrinhosAbertos:
            CarrinhosAbertos.append(NumeroValido)

    if NumeroCarrinho not in CarrinhosAbertos:
        CarrinhosAbertos.append(NumeroCarrinho)

    Parametros = {
        "carrinho": NumeroCarrinho,
        "carrinhos_abertos": ",".join(CarrinhosAbertos),
    }

    if Busca:
        Parametros["busca_carrinho"] = Busca

    return Redirecionar(f"/?{urlencode(Parametros)}")


def RenderizarAbasCarrinhos(ResumosCarrinhos, NumeroSelecionado):
    return "".join(
        f"""
        <a
            class="AbaCarrinho{' Ativa' if Resumo['Numero'] == NumeroSelecionado else ''}"
            href="/carrinho?carrinho={Resumo['Numero']}"
            {'aria-current="page"' if Resumo['Numero'] == NumeroSelecionado else ''}
        >
            <span>{escape(Resumo['Nome'])}</span>
            <strong>{Resumo['QuantidadeProdutos']}</strong>
        </a>
        """
        for Resumo in ResumosCarrinhos
    )


def RenderizarResultadosBusca(ProdutosEncontrados, TokenCsrf, NumeroCarrinho, Busca):
    if not Busca:
        return """
        <section class="EstadoBuscaVenda">
            <h2>Pesquisar produtos</h2>
            <p>Use o produto, a categoria, a marca ou o fornecedor na pesquisa.</p>
        </section>
        """

    if not ProdutosEncontrados:
        return """
        <section class="EstadoBuscaVenda">
            <h2>Nenhum produto disponível</h2>
            <p>Confira o nome pesquisado ou verifique o estoque.</p>
        </section>
        """

    CartoesProdutos = []

    for ProdutoVenda in ProdutosEncontrados:
        NomeSeguro = escape(ProdutoVenda.Nome)
        CategoriaSegura = escape(ProdutoVenda.Categoria or "Sem categoria")
        MarcaSegura = escape(ProdutoVenda.Marca or "Sem marca")
        FornecedorSeguro = escape(ProdutoVenda.Fornecedor.Nome)
        Unidade = ProdutoVenda.ObterUnidadeResumida()
        Estoque = (
            escape(ProdutoVenda.ObterDescricaoEstoque())
            if ProdutoVenda.EhControladoPorDisponibilidade()
            else f"{FormatarQuantidade(ProdutoVenda.QuantidadeEstoque)} {Unidade}"
        )
        Preco = FormatarValorMoeda(ProdutoVenda.PrecoVenda)
        Passo = ProdutoVenda.ObterPassoVenda()
        QuantidadeInicial = ProdutoVenda.ObterQuantidadeInicialVenda()
        RotuloQuantidade = ProdutoVenda.ObterRotuloQuantidadeVenda()
        AtributoMaximo = (
            f'max="{ProdutoVenda.QuantidadeEstoque}"'
            if ProdutoVenda.ControlaQuantidadeEstoque()
            else ""
        )

        CartoesProdutos.append(
            f"""
            <article class="ProdutoResultado">
                <div class="DadosProdutoResultado">
                    <strong>{NomeSeguro}</strong>
                    <span>{CategoriaSegura} · {MarcaSegura}</span>
                    <small>{FornecedorSeguro} · R$ {Preco} / {Unidade} · Estoque: {Estoque}</small>
                </div>
                <form class="FormularioAdicionar" method="post" action="/carrinho/adicionar">
                    <input type="hidden" name="csrfmiddlewaretoken" value="{TokenCsrf}">
                    <input type="hidden" name="carrinho" value="{NumeroCarrinho}">
                    <input type="hidden" name="produto" value="{ProdutoVenda.id}">
                    <input type="hidden" name="busca" value="{escape(Busca)}">
                    <label for="Quantidade-{ProdutoVenda.id}">{RotuloQuantidade}</label>
                    <input
                        id="Quantidade-{ProdutoVenda.id}"
                        class="CampoQuantidade"
                        type="number"
                        name="quantidade"
                        min="{Passo}"
                        {AtributoMaximo}
                        step="{Passo}"
                        value="{QuantidadeInicial}"
                        required
                    >
                    <button class="BotaoPrimario" type="submit">Adicionar</button>
                </form>
            </article>
            """
        )

    return f'<section class="ListaResultadosVenda">{"".join(CartoesProdutos)}</section>'


def RenderizarItensCarrinho(ResumoCarrinho, TokenCsrf, NumeroCarrinho):
    if not ResumoCarrinho["Itens"]:
        return """
        <div class="CarrinhoVazio">
            <strong>Carrinho vazio</strong>
            <span>Pesquise um produto para iniciar o atendimento.</span>
        </div>
        """

    Linhas = []

    for Item in ResumoCarrinho["Itens"]:
        ProdutoVenda = Item["Produto"]
        Linhas.append(
            f"""
            <tr>
                <td>
                    <strong>{escape(ProdutoVenda.Nome)}</strong>
                    <small>{Item['QuantidadeFormatada']} {Item['Unidade']} × R$ {Item['PrecoFormatado']}</small>
                </td>
                <td>R$ {Item['SubtotalFormatado']}</td>
                <td class="ColunaAcao">
                    <form method="post" action="/carrinho/remover">
                        <input type="hidden" name="csrfmiddlewaretoken" value="{TokenCsrf}">
                        <input type="hidden" name="carrinho" value="{NumeroCarrinho}">
                        <input type="hidden" name="produto" value="{ProdutoVenda.id}">
                        <button class="BotaoRemover" type="submit" aria-label="Remover {escape(ProdutoVenda.Nome)}">×</button>
                    </form>
                </td>
            </tr>
            """
        )

    return f"""
    <div class="TabelaCarrinho">
        <table>
            <thead>
                <tr>
                    <th>Produto</th>
                    <th>Subtotal</th>
                    <th><span class="SomenteLeitorTela">Ação</span></th>
                </tr>
            </thead>
            <tbody>{''.join(Linhas)}</tbody>
        </table>
    </div>
    """


def RenderizarPagamento(ResumoCarrinho, TokenCsrf, NumeroCarrinho):
    if not ResumoCarrinho["Itens"]:
        return ""

    return f"""
    <section class="PagamentoVenda" aria-labelledby="TituloPagamento">
        <h2 id="TituloPagamento">Pagamento</h2>
        <form method="post" action="/carrinho/concluir" id="FormularioPagamento">
            <input type="hidden" name="csrfmiddlewaretoken" value="{TokenCsrf}">
            <input type="hidden" name="carrinho" value="{NumeroCarrinho}">

            <fieldset class="OpcoesPagamento">
                <legend>Forma de pagamento</legend>
                <label>
                    <input type="radio" name="forma_pagamento" value="dinheiro" checked>
                    Dinheiro
                </label>
                <label>
                    <input type="radio" name="forma_pagamento" value="pix">
                    PIX
                </label>
            </fieldset>

            <div class="AreaDinheiro" id="AreaDinheiro">
                <label for="ValorRecebido">Valor recebido</label>
                <div class="CampoMoeda">
                    <span>R$</span>
                    <input
                        id="ValorRecebido"
                        name="valor_recebido"
                        type="text"
                        inputmode="decimal"
                        autocomplete="off"
                        placeholder="0,00"
                        required
                    >
                </div>
                <div class="ResultadoTroco">
                    <span>Troco</span>
                    <output id="TrocoCalculado">R$ 0,00</output>
                </div>
            </div>

            <button class="BotaoConcluir" type="submit">Concluir compra</button>
        </form>

        <form method="post" action="/carrinho/cancelar" onsubmit="return confirm('Cancelar este carrinho?');">
            <input type="hidden" name="csrfmiddlewaretoken" value="{TokenCsrf}">
            <input type="hidden" name="carrinho" value="{NumeroCarrinho}">
            <button class="BotaoCancelar" type="submit">Cancelar carrinho</button>
        </form>
    </section>
    """


def ComponenteCarrinho(Request):
    NumeroCarrinho = ObterNumeroCarrinhoSeguro(Request.GET.get("carrinho", "1"))
    Busca = Request.GET.get("busca", "").strip()
    BuscaSegura = escape(Busca)
    TokenCsrf = escape(ObterTokenCsrf(Request))
    ResumosCarrinhos = MontarResumosCarrinhos(Request)
    ResumoCarrinho = next(
        Resumo
        for Resumo in ResumosCarrinhos
        if Resumo["Numero"] == NumeroCarrinho
    )
    ProdutosEncontrados = list(BuscarProdutosParaVenda(Busca))
    Mensagem = ConsumirMensagem(Request)
    HtmlMensagem = ""

    if Mensagem:
        ClasseMensagem = "Erro" if Mensagem["Tipo"] == "erro" else "Sucesso"
        HtmlMensagem = (
            f'<div class="MensagemOperacao {ClasseMensagem}" role="status">'
            f'{escape(Mensagem["Texto"])}</div>'
        )

    AbasCarrinhos = RenderizarAbasCarrinhos(ResumosCarrinhos, NumeroCarrinho)
    ResultadosBusca = RenderizarResultadosBusca(
        ProdutosEncontrados,
        TokenCsrf,
        NumeroCarrinho,
        Busca,
    )
    ItensCarrinho = RenderizarItensCarrinho(
        ResumoCarrinho,
        TokenCsrf,
        NumeroCarrinho,
    )
    Pagamento = RenderizarPagamento(
        ResumoCarrinho,
        TokenCsrf,
        NumeroCarrinho,
    )

    ConteudoPrincipal = f"""
    <style>
        .CabecalhoCarrinho {{
            margin-bottom: 18px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 16px;
        }}

        .CabecalhoCarrinho h1 {{ margin: 0; }}

        .AbasCarrinhos {{
            margin-bottom: 24px;
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            border-bottom: 1px solid #cbd6df;
        }}

        .AbaCarrinho {{
            min-height: 52px;
            padding: 0 16px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            border-bottom: 3px solid transparent;
            color: #52616f;
            text-decoration: none;
            font-weight: 700;
        }}

        .AbaCarrinho strong {{
            min-width: 26px;
            height: 26px;
            display: grid;
            place-items: center;
            border-radius: 50%;
            color: #3f4f5f;
            background: #dce5ea;
            font-size: 12px;
        }}

        .AbaCarrinho.Ativa {{
            border-bottom-color: #0784ca;
            color: #056da8;
        }}

        .AbaCarrinho.Ativa strong {{
            color: #ffffff;
            background: #0784ca;
        }}

        .GradeVenda {{
            display: grid;
            grid-template-columns: minmax(0, 1.25fr) minmax(330px, 0.75fr);
            gap: 24px;
            align-items: start;
        }}

        .BuscaVenda {{ min-width: 0; }}

        .BuscaVenda form.BarraFiltros {{ margin-bottom: 16px; }}

        .ListaResultadosVenda {{ display: grid; gap: 10px; }}

        .ProdutoResultado {{
            padding: 16px;
            display: grid;
            grid-template-columns: minmax(0, 1fr) auto;
            align-items: end;
            gap: 18px;
            border: 1px solid #d6e0e6;
            border-radius: 6px;
            background: #ffffff;
        }}

        .DadosProdutoResultado {{ display: grid; gap: 5px; }}
        .DadosProdutoResultado strong {{ font-size: 16px; }}
        .DadosProdutoResultado span,
        .DadosProdutoResultado small {{ color: #667482; }}

        .FormularioAdicionar {{
            display: grid;
            grid-template-columns: 100px 104px;
            gap: 6px 8px;
            align-items: end;
        }}

        .FormularioAdicionar label {{
            grid-column: 1 / -1;
            color: #52616f;
            font-size: 12px;
            font-weight: 700;
        }}

        .CampoQuantidade {{
            width: 100%;
            min-height: 42px;
            padding: 0 10px;
            border: 1px solid #cbd6df;
            border-radius: 6px;
            font: inherit;
        }}

        .EstadoBuscaVenda {{
            padding: 30px 0;
            border-top: 1px solid #d6e0e6;
        }}

        .EstadoBuscaVenda p {{ color: #667482; }}

        .ResumoCarrinho {{
            padding: 20px;
            border: 1px solid #d6e0e6;
            border-radius: 6px;
            background: #ffffff;
            box-shadow: 0 10px 22px rgba(31, 49, 61, 0.08);
        }}

        .TituloResumo {{
            margin-bottom: 16px;
            display: flex;
            align-items: baseline;
            justify-content: space-between;
            gap: 12px;
        }}

        .TituloResumo h2 {{ margin: 0; font-size: 19px; }}
        .TituloResumo span {{ color: #667482; font-size: 13px; }}

        .TituloNomeResumo {{
            min-width: 0;
            display: flex;
            align-items: center;
            gap: 7px;
        }}

        .TituloNomeResumo h2 {{
            overflow: hidden;
            max-width: 230px;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}

        .BotaoEditarNomeResumo {{
            flex: 0 0 auto;
            width: 30px;
            height: 30px;
            border: 1px solid #cad8e1;
            border-radius: 4px;
            color: #3f596a;
            background: #f4f8fa;
            font-size: 17px;
            cursor: pointer;
        }}

        .BotaoEditarNomeResumo:hover,
        .BotaoEditarNomeResumo:focus-visible {{
            border-color: #0784ca;
            color: #0784ca;
            outline: 2px solid rgba(7, 132, 202, 0.15);
        }}

        .DialogoNomeCarrinho {{
            width: min(430px, calc(100vw - 32px));
            padding: 0;
            border: 1px solid #b8c8d2;
            border-radius: 6px;
            color: #26313d;
            background: #ffffff;
            box-shadow: 0 22px 60px rgba(22, 43, 56, 0.32);
        }}

        .DialogoNomeCarrinho::backdrop {{ background: rgba(21, 36, 47, 0.48); }}
        .FormularioNomeCarrinho {{ padding: 22px; }}
        .FormularioNomeCarrinho h2 {{ margin: 0 0 18px; font-size: 21px; }}
        .FormularioNomeCarrinho label {{
            display: block;
            margin-bottom: 7px;
            color: #3f4f5f;
            font-size: 13px;
            font-weight: 700;
        }}
        .AcoesDialogoNome {{
            margin-top: 20px;
            display: flex;
            justify-content: flex-end;
            gap: 9px;
        }}
        .AcoesDialogoNome button {{ min-height: 40px; }}

        .TabelaCarrinho {{ overflow-x: auto; }}
        .TabelaCarrinho table {{ box-shadow: none; }}
        .TabelaCarrinho td {{ padding: 11px 6px; }}
        .TabelaCarrinho td strong,
        .TabelaCarrinho td small {{ display: block; }}
        .TabelaCarrinho td small {{ margin-top: 4px; color: #667482; }}
        .TabelaCarrinho th {{ padding: 9px 6px; }}
        .ColunaAcao {{ width: 34px; text-align: right; }}

        .BotaoRemover {{
            width: 30px;
            height: 30px;
            border: 0;
            border-radius: 4px;
            color: #a12c25;
            background: #fde9e7;
            font-size: 20px;
            cursor: pointer;
        }}

        .TotalCarrinho {{
            margin: 18px 0;
            padding-top: 16px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-top: 2px solid #d6e0e6;
        }}

        .TotalCarrinho span {{ color: #52616f; font-weight: 700; }}
        .TotalCarrinho strong {{ color: #0784ca; font-size: 25px; }}

        .CarrinhoVazio {{
            min-height: 120px;
            display: grid;
            place-content: center;
            gap: 7px;
            color: #667482;
            text-align: center;
        }}

        .PagamentoVenda {{ padding-top: 4px; }}
        .PagamentoVenda h2 {{ font-size: 18px; }}

        .OpcoesPagamento {{
            margin: 0 0 16px;
            padding: 0;
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 8px;
            border: 0;
        }}

        .OpcoesPagamento legend {{
            margin-bottom: 8px;
            color: #52616f;
            font-size: 13px;
            font-weight: 700;
        }}

        .OpcoesPagamento label {{
            min-height: 42px;
            padding: 0 12px;
            display: flex;
            align-items: center;
            gap: 8px;
            border: 1px solid #cbd6df;
            border-radius: 6px;
            cursor: pointer;
        }}

        .AreaDinheiro label {{
            display: block;
            margin-bottom: 7px;
            color: #52616f;
            font-size: 13px;
            font-weight: 700;
        }}

        .CampoMoeda {{
            display: grid;
            grid-template-columns: auto 1fr;
            align-items: center;
            border: 1px solid #cbd6df;
            border-radius: 6px;
            overflow: hidden;
        }}

        .CampoMoeda span {{ padding-left: 12px; color: #52616f; }}
        .CampoMoeda input {{
            min-width: 0;
            min-height: 44px;
            padding: 0 12px 0 7px;
            border: 0;
            outline: 0;
            font: inherit;
        }}

        .ResultadoTroco {{
            margin: 12px 0 16px;
            display: flex;
            justify-content: space-between;
            color: #52616f;
        }}

        .ResultadoTroco output {{ color: #202b36; font-weight: 700; }}

        .BotaoConcluir,
        .BotaoCancelar {{
            width: 100%;
            min-height: 44px;
            border-radius: 6px;
            font: inherit;
            font-weight: 700;
            cursor: pointer;
        }}

        .BotaoConcluir {{ border: 0; color: #ffffff; background: #0784ca; }}
        .BotaoCancelar {{ margin-top: 10px; border: 1px solid #c53b32; color: #a12c25; background: #ffffff; }}

        .MensagemOperacao {{
            margin-bottom: 18px;
            padding: 12px 14px;
            border-left: 4px solid;
            border-radius: 4px;
        }}

        .MensagemOperacao.Sucesso {{ border-color: #14866d; color: #0c614f; background: #e7f7f2; }}
        .MensagemOperacao.Erro {{ border-color: #c53b32; color: #8b241e; background: #fff0ef; }}

        .SomenteLeitorTela {{
            position: absolute;
            width: 1px;
            height: 1px;
            padding: 0;
            margin: -1px;
            overflow: hidden;
            clip: rect(0, 0, 0, 0);
            white-space: nowrap;
            border: 0;
        }}

        @media (max-width: 900px) {{
            .GradeVenda {{ grid-template-columns: 1fr; }}
            .ResumoCarrinho {{ order: -1; }}
        }}

        @media (max-width: 620px) {{
            .CabecalhoCarrinho {{ align-items: stretch; flex-direction: column; }}
            .AbaCarrinho {{ padding: 0 8px; flex-direction: column; gap: 3px; font-size: 12px; }}
            .ProdutoResultado {{ grid-template-columns: 1fr; }}
            .FormularioAdicionar {{ grid-template-columns: minmax(90px, 1fr) minmax(104px, 1fr); }}
        }}
    </style>

    <div class="CabecalhoCarrinho">
        <h1>Carrinho de compras</h1>
        <a class="BotaoSecundario" href="/">Página Principal</a>
    </div>

    <nav class="AbasCarrinhos" aria-label="Carrinhos em atendimento">
        {AbasCarrinhos}
    </nav>

    {HtmlMensagem}

    <div class="GradeVenda">
        <section class="BuscaVenda" aria-labelledby="TituloBuscaVenda">
            <h2 id="TituloBuscaVenda">Adicionar produtos</h2>
            <form class="BarraFiltros" method="get" action="/carrinho">
                <input type="hidden" name="carrinho" value="{NumeroCarrinho}">
                <input
                    class="CampoFormulario"
                    type="search"
                    name="busca"
                    value="{BuscaSegura}"
                    placeholder="Produto, categoria, marca ou fornecedor"
                    aria-label="Pesquisar produto, categoria, marca ou fornecedor"
                    autofocus
                >
                <button class="BotaoPrimario" type="submit">Pesquisar</button>
            </form>
            {ResultadosBusca}
        </section>

        <aside class="ResumoCarrinho" aria-labelledby="TituloResumoCarrinho">
            <div class="TituloResumo">
                <div class="TituloNomeResumo">
                    <h2 id="TituloResumoCarrinho">{escape(ResumoCarrinho['Nome'])}</h2>
                    <button
                        class="BotaoEditarNomeResumo"
                        type="button"
                        id="EditarNomeCarrinho"
                        aria-label="Editar nome do carrinho {NumeroCarrinho}"
                        title="Editar nome do cliente"
                    >&#9998;</button>
                </div>
                <span>{ResumoCarrinho['QuantidadeProdutos']} produtos</span>
            </div>
            {ItensCarrinho}
            <div class="TotalCarrinho">
                <span>Total</span>
                <strong>R$ {ResumoCarrinho['TotalFormatado']}</strong>
            </div>
            {Pagamento}
        </aside>
    </div>

    <dialog class="DialogoNomeCarrinho" id="DialogoNomeCarrinho">
        <form class="FormularioNomeCarrinho" method="post" action="/carrinho/nome">
            <input type="hidden" name="csrfmiddlewaretoken" value="{TokenCsrf}">
            <input type="hidden" name="carrinho" value="{NumeroCarrinho}">
            <h2>Identificar atendimento</h2>
            <label for="NomeClienteCarrinho">Nome do cliente</label>
            <input
                id="NomeClienteCarrinho"
                class="CampoFormulario"
                type="text"
                name="nome_cliente"
                value="{escape(ResumoCarrinho['NomePersonalizado'])}"
                maxlength="80"
                autocomplete="off"
                placeholder="Nome do cliente (opcional)"
            >
            <div class="AcoesDialogoNome">
                <button class="BotaoSecundario" type="button" id="FecharDialogoNome">Cancelar</button>
                <button class="BotaoPrimario" type="submit">Salvar nome</button>
            </div>
        </form>
    </dialog>

    <script>
        (() => {{
            const DialogoNome = document.getElementById("DialogoNomeCarrinho");
            const CampoNomeCliente = document.getElementById("NomeClienteCarrinho");

            document.getElementById("EditarNomeCarrinho").addEventListener("click", () => {{
                DialogoNome.showModal();
                CampoNomeCliente.focus();
                CampoNomeCliente.select();
            }});

            document.getElementById("FecharDialogoNome").addEventListener("click", () => {{
                DialogoNome.close();
            }});

            const Formulario = document.getElementById("FormularioPagamento");
            if (!Formulario) return;

            const OpcoesPagamento = Formulario.querySelectorAll('[name="forma_pagamento"]');
            const AreaDinheiro = document.getElementById("AreaDinheiro");
            const ValorRecebido = document.getElementById("ValorRecebido");
            const TrocoCalculado = document.getElementById("TrocoCalculado");
            const Total = Number("{ResumoCarrinho['Total']}");

            const FormatarMoeda = (Valor) => Valor.toLocaleString("pt-BR", {{
                style: "currency",
                currency: "BRL",
            }});

            const ConverterValor = (Valor) => Number(Valor.replace(".", "").replace(",", "."));

            const AtualizarTroco = () => {{
                const Recebido = ConverterValor(ValorRecebido.value);
                if (!Number.isFinite(Recebido)) {{
                    TrocoCalculado.textContent = "R$ 0,00";
                    return;
                }}

                const Diferenca = Recebido - Total;
                TrocoCalculado.textContent = Diferenca >= 0
                    ? FormatarMoeda(Diferenca)
                    : `Faltam ${{FormatarMoeda(Math.abs(Diferenca))}}`;
            }};

            const AtualizarFormaPagamento = () => {{
                const Forma = Formulario.querySelector('[name="forma_pagamento"]:checked').value;
                const UsaDinheiro = Forma === "dinheiro";
                AreaDinheiro.hidden = !UsaDinheiro;
                ValorRecebido.required = UsaDinheiro;
                if (UsaDinheiro) AtualizarTroco();
            }};

            OpcoesPagamento.forEach((Opcao) => Opcao.addEventListener("change", AtualizarFormaPagamento));
            ValorRecebido.addEventListener("input", AtualizarTroco);
            AtualizarFormaPagamento();
        }})();
    </script>
    """

    return HttpResponse(
        RenderizarLayoutBase(
            "Carrinho de compras",
            ConteudoPrincipal,
            RotaAtiva="carrinho",
        )
    )


@ExigirPost
def ComponenteAdicionarItem(Request):
    NumeroCarrinho = ObterNumeroCarrinhoDaAcao(Request)

    if NumeroCarrinho is None:
        return RedirecionarParaCarrinho("1")

    Busca = Request.POST.get("busca", "").strip()

    try:
        ProdutoVenda = AdicionarProdutoAoCarrinho(
            Request,
            NumeroCarrinho,
            Request.POST.get("produto"),
            Request.POST.get("quantidade"),
        )
        DefinirMensagem(Request, f"{ProdutoVenda.Nome} adicionado ao carrinho {NumeroCarrinho}.")
    except ValueError as Erro:
        DefinirMensagem(Request, str(Erro), Tipo="erro")

    return RedirecionarAposAcao(Request, NumeroCarrinho, Busca)


@ExigirPost
def ComponenteRemoverItem(Request):
    NumeroCarrinho = ObterNumeroCarrinhoDaAcao(Request)

    if NumeroCarrinho is None:
        return RedirecionarParaCarrinho("1")

    RemoverProdutoDoCarrinho(
        Request,
        NumeroCarrinho,
        Request.POST.get("produto"),
    )
    DefinirMensagem(Request, f"Produto removido do carrinho {NumeroCarrinho}.")
    return RedirecionarAposAcao(Request, NumeroCarrinho)


@ExigirPost
def ComponenteCancelarCarrinho(Request):
    NumeroCarrinho = ObterNumeroCarrinhoDaAcao(Request)

    if NumeroCarrinho is None:
        return RedirecionarParaCarrinho("1")

    LimparCarrinho(Request, NumeroCarrinho)
    DefinirMensagem(Request, f"Carrinho {NumeroCarrinho} cancelado.")
    return RedirecionarAposAcao(Request, NumeroCarrinho)


@ExigirPost
def ComponenteConcluirCompra(Request):
    NumeroCarrinho = ObterNumeroCarrinhoDaAcao(Request)

    if NumeroCarrinho is None:
        return RedirecionarParaCarrinho("1")

    try:
        VendaConcluida = ConcluirVenda(
            Request,
            NumeroCarrinho,
            Request.POST.get("forma_pagamento", ""),
            Request.POST.get("valor_recebido", ""),
        )
        TotalFormatado = FormatarValorMoeda(VendaConcluida.Total)
        DefinirMensagem(
            Request,
            f"Venda #{VendaConcluida.id} concluída por R$ {TotalFormatado}. Estoque atualizado.",
        )
    except ValueError as Erro:
        DefinirMensagem(Request, str(Erro), Tipo="erro")

    return RedirecionarAposAcao(Request, NumeroCarrinho)


@ExigirPost
def ComponenteRenomearCarrinho(Request):
    NumeroCarrinho = ObterNumeroCarrinhoDaAcao(Request)

    if NumeroCarrinho is None:
        return RedirecionarParaCarrinho("1")

    try:
        NomeExibicao = DefinirNomeCarrinho(
            Request,
            NumeroCarrinho,
            Request.POST.get("nome_cliente", ""),
        )
        DefinirMensagem(
            Request,
            f"O atendimento agora está identificado como {NomeExibicao}.",
        )
    except ValueError as Erro:
        DefinirMensagem(Request, str(Erro), Tipo="erro")

    return RedirecionarAposAcao(Request, NumeroCarrinho)
