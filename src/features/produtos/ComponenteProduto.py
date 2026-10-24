"""Componentes de cadastro e manutenção de produtos."""
from datetime import date
from html import escape
from urllib.parse import urlencode

from django.http import HttpResponse
from django.middleware.csrf import get_token as ObterTokenCsrf
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.decorators.http import require_POST as ExigirPost
from django.views.decorators.http import require_GET as ExigirGet

from componentes.LayoutBase import RenderizarLayoutBase

from .ApiProduto import BuscarProdutoPorCodigoBarras
from .ComponenteCatalogoProduto import ObterScriptConsultaCatalogoProduto
from .LogicaCodigoBarras import EhCodigoGtin, NormalizarCodigoBarras
from .FormularioProduto import (
    FormularioEdicaoProduto,
    FormularioLoteEstoque,
    FormularioProduto,
    FormularioValidadeLote,
)
from .LogicaProduto import FormatarQuantidade, FormatarValorMoeda
from .models import LoteEstoque, Produto


ChaveMensagemProduto = "MensagemProduto"


def DefinirMensagemProduto(Request, Texto, Tipo="sucesso"):
    Request.session[ChaveMensagemProduto] = {"Texto": Texto, "Tipo": Tipo}


def ConsumirMensagemProduto(Request):
    return Request.session.pop(ChaveMensagemProduto, None)


def ComponenteRedirecionarProdutos(Request):
    return redirect("Estoque")


def RedirecionarPesquisaEstoque(Request):
    Parametros = {"busca": Request.GET.get("codigo", "").strip()}

    for NomeFiltro in ("categoria", "fornecedor", "estoque", "inicio"):
        ValorFiltro = Request.GET.get(NomeFiltro, "").strip()
        if ValorFiltro:
            Parametros[NomeFiltro] = ValorFiltro

    return redirect(f"/estoque?{urlencode(Parametros)}")


@ExigirGet
def ComponenteLerCodigoEstoque(Request):
    PermitirPesquisa = Request.GET.get("permitir_pesquisa") == "1"

    try:
        Codigo = NormalizarCodigoBarras(Request.GET.get("codigo"), Obrigatorio=True)
        ProdutoEncontrado = BuscarProdutoPorCodigoBarras(Codigo)
    except ValueError as Erro:
        if PermitirPesquisa and "\x00" not in Request.GET.get("codigo", ""):
            return RedirecionarPesquisaEstoque(Request)
        DefinirMensagemProduto(Request, str(Erro), Tipo="erro")
        return redirect("Estoque")

    if ProdutoEncontrado is None:
        if PermitirPesquisa and not EhCodigoGtin(Codigo):
            return RedirecionarPesquisaEstoque(Request)
        return redirect(f"/estoque/novo?{urlencode({'codigo': Codigo})}")

    if not ProdutoEncontrado.Ativo:
        DefinirMensagemProduto(Request, "Este código pertence a um produto inativo.", Tipo="erro")
        return redirect("Estoque")

    return redirect(f"/estoque/{ProdutoEncontrado.id}/editar?entrada=1#NovaEntradaEstoque")


def ObterScriptCodigoProduto():
    return """
    <script>
        (() => {
            const CampoCodigo = document.getElementById("id_CodigoBarras");
            CampoCodigo.addEventListener("keydown", (Evento) => {
                if (Evento.key !== "Enter" || Evento.isComposing) return;
                Evento.preventDefault();
                document.getElementById("id_Nome").focus();
            });
            if (new URLSearchParams(window.location.search).get("entrada") === "1") {
                const CampoEntrada = document.getElementById("id_Lote-QuantidadeEntrada")
                    || document.getElementById("id_Lote-Fornecedor");
                if (CampoEntrada) {
                    window.addEventListener("load", () => CampoEntrada.focus({ preventScroll: true }), { once: true });
                }
            }
        })();
    </script>
    """


def RenderizarErrosCampo(Formulario, NomeCampo):
    return "".join(
        f'<span class="ErroCampo">{escape(str(Erro))}</span>'
        for Erro in Formulario.errors.get(NomeCampo, [])
    )


def RenderizarCampo(Formulario, NomeCampo, Rotulo, Descricao=""):
    Campo = Formulario[NomeCampo]
    DescricaoHtml = (
        f'<small class="AjudaCampo">{escape(Descricao)}</small>' if Descricao else ""
    )
    return f"""
    <div class="GrupoCampo" data-campo="{NomeCampo}">
        <label for="{Campo.id_for_label}">{escape(Rotulo)}</label>
        {Campo}
        {DescricaoHtml}
        {RenderizarErrosCampo(Formulario, NomeCampo)}
    </div>
    """


