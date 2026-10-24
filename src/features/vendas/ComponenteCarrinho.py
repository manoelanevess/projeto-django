"""Componentes do fluxo de atendimento e carrinho de compras."""
from decimal import Decimal
from html import escape
from urllib.parse import urlencode

from django.http import HttpResponse, JsonResponse
from django.middleware.csrf import get_token as ObterTokenCsrf
from django.shortcuts import redirect as Redirecionar
from django.urls import reverse as ObterRota
from django.views.decorators.http import require_POST as ExigirPost

from componentes.LayoutBase import RenderizarLayoutBase
from componentes.PagamentoCarrinho import ObterScriptPagamentoCarrinho
from features.produtos.ApiProduto import (
    BuscarProdutosParaVenda,
    ObterLotesDisponiveisProduto,
)
from features.produtos.LogicaProduto import FormatarQuantidade, FormatarValorMoeda

from .LogicaCarrinho import (
    AdicionarProdutoAoCarrinho,
    ConcluirVenda,
    CriarCarrinhoSessao,
    DefinirNomeCarrinho,
    FecharCarrinhoSessao,
    LimparCarrinho,
    MontarResumosCarrinhos,
    ObterNumerosCarrinhos,
    RemoverProdutoDoCarrinho,
    ValidarNumeroCarrinho,
)
from .ComponenteLeitorCodigoBarras import ObterComplementoLeitorCodigoBarras


ChaveMensagemCarrinho = "MensagemCarrinho"


def ObterNumeroCarrinhoSeguro(Request, Valor):
    try:
        return ValidarNumeroCarrinho(Valor, Request)
    except ValueError:
        return next(iter(ObterNumerosCarrinhos(Request)), None)


def ObterNumeroCarrinhoDaAcao(Request):
    try:
        return ValidarNumeroCarrinho(Request.POST.get("carrinho"), Request)
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

    CarrinhosAbertos = ObterNumerosCarrinhos(Request)

    Parametros = {
        "carrinho": NumeroCarrinho,
        "carrinhos_abertos": ",".join(CarrinhosAbertos),
    }

    if Busca:
        Parametros["busca_carrinho"] = Busca

    return Redirecionar(f"/?{urlencode(Parametros)}")


def RenderizarAbasCarrinhos(ResumosCarrinhos, NumeroSelecionado, TokenCsrf):
    return "".join(
        f"""
        <div class="ItemAbaCarrinho">
        <a
            class="AbaCarrinho{' Ativa' if Resumo['Numero'] == NumeroSelecionado else ''}"
            href="/carrinho?carrinho={Resumo['Numero']}"
            {'aria-current="page"' if Resumo['Numero'] == NumeroSelecionado else ''}
        >
            <span>{escape(Resumo['Nome'])}</span>
            <strong data-resumo-carrinho="{Resumo['Numero']}" data-parte-resumo="aba-quantidade">{Resumo['QuantidadeProdutos']}</strong>
        </a>
        <form method="post" action="/carrinho/fechar" class="FormularioFecharCarrinho"
            data-confirmar-fechamento data-cliente-identificado="{'true' if Resumo['NomePersonalizado'] else 'false'}">
            <input type="hidden" name="csrfmiddlewaretoken" value="{TokenCsrf}">
            <input type="hidden" name="carrinho" value="{Resumo['Numero']}">
            <input type="hidden" name="carrinho_selecionado" value="{NumeroSelecionado}">
            <button class="BotaoFecharCarrinho" type="submit" aria-label="Fechar carrinho {Resumo['Numero']}" title="Fechar carrinho">&times;</button>
        </form>
        </div>
        """
        for Resumo in ResumosCarrinhos
    )


def MontarProdutosParaPesquisa(ProdutosEncontrados):
    Produtos = []

    for ProdutoVenda in ProdutosEncontrados:
        LotesDisponiveis = ObterLotesDisponiveisProduto(ProdutoVenda)

        if not LotesDisponiveis:
            continue

        LoteReferencia = LotesDisponiveis[0]
        Unidade = ProdutoVenda.ObterUnidadeResumida()
        QuantidadeDisponivel = sum(
            (Lote.QuantidadeDisponivel or Decimal("0.000") for Lote in LotesDisponiveis),
            Decimal("0.000"),
        )
        ControlaQuantidade = ProdutoVenda.ControlaQuantidadeEstoque()
        Produtos.append(
            {
                "Id": ProdutoVenda.id,
                "Nome": ProdutoVenda.Nome,
                "Categoria": ProdutoVenda.Categoria or "Sem categoria",
                "Marca": ProdutoVenda.Marca or "Sem marca",
                "Fornecedor": ", ".join(dict.fromkeys(
                    Lote.Fornecedor.Nome for Lote in LotesDisponiveis
                )),
                "Unidade": Unidade,
                "Estoque": (
                    f"{FormatarQuantidade(QuantidadeDisponivel)} {Unidade}"
                    if ControlaQuantidade
                    else LoteReferencia.ObterDescricaoEstoque()
                ),
                "Preco": FormatarValorMoeda(LoteReferencia.PrecoVenda),
                "Passo": ProdutoVenda.ObterPassoVenda(),
                "QuantidadeInicial": ProdutoVenda.ObterQuantidadeInicialVenda(),
                "RotuloQuantidade": ProdutoVenda.ObterRotuloQuantidadeVenda(),
                "EstoqueMaximo": format(QuantidadeDisponivel, "f") if ControlaQuantidade else "",
            }
        )

    return Produtos


def RenderizarResultadosBusca(ProdutosEncontrados, TokenCsrf, NumeroCarrinho, Busca):
    if not Busca:
        return ""

    Produtos = MontarProdutosParaPesquisa(ProdutosEncontrados)

    if not Produtos:
        return """
        <section class="EstadoBuscaVenda">
            <h2>Nenhum produto disponível</h2>
            <p>Confira o nome pesquisado ou verifique o estoque.</p>
        </section>
        """

    CartoesProdutos = []

    for Produto in Produtos:
        AtributoMaximo = f'max="{Produto["EstoqueMaximo"]}"' if Produto["EstoqueMaximo"] else ""
        CartoesProdutos.append(
            f"""
                <article class="ProdutoResultado">
                    <div class="DadosProdutoResultado">
                        <div class="LinhaNomeProduto">
                            <strong>{escape(Produto['Nome'])}</strong>
                            <span class="MarcaProduto">{escape(Produto['Marca'])}</span>
                        </div>
                        <span>{escape(Produto['Categoria'])}</span>
                        <small>{escape(Produto['Fornecedor'])} · Venda R$ {Produto['Preco']} / {Produto['Unidade']} · Estoque: {escape(Produto['Estoque'])}</small>
                    </div>
                    <form class="FormularioAdicionar" method="post" action="/carrinho/adicionar">
                        <input type="hidden" name="csrfmiddlewaretoken" value="{TokenCsrf}">
                        <input type="hidden" name="carrinho" value="{NumeroCarrinho}">
                        <input type="hidden" name="produto" value="{Produto['Id']}">
                        <input type="hidden" name="busca" value="{escape(Busca)}">
                        <label for="Quantidade-{Produto['Id']}">{Produto['RotuloQuantidade']}</label>
                        <input
                            id="Quantidade-{Produto['Id']}"
                            class="CampoQuantidade"
                            type="number"
                            name="quantidade"
                            min="{Produto['Passo']}"
                            {AtributoMaximo}
                            step="{Produto['Passo']}"
                            value="{Produto['QuantidadeInicial']}"
                            required
                        >
                        <button class="BotaoPrimario" type="submit">Adicionar</button>
                    </form>
                </article>
                """
        )

    return f'<section class="ListaResultadosVenda">{"".join(CartoesProdutos)}</section>'