def RenderizarLotesProduto(ProdutoEdicao, TokenCsrf):
    Lotes = ProdutoEdicao.LotesEstoque.select_related("Fornecedor").order_by(
        "-CriadoEm", "-id"
    )

    if not Lotes:
        return """
        <div class="EstadoLotesVazio">
            Nenhuma entrada de estoque foi registrada para este produto.
        </div>
        """

    Linhas = []

    for Lote in Lotes:
        NumeroLote = Lote.ObterNumeroNoProduto()
        DataEntrada = timezone.localtime(Lote.CriadoEm).date()
        IdValidade = f"ValidadeLote-{Lote.id}"
        CampoValidade = FormularioValidadeLote(instance=Lote)["DataValidade"].as_widget(
            attrs={"id": IdValidade, "class": "CampoDataLote"}
        )

        if ProdutoEdicao.EhControladoPorDisponibilidade():
            Saldo = "Disponível" if Lote.Disponivel else "Indisponível"
        else:
            Saldo = (
                f"{FormatarQuantidade(Lote.QuantidadeDisponivel)} "
                f"{ProdutoEdicao.ObterUnidadeResumida()}"
            )

        Situacao = "Ativo" if Lote.EstaDisponivelParaVenda() else "Encerrado"
        AcaoEncerrar = ""

        if Lote.Ativo:
            AcaoEncerrar = f"""
            <form
                method="post"
                action="/estoque/{ProdutoEdicao.id}/lotes/{Lote.id}/encerrar"
                data-confirmar="Encerrar lote #{NumeroLote}?"
                data-confirmar-descricao="Este lote deixará de estar disponível para adicionar produtos aos carrinhos."
                data-confirmar-acao="Encerrar lote"
            >
                <input type="hidden" name="csrfmiddlewaretoken" value="{TokenCsrf}">
                <button class="BotaoEncerrarLote" type="submit">Encerrar</button>
            </form>
            """

        AcaoExcluir = f"""
        <form
            method="post"
            action="/estoque/{ProdutoEdicao.id}/lotes/{Lote.id}/excluir"
            data-confirmar="Excluir lote #{NumeroLote}?"
            data-confirmar-descricao="O saldo deste lote será removido do estoque. Confira o lote antes de continuar."
            data-confirmar-acao="Excluir lote"
        >
            <input type="hidden" name="csrfmiddlewaretoken" value="{TokenCsrf}">
            <button class="BotaoExcluirLote" type="submit">Excluir</button>
        </form>
        """
        Acoes = f'<div class="AcoesLote">{AcaoEncerrar}{AcaoExcluir}</div>'

        Linhas.append(
            f"""
            <tr>
                <td><strong>#{NumeroLote}</strong></td>
                <td>
                    <form class="FormularioDataLote" method="post" action="/estoque/{ProdutoEdicao.id}/lotes/{Lote.id}/data">
                        <input type="hidden" name="csrfmiddlewaretoken" value="{TokenCsrf}">
                        <label class="SomenteLeitorTela" for="DataLote-{Lote.id}">Data de entrada do lote #{NumeroLote}</label>
                        <input
                            id="DataLote-{Lote.id}"
                            class="CampoDataLote"
                            type="date"
                            name="DataEntrada"
                            value="{DataEntrada.isoformat()}"
                            max="{timezone.localdate().isoformat()}"
                            required
                        >
                        <button class="BotaoSalvarDataLote" type="submit">Salvar</button>
                    </form>
                </td>
                <td>
                    <form class="FormularioDataLote" method="post" action="/estoque/{ProdutoEdicao.id}/lotes/{Lote.id}/validade">
                        <input type="hidden" name="csrfmiddlewaretoken" value="{TokenCsrf}">
                        <label class="SomenteLeitorTela" for="{IdValidade}">Data de validade do lote #{NumeroLote}</label>
                        {CampoValidade}
                        <button class="BotaoSalvarDataLote" type="submit" aria-label="Salvar validade do lote #{NumeroLote}">Salvar</button>
                    </form>
                </td>
                <td>{escape(Lote.Fornecedor.Nome)}</td>
                <td>R$ {FormatarValorMoeda(Lote.PrecoCusto)}</td>
                <td>R$ {FormatarValorMoeda(Lote.PrecoVenda)}</td>
                <td>{escape(Saldo)}</td>
                <td><span class="SituacaoLote {'Ativo' if Lote.EstaDisponivelParaVenda() else 'Encerrado'}">{Situacao}</span></td>
                <td>{Acoes}</td>
            </tr>
            """
        )

    return f"""
    <div class="TabelaLotes">
        <table>
            <thead>
                <tr>
                    <th>Lote</th>
                    <th>Data de entrada</th>
                    <th>Data de validade</th>
                    <th>Fornecedor</th>
                    <th>Preço de custo</th>
                    <th>Preço de venda</th>
                    <th>Saldo</th>
                    <th>Situação</th>
                    <th><span class="SomenteLeitorTela">Ações</span></th>
                </tr>
            </thead>
            <tbody>{''.join(Linhas)}</tbody>
        </table>
    </div>
    """