def ComponentePesquisarProdutos(Request):
    Busca = Request.GET.get("busca", "").strip()
    ProdutosEncontrados = BuscarProdutosParaVenda(Busca)
    return JsonResponse({"Produtos": MontarProdutosParaPesquisa(ProdutosEncontrados)})


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
        LoteVenda = Item["Lote"]
        Linhas.append(
            f"""
            <tr>
                <td>
                    <div class="LinhaNomeProduto">
                        <strong>{escape(ProdutoVenda.Nome)}</strong>
                        <span class="MarcaProduto">{escape(ProdutoVenda.Marca or 'Sem marca')}</span>
                    </div>
                    <small>Lote #{Item['NumeroLote']} · {escape(LoteVenda.Fornecedor.Nome)}</small>
                    <small>{Item['QuantidadeFormatada']} {Item['Unidade']} × R$ {Item['PrecoFormatado']}</small>
                </td>
                <td>R$ {Item['SubtotalFormatado']}</td>
                <td class="ColunaAcao">
                    <form method="post" action="/carrinho/remover">
                        <input type="hidden" name="csrfmiddlewaretoken" value="{TokenCsrf}">
                        <input type="hidden" name="carrinho" value="{NumeroCarrinho}">
                        <input type="hidden" name="item" value="{escape(Item['ChaveItem'])}">
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
        <form method="post" action="/carrinho/concluir" id="FormularioPagamento" data-formulario-pagamento data-total="{ResumoCarrinho['Total']}">
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
                <label>
                    <input type="radio" name="forma_pagamento" value="pix_dinheiro">
                    PIX + dinheiro
                </label>
                <label>
                    <input type="radio" name="forma_pagamento" value="conta_cliente">
                    Conta
                </label>
            </fieldset>

            <div class="AreaDinheiro" id="AreaDinheiro" data-area-dinheiro>
                <label for="ValorRecebido">Recebido em dinheiro</label>
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
            </div>

            <div class="AreaPix" data-area-pix hidden>
                <label for="ValorPix">Valor no PIX</label>
                <div class="CampoMoeda">
                    <span>R$</span>
                    <input id="ValorPix" name="valor_pix" type="text" inputmode="decimal"
                        autocomplete="off" placeholder="0,00" disabled>
                </div>
            </div>

            <div class="ResultadoTroco" data-area-troco>
                <span>Troco</span>
                <output id="TrocoCalculado" data-troco aria-live="polite">R$ 0,00</output>
            </div>

            <button class="BotaoConcluir" type="submit">Concluir compra</button>
        </form>

        <form method="post" action="/carrinho/cancelar" data-confirmar="Cancelar atendimento?"
              data-confirmar-descricao="Os itens e o nome do cliente serão descartados. O carrinho continuará aberto para um novo atendimento."
              data-confirmar-acao="Cancelar atendimento" data-confirmar-cancelar="Continuar atendendo">
            <input type="hidden" name="csrfmiddlewaretoken" value="{TokenCsrf}">
            <input type="hidden" name="carrinho" value="{NumeroCarrinho}">
            <button class="BotaoCancelar" type="submit">Cancelar carrinho</button>
        </form>
    </section>
    """


def ComponenteCarrinho(Request):
    NumeroCarrinho = ObterNumeroCarrinhoSeguro(Request, Request.GET.get("carrinho", "1"))
    if NumeroCarrinho is None:
        TokenCsrf = escape(ObterTokenCsrf(Request))
        return HttpResponse(RenderizarLayoutBase("Carrinhos", f"""
            <h1>Carrinhos</h1>
            <p>Nenhum carrinho aberto.</p>
            <form method="post" action="/carrinho/abrir">
                <input type="hidden" name="csrfmiddlewaretoken" value="{TokenCsrf}">
                <button class="BotaoPrimario" type="submit" aria-label="Abrir novo carrinho" title="Abrir novo carrinho"
                    style="width: 42px; height: 42px; padding: 0; font-size: 28px">+</button>
            </form>
        """, RotaAtiva="carrinho", Request=Request))
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

    AbasCarrinhos = RenderizarAbasCarrinhos(ResumosCarrinhos, NumeroCarrinho, TokenCsrf)
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
            display: flex;
            align-items: center;
            gap: 12px;
            border-bottom: 1px solid #cbd6df;
        }}

        .ListaAbasCarrinhos {{ display: flex; flex: 1; min-width: 0; overflow-x: auto; }}
        .ItemAbaCarrinho {{ flex: 1 0 190px; min-width: 0; display: flex; align-items: center; }}
        .FormularioFecharCarrinho {{ margin: 0; flex: 0 0 auto; }}
        .BotaoFecharCarrinho {{
            width: 30px; height: 30px; padding: 0; border: 0; border-radius: 4px;
            background: transparent; color: #52616f; font-size: 23px; cursor: pointer;
        }}
        .BotaoFecharCarrinho:hover {{ color: #9b2635; background: #fbecef; }}
        .AbrirCarrinho {{ flex: 0 0 auto; margin: 0; }}
        .BotaoAbrirCarrinho {{
            width: 42px; height: 42px; padding: 0;
            border: 1px solid #0784ca; border-radius: 4px;
            background: #0784ca; color: white; font-size: 28px; cursor: pointer;
        }}
        .BotaoAbrirCarrinho:hover {{ background: #056da8; }}
        .BotaoAbrirCarrinho:focus-visible {{ outline: 2px solid #26313d; outline-offset: 2px; }}

        .AbaCarrinho {{
            flex: 1;
            min-width: 0;
            max-width: 100%;
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

        .AbaCarrinho span {{ overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}

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

        .BuscaVenda form.BarraFiltros {{ margin-bottom: 0; }}

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
        .LinhaNomeProduto {{ display: flex; align-items: baseline; gap: 8px; flex-wrap: wrap; }}
        .DadosProdutoResultado .MarcaProduto,
        .MarcaProduto {{ color: #202b36; font-size: 13px; font-weight: 600; }}

        .FormularioAdicionar {{
            display: grid;
            grid-template-columns: 132px 104px;
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
            min-width: 0;
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

        .TabelaCarrinho {{ position: relative; overflow-x: auto; }}
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
            grid-template-columns: repeat(2, minmax(0, 1fr));
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

        .AreaPix label,
        .AreaDinheiro label {{
            display: block;
            margin-bottom: 7px;
            color: #52616f;
            font-size: 13px;
            font-weight: 700;
        }}

        .AreaPix {{ margin-top: 12px; }}

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
            .GradeVenda {{ grid-template-columns: minmax(0, 1fr); }}
            .ResumoCarrinho {{ order: -1; }}
        }}

        @media (max-width: 620px) {{
            .CabecalhoCarrinho {{ align-items: stretch; flex-direction: column; }}
            .AbaCarrinho {{ padding: 0 8px; flex-direction: column; gap: 3px; font-size: 12px; }}
            .OpcoesPagamento {{ grid-template-columns: 1fr; }}
            .ProdutoResultado {{ grid-template-columns: 1fr; }}
            .FormularioAdicionar {{ grid-template-columns: minmax(90px, 1fr) minmax(104px, 1fr); }}
        }}
    </style>

    <div class="CabecalhoCarrinho">
        <h1>Carrinho de compras</h1>
        <a class="BotaoSecundario" href="/">Página Principal</a>
    </div>

    <nav class="AbasCarrinhos" aria-label="Carrinhos em atendimento">
        <div class="ListaAbasCarrinhos">{AbasCarrinhos}</div>
        <form class="AbrirCarrinho" method="post" action="/carrinho/abrir">
            <input type="hidden" name="csrfmiddlewaretoken" value="{TokenCsrf}">
            <button class="BotaoAbrirCarrinho" type="submit" aria-label="Abrir novo carrinho" title="Abrir novo carrinho">+</button>
        </form>
    </nav>

    {HtmlMensagem}

    <div class="GradeVenda">
        <section class="BuscaVenda" aria-labelledby="TituloBuscaVenda">
            <h2 id="TituloBuscaVenda">Adicionar produtos</h2>
            <form class="BarraFiltros BuscaUnificadaCarrinho" id="FormularioBuscaCarrinho" method="get" action="/carrinho" data-leitor-codigo="{NumeroCarrinho}" data-token-csrf="{TokenCsrf}">
                <input type="hidden" name="carrinho" value="{NumeroCarrinho}">
                <input
                    id="BuscaProdutoCarrinho"
                    class="CampoFormulario"
                    type="search"
                    name="busca"
                    value="{BuscaSegura}"
                    placeholder="Produto ou código de barras"
                    aria-label="Pesquisar produto, código de barras, categoria, marca ou fornecedor"
                    autocomplete="off"
                    spellcheck="false"
                    data-campo-leitor
                >
                <button class="BotaoPrimario" type="submit">Pesquisar</button>
            </form>
            <p class="MensagemLeitorCodigo" data-mensagem-leitor="{NumeroCarrinho}" role="status"></p>
            <div id="ResultadosBuscaCarrinho" aria-live="polite">
                {ResultadosBusca}
            </div>
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
                <span data-resumo-carrinho="{NumeroCarrinho}" data-parte-resumo="quantidade">{ResumoCarrinho['QuantidadeProdutos']} produtos</span>
            </div>
            <div data-resumo-carrinho="{NumeroCarrinho}" data-parte-resumo="itens">{ItensCarrinho}</div>
            <div class="TotalCarrinho">
                <span>Total</span>
                <strong data-resumo-carrinho="{NumeroCarrinho}" data-parte-resumo="total">R$ {ResumoCarrinho['TotalFormatado']}</strong>
            </div>
            <div data-resumo-carrinho="{NumeroCarrinho}" data-parte-resumo="pagamento">{Pagamento}</div>
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
            const AbaAtiva = document.querySelector(".AbaCarrinho.Ativa");
            const ListaAbas = document.querySelector(".ListaAbasCarrinhos");
            const ExibirAbaAtiva = () => {{
                ListaAbas.scrollLeft += AbaAtiva.getBoundingClientRect().left - ListaAbas.getBoundingClientRect().left;
            }};
            ExibirAbaAtiva();
            window.addEventListener("resize", ExibirAbaAtiva);
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

            const CampoBusca = document.getElementById("BuscaProdutoCarrinho");
            const AreaResultados = document.getElementById("ResultadosBuscaCarrinho");
            let TemporizadorBusca;
            let ControleBusca;

            const CriarElemento = (Tag, Classe, Texto = "") => {{
                const Elemento = document.createElement(Tag);
                if (Classe) Elemento.className = Classe;
                if (Texto) Elemento.textContent = Texto;
                return Elemento;
            }};

            const CriarCampoOculto = (FormularioProduto, Nome, Valor) => {{
                const Campo = document.createElement("input");
                Campo.type = "hidden";
                Campo.name = Nome;
                Campo.value = Valor;
                FormularioProduto.append(Campo);
            }};

            const RenderizarEstadoBusca = (Titulo, Texto) => {{
                const Estado = CriarElemento("section", "EstadoBuscaVenda");
                Estado.append(
                    CriarElemento("h2", "", Titulo),
                    CriarElemento("p", "", Texto),
                );
                AreaResultados.replaceChildren(Estado);
            }};

            const RenderizarProdutos = (Produtos, Busca) => {{
                if (!Produtos.length) {{
                    RenderizarEstadoBusca(
                        "Nenhum produto disponível",
                        "Confira o nome pesquisado ou verifique o estoque.",
                    );
                    return;
                }}

                const Lista = CriarElemento("section", "ListaResultadosVenda");

                Produtos.forEach((Produto) => {{
                    const Cartao = CriarElemento("article", "ProdutoResultado");
                    const Dados = CriarElemento("div", "DadosProdutoResultado");
                    const LinhaNome = CriarElemento("div", "LinhaNomeProduto");
                    LinhaNome.append(
                        CriarElemento("strong", "", Produto.Nome),
                        CriarElemento("span", "MarcaProduto", Produto.Marca),
                    );
                    Dados.append(
                        LinhaNome,
                        CriarElemento("span", "", Produto.Categoria),
                        CriarElemento(
                            "small",
                            "",
                            `${{Produto.Fornecedor}} · Venda R$ ${{Produto.Preco}} / ${{Produto.Unidade}} · Estoque: ${{Produto.Estoque}}`,
                        ),
                    );

                    const FormularioProduto = CriarElemento("form", "FormularioAdicionar");
                    FormularioProduto.method = "post";
                    FormularioProduto.action = "/carrinho/adicionar";
                    CriarCampoOculto(FormularioProduto, "csrfmiddlewaretoken", "{TokenCsrf}");
                    CriarCampoOculto(FormularioProduto, "carrinho", "{NumeroCarrinho}");
                    CriarCampoOculto(FormularioProduto, "produto", Produto.Id);
                    CriarCampoOculto(FormularioProduto, "busca", Busca);

                    const IdentificadorQuantidade = `Quantidade-${{Produto.Id}}`;
                    const Rotulo = CriarElemento("label", "", Produto.RotuloQuantidade);
                    Rotulo.htmlFor = IdentificadorQuantidade;

                    const Quantidade = CriarElemento("input", "CampoQuantidade");
                    Quantidade.id = IdentificadorQuantidade;
                    Quantidade.type = "number";
                    Quantidade.name = "quantidade";
                    Quantidade.min = Produto.Passo;
                    Quantidade.step = Produto.Passo;
                    Quantidade.value = Produto.QuantidadeInicial;
                    Quantidade.required = true;
                    if (Produto.EstoqueMaximo) Quantidade.max = Produto.EstoqueMaximo;

                    const BotaoAdicionar = CriarElemento("button", "BotaoPrimario", "Adicionar");
                    BotaoAdicionar.type = "submit";
                    FormularioProduto.append(Rotulo, Quantidade, BotaoAdicionar);
                    Cartao.append(Dados, FormularioProduto);
                    Lista.append(Cartao);
                }});

                AreaResultados.replaceChildren(Lista);
            }};

            const AtualizarBuscaNaUrl = (Busca) => {{
                const Endereco = new URL(window.location.href);
                if (Busca) Endereco.searchParams.set("busca", Busca);
                else Endereco.searchParams.delete("busca");
                window.history.replaceState(null, "", Endereco.toString());
            }};

            const PesquisarProdutos = async (Busca) => {{
                ControleBusca = new AbortController();
                const ControleAtual = ControleBusca;

                try {{
                    const Parametros = new URLSearchParams({{ busca: Busca }});
                    const Resposta = await fetch(`/carrinho/pesquisar?${{Parametros}}`, {{
                        credentials: "same-origin",
                        signal: ControleAtual.signal,
                    }});

                    if (!Resposta.ok) throw new Error("Falha ao pesquisar produtos");
                    const Dados = await Resposta.json();
                    if (ControleBusca !== ControleAtual) return;
                    RenderizarProdutos(Dados.Produtos, Busca);
                }} catch (Erro) {{
                    if (Erro.name !== "AbortError" && ControleBusca === ControleAtual) {{
                        RenderizarEstadoBusca(
                            "Pesquisa indisponível",
                            "Não foi possível pesquisar agora. Tente novamente.",
                        );
                    }}
                }} finally {{
                    if (ControleBusca === ControleAtual) {{
                        AreaResultados.removeAttribute("aria-busy");
                    }}
                }}
            }};

            CampoBusca.addEventListener("input", () => {{
                const Busca = CampoBusca.value.trim();
                clearTimeout(TemporizadorBusca);
                if (ControleBusca) ControleBusca.abort();
                ControleBusca = null;
                AtualizarBuscaNaUrl(Busca);

                if (!Busca) {{
                    AreaResultados.removeAttribute("aria-busy");
                    AreaResultados.replaceChildren();
                    return;
                }}

                AreaResultados.setAttribute("aria-busy", "true");
                TemporizadorBusca = window.setTimeout(() => PesquisarProdutos(Busca), 160);
            }});
        }})();
    </script>
    """

    return HttpResponse(
        RenderizarLayoutBase(
            "Carrinho de compras",
            ConteudoPrincipal + ObterScriptPagamentoCarrinho() + ObterComplementoLeitorCodigoBarras(NumeroCarrinho),
            RotaAtiva="carrinho",
            Request=Request,
        )
    )


@ExigirPost
def ComponenteAbrirCarrinho(Request):
    Numero = CriarCarrinhoSessao(Request)
    return RedirecionarAposAcao(Request, Numero)


@ExigirPost
def ComponenteFecharCarrinho(Request):
    Numero = ObterNumeroCarrinhoDaAcao(Request)
    if Numero is not None:
        FecharCarrinhoSessao(Request, Numero)
    Proximo = ObterNumeroCarrinhoSeguro(Request, Request.POST.get("carrinho_selecionado")) or "1"
    return RedirecionarAposAcao(Request, Proximo)


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
        Request.POST.get("item") or Request.POST.get("produto"),
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
            Request.POST.get("valor_pix", ""),
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