def ComponenteEditarProdutoComLotes(Request, ProdutoEdicao):
    Acao = Request.POST.get("acao", "salvar_produto")
    FormularioDados = FormularioEdicaoProduto(instance=ProdutoEdicao)
    FormularioLote = FormularioLoteEstoque(ProdutoVenda=ProdutoEdicao, prefix="Lote")

    if Request.method == "POST" and Acao == "adicionar_lote":
        FormularioLote = FormularioLoteEstoque(
            Request.POST,
            ProdutoVenda=ProdutoEdicao,
            prefix="Lote",
        )

        if FormularioLote.is_valid():
            LoteCriado = FormularioLote.CriarLote()
            DefinirMensagemProduto(
                Request,
                f"Lote #{LoteCriado.ObterNumeroNoProduto()} adicionado a {ProdutoEdicao.Nome}.",
            )
            return redirect("EditarProduto", ProdutoId=ProdutoEdicao.id)
    elif Request.method == "POST":
        FormularioDados = FormularioEdicaoProduto(
            Request.POST,
            instance=ProdutoEdicao,
        )

        if FormularioDados.is_valid():
            FormularioDados.save()
            DefinirMensagemProduto(
                Request,
                f"{ProdutoEdicao.Nome} foi atualizado com sucesso.",
            )
            return redirect("EditarProduto", ProdutoId=ProdutoEdicao.id)

    TokenCsrf = ObterTokenCsrf(Request)
    LotesHtml = RenderizarLotesProduto(ProdutoEdicao, TokenCsrf)
    Mensagem = ConsumirMensagemProduto(Request)
    MensagemHtml = ""

    if Mensagem:
        Tipo = "Erro" if Mensagem.get("Tipo") == "erro" else "Sucesso"
        MensagemHtml = (
            f'<div class="MensagemOperacao {Tipo}" role="status">'
            f'{escape(Mensagem.get("Texto", ""))}</div>'
        )

    CampoEntrada = ""

    if ProdutoEdicao.EhControladoPorDisponibilidade():
        CampoDisponivel = FormularioLote["Disponivel"]
        CampoEntrada = f"""
        <div class="GrupoCampo GrupoCampoLargo">
            <div class="ControleDisponibilidade">
                {CampoDisponivel}
                <label for="{CampoDisponivel.id_for_label}">
                    Lote disponível para venda
                    <small class="AjudaCampo">Desmarque quando o lote vendido por peso terminar.</small>
                </label>
            </div>
            {RenderizarErrosCampo(FormularioLote, "Disponivel")}
        </div>
        """
    else:
        CampoEntrada = RenderizarCampo(
            FormularioLote,
            "QuantidadeEntrada",
            "Quantidade recebida",
            "O saldo antigo continuará separado neste produto.",
        )

    ErrosDados = "".join(
        f'<div class="MensagemFormulario Erro">{escape(str(Erro))}</div>'
        for Erro in FormularioDados.non_field_errors()
    )
    ErrosLote = "".join(
        f'<div class="MensagemFormulario Erro">{escape(str(Erro))}</div>'
        for Erro in FormularioLote.non_field_errors()
    )
    ConteudoPrincipal = f"""
    <style>
        .CabecalhoFormulario {{
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 16px;
        }}
        .CabecalhoFormulario h1 {{ margin: 0; }}
        .SecaoEdicaoProduto {{
            margin-bottom: 22px;
            padding: 22px;
            border: 1px solid #d6e0e6;
            border-radius: 6px;
            background: #ffffff;
            box-shadow: 0 10px 22px rgba(31, 49, 61, 0.07);
        }}
        .SecaoEdicaoProduto h2 {{ margin: 0 0 5px; font-size: 20px; }}
        .SecaoEdicaoProduto > p {{ margin: 0 0 18px; color: #667482; }}
        .GradeFormulario {{
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 18px;
        }}
        .GrupoCampo {{ min-width: 0; }}
        .GrupoCampo label {{
            display: block;
            margin-bottom: 7px;
            color: #3f4f5f;
            font-size: 13px;
            font-weight: 700;
        }}
        .GrupoCampo .CampoFormulario {{ width: 100%; min-width: 0; }}
        .GrupoCampoLargo {{ grid-column: 1 / -1; }}
        .AjudaCampo {{ display: block; margin-top: 6px; color: #667482; line-height: 1.35; }}
        .ErroCampo {{ display: block; margin-top: 6px; color: #a12c25; font-size: 13px; }}
        .AcoesFormulario {{
            margin-top: 20px;
            padding-top: 18px;
            display: flex;
            justify-content: flex-end;
            gap: 10px;
            border-top: 1px solid #d9e2ec;
        }}
        .ControleDisponibilidade {{
            min-height: 64px;
            padding: 12px 14px;
            display: flex;
            align-items: center;
            gap: 10px;
            border: 1px solid #cbd6df;
            border-radius: 6px;
            background: #f7fafb;
        }}
        .ControleDisponibilidade label {{ margin: 0; cursor: pointer; }}
        .CampoCheckbox {{ width: 18px; height: 18px; accent-color: #0784ca; }}
        .TabelaLotes {{ margin-bottom: 22px; overflow-x: auto; position: relative; }}
        .TabelaLotes table {{ min-width: 1100px; box-shadow: none; }}
        .TabelaLotes td strong,
        .TabelaLotes td small {{ display: block; }}
        .TabelaLotes td small {{ margin-top: 3px; color: #667482; }}
        .FormularioDataLote {{ display: flex; align-items: center; gap: 6px; }}
        .CampoDataLote {{
            min-height: 34px;
            width: 138px;
            padding: 0 7px;
            border: 1px solid #cbd6df;
            border-radius: 5px;
            color: #26313d;
            background: #ffffff;
            font: inherit;
            font-size: 12px;
        }}
        .BotaoSalvarDataLote {{
            min-height: 34px;
            padding: 0 9px;
            border: 1px solid #9dcbe4;
            border-radius: 5px;
            color: #0677b5;
            background: #e5f4fc;
            font: inherit;
            font-size: 12px;
            font-weight: 700;
            cursor: pointer;
        }}
        .SituacaoLote {{
            display: inline-flex;
            min-height: 26px;
            padding: 0 9px;
            align-items: center;
            border-radius: 999px;
            font-size: 12px;
            font-weight: 700;
        }}
        .SituacaoLote.Ativo {{ color: #0c614f; background: #dff4ed; }}
        .SituacaoLote.Encerrado {{ color: #6b7783; background: #e9eef1; }}
        .AcoesLote {{ display: flex; align-items: center; gap: 6px; }}
        .BotaoEncerrarLote {{
            min-height: 34px;
            padding: 0 11px;
            border: 1px solid #d6a6a1;
            border-radius: 5px;
            color: #972d26;
            background: #fff3f2;
            font: inherit;
            font-size: 12px;
            font-weight: 700;
            cursor: pointer;
        }}
        .BotaoExcluirLote {{
            min-height: 34px;
            padding: 0 11px;
            border: 1px solid #e2a6a1;
            border-radius: 5px;
            color: #a12c25;
            background: #ffffff;
            font: inherit;
            font-size: 12px;
            font-weight: 700;
            cursor: pointer;
        }}
        .EstadoLotesVazio {{ margin-bottom: 20px; padding: 18px; background: #f3f7f9; color: #667482; }}
        .MensagemFormulario.Erro {{ margin-bottom: 16px; color: #8b241e; }}
        .MensagemOperacao {{ margin-bottom: 18px; padding: 12px 14px; border-left: 4px solid; border-radius: 4px; }}
        .MensagemOperacao.Sucesso {{ border-color: #14866d; color: #0c614f; background: #e7f7f2; }}
        .MensagemOperacao.Erro {{ border-color: #c53b32; color: #8b241e; background: #fff0ef; }}
        .SomenteLeitorTela {{ position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0, 0, 0, 0); }}
        @media (max-width: 760px) {{
            .GradeFormulario {{ grid-template-columns: minmax(0, 1fr); }}
            .CabecalhoFormulario {{ flex-direction: column; align-items: stretch; }}
            .SecaoEdicaoProduto {{ padding: 16px; }}
        }}
    </style>

    <div class="CabecalhoFormulario">
        <h1>Editar produto</h1>
        <a class="BotaoSecundario" href="/estoque">Voltar ao estoque</a>
    </div>
    {MensagemHtml}

    <form class="SecaoEdicaoProduto" method="post">
        <input type="hidden" name="csrfmiddlewaretoken" value="{TokenCsrf}">
        <input type="hidden" name="acao" value="salvar_produto">
        <h2>Dados do produto</h2>
        <p>Os preços e saldos são mantidos separadamente em cada lote.</p>
        {ErrosDados}
        <div class="GradeFormulario">
            {RenderizarCampo(FormularioDados, "Nome", "Nome do produto")}
            {RenderizarCampo(FormularioDados, "CodigoBarras", "Código de barras")}
            {RenderizarCampo(FormularioDados, "Categoria", "Categoria")}
            {RenderizarCampo(FormularioDados, "Marca", "Marca", "Opcional para produtos sem marca definida.")}
            {RenderizarCampo(FormularioDados, "UnidadeVenda", "Forma de venda", "A forma de venda não pode ser alterada depois da criação dos lotes.")}
            {'' if ProdutoEdicao.EhControladoPorDisponibilidade() else RenderizarCampo(FormularioDados, "EstoqueMinimo", "Estoque mínimo")}
        </div>
        <div class="AcoesFormulario">
            <button class="BotaoPrimario" type="submit">Salvar dados</button>
        </div>
    </form>

    <section class="SecaoEdicaoProduto" aria-labelledby="TituloLotesProduto">
        <h2 id="TituloLotesProduto">Entradas de estoque</h2>
        <p>Cada entrada preserva seu fornecedor, custo, preço de venda e saldo.</p>
        {LotesHtml}

        <form method="post" id="NovaEntradaEstoque">
            <input type="hidden" name="csrfmiddlewaretoken" value="{TokenCsrf}">
            <input type="hidden" name="acao" value="adicionar_lote">
            <h2>Adicionar nova entrada</h2>
            {ErrosLote}
            <div class="GradeFormulario">
                {RenderizarCampo(FormularioLote, "Fornecedor", "Fornecedor")}
                {RenderizarCampo(FormularioLote, "DataValidade", "Data de validade (opcional)")}
                {RenderizarCampo(FormularioLote, "PrecoCusto", "Preço de custo (R$)")}
                {RenderizarCampo(FormularioLote, "PrecoVenda", "Preço de venda (R$)")}
                {CampoEntrada}
            </div>
            <div class="AcoesFormulario">
                <button class="BotaoPrimario" type="submit">Adicionar entrada</button>
            </div>
        </form>
    </section>
    """

    return HttpResponse(
        RenderizarLayoutBase("Editar produto", ConteudoPrincipal + ObterScriptCodigoProduto(), RotaAtiva="estoque", Request=Request)
    )


def ComponenteFormularioProduto(Request, ProdutoId=None):
    if ProdutoId is not None:
        ProdutoEdicao = get_object_or_404(Produto, pk=ProdutoId, Ativo=True)
        return ComponenteEditarProdutoComLotes(Request, ProdutoEdicao)

    ProdutoEdicao = None

    if Request.method == "POST":
        Formulario = FormularioProduto(Request.POST, instance=ProdutoEdicao)

        if Formulario.is_valid():
            ProdutoSalvo = Formulario.CriarProduto()
            Acao = "atualizado" if ProdutoEdicao else "cadastrado"
            DefinirMensagemProduto(
                Request,
                f"{ProdutoSalvo.Nome} foi {Acao} com sucesso.",
            )
            return redirect("Estoque")
    else:
        Formulario = FormularioProduto(
            instance=ProdutoEdicao,
            initial={"CodigoBarras": Request.GET.get("codigo", "")},
        )

    Titulo = "Editar produto" if ProdutoEdicao else "Adicionar produto"
    TextoBotao = "Salvar alterações" if ProdutoEdicao else "Cadastrar produto"
    TokenCsrf = ObterTokenCsrf(Request)
    TemFornecedores = Formulario.fields["Fornecedor"].queryset.exists()
    AvisoFornecedor = ""

    if not TemFornecedores:
        AvisoFornecedor = """
        <div class="AvisoFornecedor" role="alert">
            Cadastre um fornecedor antes de adicionar o produto.
            <a href="/fornecedores/novo">Adicionar fornecedor</a>
        </div>
        """

    ErrosGerais = "".join(
        f'<div class="MensagemFormulario Erro">{escape(str(Erro))}</div>'
        for Erro in Formulario.non_field_errors()
    )

    CampoDisponivel = Formulario["Disponivel"]
    ErroDisponivel = RenderizarErrosCampo(Formulario, "Disponivel")
    ConteudoPrincipal = f"""
    <style>
        .CabecalhoFormulario {{
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 16px;
        }}

        .CabecalhoFormulario h1 {{ margin: 0; }}

        .PainelFormulario {{
            padding: 24px;
            border: 1px solid #d6e0e6;
            border-radius: 6px;
            background: #ffffff;
            box-shadow: 0 10px 22px rgba(31, 49, 61, 0.08);
        }}

        .GradeFormulario {{
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 18px;
        }}

        .GrupoCampo {{ min-width: 0; }}
        .GrupoCampo label {{
            display: block;
            margin-bottom: 7px;
            color: #3f4f5f;
            font-size: 13px;
            font-weight: 700;
        }}
        .GrupoCampo .CampoFormulario {{ width: 100%; min-width: 0; }}
        .GrupoCampoLargo {{ grid-column: 1 / -1; }}

        .AjudaCampo {{
            display: block;
            margin-top: 6px;
            color: #667482;
            line-height: 1.35;
        }}

        .ErroCampo {{
            display: block;
            margin-top: 6px;
            color: #a12c25;
            font-size: 13px;
        }}

        .ControleDisponibilidade {{
            min-height: 64px;
            padding: 12px 14px;
            display: flex;
            align-items: center;
            gap: 10px;
            border: 1px solid #cbd6df;
            border-radius: 6px;
            background: #f7fafb;
        }}

        .ControleDisponibilidade label {{ margin: 0; cursor: pointer; }}
        .CampoCheckbox {{ width: 18px; height: 18px; accent-color: #0784ca; }}

        .AcoesFormulario {{
            margin-top: 24px;
            padding-top: 20px;
            display: flex;
            justify-content: flex-end;
            gap: 10px;
            border-top: 1px solid #d9e2ec;
        }}

        .MensagemFormulario.Erro {{
            margin-bottom: 16px;
            padding: 12px 14px;
            border-left: 4px solid #c53b32;
            border-radius: 4px;
            color: #8b241e;
            background: #fff0ef;
        }}

        .AvisoFornecedor {{
            margin-bottom: 18px;
            padding: 12px 14px;
            border-left: 4px solid #f59f18;
            border-radius: 4px;
            color: #68440b;
            background: #fff6df;
        }}
        .AvisoFornecedor a {{ color: #056da8; font-weight: 700; }}

        .ConsultaCatalogo {{ margin: 0 0 18px; color: #526473; font-size: 14px; line-height: 1.5; }}
        .ConsultaCatalogo a {{ color: #056da8; }}

        .CabecalhoCadastroProduto {{ margin-bottom: 12px; }}
        .CadastroProdutoCompacto {{ padding: 16px; }}
        .CadastroProdutoCompacto .GradeFormulario {{ gap: 12px 16px; }}
        .CadastroProdutoCompacto .GrupoCampo label {{ margin-bottom: 5px; }}
        .CadastroProdutoCompacto .CampoFormulario {{ min-height: 38px; padding: 8px 10px; }}
        .CadastroProdutoCompacto .ConsultaCatalogo {{ margin-bottom: 12px; line-height: 1.35; }}
        .CadastroProdutoCompacto .AcoesFormulario {{ margin-top: 14px; padding-top: 12px; }}
        .CadastroProdutoCompacto .ControleDisponibilidade {{ min-height: 38px; padding: 8px 10px; }}
        @media (min-width: 1000px) {{
            .CadastroProdutoCompacto .GradeFormulario {{
                grid-template-columns: repeat(3, minmax(0, 1fr));
                grid-template-areas:
                    "Nome Nome CodigoBarras"
                    "Marca Categoria DataValidade"
                    "PrecoCusto UnidadeVenda QuantidadeEstoque"
                    "PrecoVenda Fornecedor EstoqueMinimo";
            }}
            .CadastroProdutoCompacto [data-campo="Nome"] {{ grid-area: Nome; }}
            .CadastroProdutoCompacto [data-campo="CodigoBarras"] {{ grid-area: CodigoBarras; }}
            .CadastroProdutoCompacto [data-campo="Marca"] {{ grid-area: Marca; }}
            .CadastroProdutoCompacto [data-campo="Categoria"] {{ grid-area: Categoria; }}
            .CadastroProdutoCompacto [data-campo="DataValidade"] {{ grid-area: DataValidade; }}
            .CadastroProdutoCompacto [data-campo="PrecoCusto"] {{ grid-area: PrecoCusto; }}
            .CadastroProdutoCompacto [data-campo="PrecoVenda"] {{ grid-area: PrecoVenda; }}
            .CadastroProdutoCompacto [data-campo="UnidadeVenda"] {{ grid-area: UnidadeVenda; }}
            .CadastroProdutoCompacto [data-campo="Fornecedor"] {{ grid-area: Fornecedor; }}
            .CadastroProdutoCompacto [data-campo="QuantidadeEstoque"] {{ grid-area: QuantidadeEstoque; }}
            .CadastroProdutoCompacto [data-campo="EstoqueMinimo"] {{ grid-area: EstoqueMinimo; }}
            .CadastroProdutoCompacto [data-campo="Disponivel"] {{ grid-column: 3; grid-row: 3 / span 2; }}
        }}
        [hidden] {{ display: none !important; }}
        @media (max-width: 760px) {{
            .GradeFormulario {{ grid-template-columns: minmax(0, 1fr); }}
            .CabecalhoFormulario {{ flex-direction: column; align-items: stretch; }}
            .PainelFormulario {{ padding: 16px; }}
        }}
    </style>

    <div class="CabecalhoFormulario CabecalhoCadastroProduto">
        <h1>{Titulo}</h1>
        <a class="BotaoSecundario" href="/estoque">Voltar ao estoque</a>
    </div>

    <form class="PainelFormulario CadastroProdutoCompacto" method="post">
        <input type="hidden" name="csrfmiddlewaretoken" value="{TokenCsrf}">
        <div class="ConsultaCatalogo" id="ConsultaCatalogoProduto" role="status" aria-live="polite" hidden>
            <span id="MensagemCatalogoProduto"></span>
            <span id="FonteCatalogoProduto" hidden></span>
        </div>
        {ErrosGerais}
        {AvisoFornecedor}

        <div class="GradeFormulario">
            {RenderizarCampo(Formulario, "Nome", "Nome do produto")}
            {RenderizarCampo(Formulario, "CodigoBarras", "Código de barras")}
            {RenderizarCampo(Formulario, "Marca", "Marca (opcional)")}
            {RenderizarCampo(Formulario, "Categoria", "Categoria")}
            {RenderizarCampo(Formulario, "DataValidade", "Validade do lote inicial (opcional)")}
            {RenderizarCampo(Formulario, "PrecoCusto", "Preço de custo (R$)")}
            {RenderizarCampo(Formulario, "UnidadeVenda", "Forma de venda")}
            {RenderizarCampo(Formulario, "QuantidadeEstoque", "Quantidade em estoque")}
            {RenderizarCampo(Formulario, "PrecoVenda", "Preço de venda (R$)")}
            {RenderizarCampo(Formulario, "Fornecedor", "Fornecedor")}
            {RenderizarCampo(Formulario, "EstoqueMinimo", "Estoque mínimo")}

            <div class="GrupoCampo GrupoCampoLargo" data-campo="Disponivel">
                <div class="ControleDisponibilidade">
                    {CampoDisponivel}
                    <label for="{CampoDisponivel.id_for_label}">
                        Produto disponível para venda
                        <small class="AjudaCampo">Use esta opção em produtos vendidos por peso, que não possuem quantidade exata cadastrada.</small>
                    </label>
                </div>
                {ErroDisponivel}
            </div>
        </div>

        <div class="AcoesFormulario">
            <a class="BotaoSecundario" href="/estoque">Cancelar</a>
            <button class="BotaoPrimario" type="submit">{TextoBotao}</button>
        </div>
    </form>

    <script>
        (() => {{
            const CampoFormaVenda = document.getElementById("id_UnidadeVenda");
            const GrupoQuantidade = document.querySelector('[data-campo="QuantidadeEstoque"]');
            const GrupoEstoqueMinimo = document.querySelector('[data-campo="EstoqueMinimo"]');
            const GrupoDisponivel = document.querySelector('[data-campo="Disponivel"]');
            const CampoQuantidade = document.getElementById("id_QuantidadeEstoque");
            const CampoEstoqueMinimo = document.getElementById("id_EstoqueMinimo");

            const AtualizarCamposEstoque = () => {{
                const VendaPorPeso = CampoFormaVenda.value === "quilograma";
                const ExigeInteiro = ["unidade", "valor_fixo"].includes(CampoFormaVenda.value);

                GrupoQuantidade.hidden = VendaPorPeso;
                GrupoEstoqueMinimo.hidden = VendaPorPeso;
                GrupoDisponivel.hidden = !VendaPorPeso;
                CampoQuantidade.required = !VendaPorPeso;
                CampoEstoqueMinimo.required = !VendaPorPeso;
                CampoQuantidade.step = ExigeInteiro ? "1" : "0.001";
                CampoEstoqueMinimo.step = ExigeInteiro ? "1" : "0.001";
            }};

            CampoFormaVenda.addEventListener("change", AtualizarCamposEstoque);
            AtualizarCamposEstoque();

            const Formulario = CampoFormaVenda.form;
            const CampoCodigo = document.getElementById("id_CodigoBarras");
            const ObterCamposVisiveis = () => Array.from(Formulario.querySelectorAll(".GrupoCampo input, .GrupoCampo select"))
                .filter((Campo) => Campo !== CampoCodigo && !Campo.matches(":disabled") && !Campo.readOnly && Campo.getClientRects().length)
                .sort((Primeiro, Segundo) => {{
                    const CaixaPrimeiro = Primeiro.closest(".GrupoCampo").getBoundingClientRect();
                    const CaixaSegundo = Segundo.closest(".GrupoCampo").getBoundingClientRect();
                    return Math.abs(CaixaPrimeiro.top - CaixaSegundo.top) > 2
                        ? CaixaPrimeiro.top - CaixaSegundo.top : CaixaPrimeiro.left - CaixaSegundo.left;
                }});
            Formulario.addEventListener("keydown", (Evento) => {{
                const Campo = Evento.target;
                if (Evento.key !== "Enter" || Evento.isComposing || !Campo.matches(".GrupoCampo input, .GrupoCampo select")) return;
                Evento.preventDefault();
                if (Evento.repeat || Evento.ctrlKey || Evento.altKey || Evento.metaKey || Evento.shiftKey) return;
                if (!Campo.checkValidity()) {{
                    Campo.reportValidity();
                    return;
                }}
                const Campos = ObterCamposVisiveis();
                const Proximo = Campo === CampoCodigo ? document.getElementById("id_Nome") : Campos[Campos.indexOf(Campo) + 1];
                (Proximo || Formulario.querySelector('button[type="submit"]')).focus();
            }});
        }})();
    </script>
    """

    return HttpResponse(
        RenderizarLayoutBase(
            Titulo,
            ConteudoPrincipal + ObterScriptConsultaCatalogoProduto(
                ConsultarInicial=Request.method == "GET" and bool(Request.GET.get("codigo", "").strip()),
            ),
            RotaAtiva="estoque",
            Request=Request,
        )
    )


@ExigirPost
def ComponenteExcluirProduto(Request, ProdutoId):
    ProdutoExcluido = get_object_or_404(Produto, pk=ProdutoId, Ativo=True)
    ProdutoExcluido.Ativo = False
    ProdutoExcluido.Disponivel = False
    ProdutoExcluido.save(update_fields=["Ativo", "Disponivel"])
    ProdutoExcluido.LotesEstoque.update(Ativo=False, Disponivel=False)
    DefinirMensagemProduto(
        Request,
        f"{ProdutoExcluido.Nome} foi removido do estoque.",
    )
    return redirect("Estoque")


@ExigirPost
def ComponenteEncerrarLote(Request, ProdutoId, LoteId):
    ProdutoEdicao = get_object_or_404(Produto, pk=ProdutoId, Ativo=True)
    Lote = get_object_or_404(
        LoteEstoque,
        pk=LoteId,
        Produto=ProdutoEdicao,
        Ativo=True,
    )
    Lote.Ativo = False
    Lote.Disponivel = False
    Lote.save(update_fields=["Ativo", "Disponivel"])
    ProdutoEdicao.SincronizarResumoLotes()
    DefinirMensagemProduto(
        Request,
        f"Lote #{Lote.ObterNumeroNoProduto()} encerrado. O restante do estoque continua disponível.",
    )
    return redirect("EditarProduto", ProdutoId=ProdutoEdicao.id)


@ExigirPost
def ComponenteAtualizarDataLote(Request, ProdutoId, LoteId):
    ProdutoEdicao = get_object_or_404(Produto, pk=ProdutoId, Ativo=True)
    Lote = get_object_or_404(
        LoteEstoque,
        pk=LoteId,
        Produto=ProdutoEdicao,
    )

    try:
        DataEntrada = date.fromisoformat(Request.POST.get("DataEntrada", ""))
    except ValueError:
        DefinirMensagemProduto(Request, "Informe uma data de entrada válida.", "erro")
        return redirect("EditarProduto", ProdutoId=ProdutoEdicao.id)

    if DataEntrada > timezone.localdate():
        DefinirMensagemProduto(
            Request,
            "A data de entrada não pode estar no futuro.",
            "erro",
        )
        return redirect("EditarProduto", ProdutoId=ProdutoEdicao.id)

    DataAtual = timezone.localtime(Lote.CriadoEm)
    NovaData = DataAtual.replace(
        year=DataEntrada.year,
        month=DataEntrada.month,
        day=DataEntrada.day,
    )
    LoteEstoque.objects.filter(pk=Lote.pk).update(CriadoEm=NovaData)
    DefinirMensagemProduto(
        Request,
        f"Data do lote #{Lote.ObterNumeroNoProduto()} atualizada.",
    )
    return redirect("EditarProduto", ProdutoId=ProdutoEdicao.id)


@ExigirPost
def ComponenteAtualizarValidadeLote(Request, ProdutoId, LoteId):
    ProdutoEdicao = get_object_or_404(Produto, pk=ProdutoId, Ativo=True)
    Lote = get_object_or_404(LoteEstoque, pk=LoteId, Produto=ProdutoEdicao)
    Formulario = FormularioValidadeLote(Request.POST, instance=Lote)

    if Formulario.is_valid():
        Formulario.save()
        DefinirMensagemProduto(Request, f"Validade do lote #{Lote.Numero} atualizada.")
    else:
        DefinirMensagemProduto(Request, "Informe uma data de validade válida.", "erro")

    return redirect("EditarProduto", ProdutoId=ProdutoEdicao.id)


@ExigirPost
def ComponenteExcluirLote(Request, ProdutoId, LoteId):
    ProdutoEdicao = get_object_or_404(Produto, pk=ProdutoId, Ativo=True)
    Lote = get_object_or_404(
        LoteEstoque,
        pk=LoteId,
        Produto=ProdutoEdicao,
    )
    NumeroLote = Lote.Numero

    if Lote.ItensVendidos.exists():
        DefinirMensagemProduto(
            Request,
            f"O lote #{NumeroLote} possui vendas registradas e não pode ser excluído. Use Encerrar para preservar o histórico.",
            "erro",
        )
        return redirect("EditarProduto", ProdutoId=ProdutoEdicao.id)

    Lote.delete()
    ProdutoEdicao.SincronizarResumoLotes()
    DefinirMensagemProduto(Request, f"Lote #{NumeroLote} excluído do estoque.")
    return redirect("EditarProduto", ProdutoId=ProdutoEdicao.id)
