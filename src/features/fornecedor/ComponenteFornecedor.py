"""Componentes de cadastro e manutenção de fornecedores."""
from html import escape

from django.http import HttpResponse
from django.middleware.csrf import get_token as ObterTokenCsrf
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST as ExigirPost

from componentes.LayoutBase import RenderizarLayoutBase

from .ApiFornecedor import BuscarFornecedores
from .FormularioFornecedor import FormularioFornecedor
from .models import Fornecedor


ChaveMensagemFornecedor = "MensagemFornecedor"


def DefinirMensagemFornecedor(Request, Texto, Tipo="sucesso"):
    Request.session[ChaveMensagemFornecedor] = {"Texto": Texto, "Tipo": Tipo}


def ConsumirMensagemFornecedor(Request):
    return Request.session.pop(ChaveMensagemFornecedor, None)


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
    <div class="GrupoCampo">
        <label for="{Campo.id_for_label}">{escape(Rotulo)}</label>
        {Campo}
        {DescricaoHtml}
        {RenderizarErrosCampo(Formulario, NomeCampo)}
    </div>
    """


def ComponenteFornecedores(Request):
    Busca = Request.GET.get("busca", "").strip()
    Fornecedores = list(BuscarFornecedores(Busca))
    TokenCsrf = ObterTokenCsrf(Request)
    Mensagem = ConsumirMensagemFornecedor(Request)
    MensagemHtml = ""

    if Mensagem:
        TipoMensagem = "Erro" if Mensagem.get("Tipo") == "erro" else "Sucesso"
        MensagemHtml = (
            f'<div class="MensagemOperacao {TipoMensagem}" role="status">'
            f'{escape(Mensagem.get("Texto", ""))}</div>'
        )

    if Fornecedores:
        LinhasFornecedores = []

        for FornecedorEstoque in Fornecedores:
            Contato = FornecedorEstoque.Email or FornecedorEstoque.Telefone or "Não informado"
            QuantidadeProdutos = (
                FornecedorEstoque.LotesEstoque.filter(
                    Produto__Ativo=True,
                    Ativo=True,
                )
                .values("Produto_id")
                .distinct()
                .count()
            )
            LinhasFornecedores.append(
                f"""
                <tr>
                    <td><strong>{escape(FornecedorEstoque.Nome)}</strong></td>
                    <td>{escape(Contato)}</td>
                    <td>{escape(FornecedorEstoque.Cidade or 'Não informada')}</td>
                    <td>{QuantidadeProdutos}</td>
                    <td>
                        <div class="AcoesFornecedor">
                            <a
                                class="BotaoIcone Editar"
                                href="/fornecedores/{FornecedorEstoque.id}/editar"
                                aria-label="Editar {escape(FornecedorEstoque.Nome)}"
                                title="Editar fornecedor"
                            >&#9998;</a>
                            <form
                                method="post"
                                action="/fornecedores/{FornecedorEstoque.id}/excluir"
                                onsubmit="return confirm('Inativar este fornecedor?');"
                            >
                                <input type="hidden" name="csrfmiddlewaretoken" value="{TokenCsrf}">
                                <button
                                    class="BotaoIcone Excluir"
                                    type="submit"
                                    aria-label="Inativar {escape(FornecedorEstoque.Nome)}"
                                    title="Inativar fornecedor"
                                >&#128465;</button>
                            </form>
                        </div>
                    </td>
                </tr>
                """
            )

        ResultadoFornecedores = f"""
        <section class="PainelTabela" aria-label="Fornecedores cadastrados">
            <table>
                <thead>
                    <tr>
                        <th>Fornecedor</th>
                        <th>Contato</th>
                        <th>Cidade</th>
                        <th>Produtos</th>
                        <th><span class="SomenteLeitorTela">Ações</span></th>
                    </tr>
                </thead>
                <tbody>{''.join(LinhasFornecedores)}</tbody>
            </table>
        </section>
        """
    else:
        ResultadoFornecedores = """
        <section class="EstadoVazio">
            <h2>Nenhum fornecedor encontrado</h2>
            <p>Altere a pesquisa ou cadastre um fornecedor para vinculá-lo aos produtos.</p>
            <a class="BotaoPrimario" href="/fornecedores/novo">Adicionar fornecedor</a>
            <a class="BotaoSecundario" href="/fornecedores">Limpar pesquisa</a>
        </section>
        """

    ConteudoPrincipal = f"""
    <style>
        .CabecalhoFornecedores {{
            margin-bottom: 18px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 16px;
        }}
        .CabecalhoFornecedores h1 {{ margin: 0; }}
        .MensagemOperacao {{
            margin-bottom: 18px;
            padding: 12px 14px;
            border-left: 4px solid;
            border-radius: 4px;
        }}
        .MensagemOperacao.Sucesso {{ border-color: #14866d; color: #0c614f; background: #e7f7f2; }}
        .MensagemOperacao.Erro {{ border-color: #c53b32; color: #8b241e; background: #fff0ef; }}
        .AcoesFornecedor {{ display: flex; justify-content: flex-end; gap: 6px; }}
        .AcoesFornecedor form {{ margin: 0; }}
        .BotaoIcone {{
            width: 34px;
            height: 34px;
            padding: 0;
            border: 1px solid;
            border-radius: 4px;
            display: grid;
            place-items: center;
            text-decoration: none;
            font-size: 17px;
            cursor: pointer;
        }}
        .BotaoIcone.Editar {{ border-color: #b8d9ea; color: #056da8; background: #e5f3fa; }}
        .BotaoIcone.Excluir {{ border-color: #efc5c1; color: #a12c25; background: #fff0ef; }}
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
    </style>

    <div class="CabecalhoFornecedores">
        <h1>Fornecedores</h1>
        <a class="BotaoPrimario" href="/fornecedores/novo">+ Adicionar fornecedor</a>
    </div>

    {MensagemHtml}

    <form class="BarraFiltros" method="get" action="/fornecedores">
        <input
            class="CampoFormulario"
            type="search"
            name="busca"
            value="{escape(Busca)}"
            placeholder="Nome, contato ou cidade"
            aria-label="Pesquisar fornecedor"
        >
        <button class="BotaoPrimario" type="submit">Pesquisar</button>
        <a class="BotaoSecundario" href="/fornecedores">Limpar</a>
    </form>

    {ResultadoFornecedores}
    """

    return HttpResponse(
        RenderizarLayoutBase(
            "Fornecedores",
            ConteudoPrincipal,
            RotaAtiva="fornecedores",
        )
    )


def ComponenteFormularioFornecedor(Request, FornecedorId=None):
    FornecedorEdicao = None

    if FornecedorId is not None:
        FornecedorEdicao = get_object_or_404(
            Fornecedor,
            pk=FornecedorId,
            Ativo=True,
        )

    if Request.method == "POST":
        Formulario = FormularioFornecedor(Request.POST, instance=FornecedorEdicao)

        if Formulario.is_valid():
            FornecedorSalvo = Formulario.save()
            Acao = "atualizado" if FornecedorEdicao else "cadastrado"
            DefinirMensagemFornecedor(
                Request,
                f"{FornecedorSalvo.Nome} foi {Acao} com sucesso.",
            )
            return redirect("Fornecedores")
    else:
        Formulario = FormularioFornecedor(instance=FornecedorEdicao)

    Titulo = "Editar fornecedor" if FornecedorEdicao else "Adicionar fornecedor"
    TextoBotao = "Salvar alterações" if FornecedorEdicao else "Cadastrar fornecedor"
    TokenCsrf = ObterTokenCsrf(Request)
    ErrosGerais = "".join(
        f'<div class="MensagemFormulario Erro">{escape(str(Erro))}</div>'
        for Erro in Formulario.non_field_errors()
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
        .GrupoCampo label {{
            display: block;
            margin-bottom: 7px;
            color: #3f4f5f;
            font-size: 13px;
            font-weight: 700;
        }}
        .GrupoCampo .CampoFormulario {{ width: 100%; }}
        .AjudaCampo,
        .ErroCampo {{ display: block; margin-top: 6px; font-size: 13px; }}
        .AjudaCampo {{ color: #667482; }}
        .ErroCampo {{ color: #a12c25; }}
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
    </style>

    <div class="CabecalhoFormulario">
        <h1>{Titulo}</h1>
        <a class="BotaoSecundario" href="/fornecedores">Voltar aos fornecedores</a>
    </div>

    <form class="PainelFormulario" method="post">
        <input type="hidden" name="csrfmiddlewaretoken" value="{TokenCsrf}">
        {ErrosGerais}
        <div class="GradeFormulario">
            {RenderizarCampo(Formulario, "Nome", "Nome do fornecedor")}
            {RenderizarCampo(Formulario, "Telefone", "Telefone")}
            {RenderizarCampo(Formulario, "Email", "E-mail")}
            {RenderizarCampo(Formulario, "Cidade", "Cidade")}
        </div>
        <div class="AcoesFormulario">
            <a class="BotaoSecundario" href="/fornecedores">Cancelar</a>
            <button class="BotaoPrimario" type="submit">{TextoBotao}</button>
        </div>
    </form>
    """

    return HttpResponse(
        RenderizarLayoutBase(Titulo, ConteudoPrincipal, RotaAtiva="fornecedores")
    )


@ExigirPost
def ComponenteExcluirFornecedor(Request, FornecedorId):
    FornecedorExcluido = get_object_or_404(
        Fornecedor,
        pk=FornecedorId,
        Ativo=True,
    )
    FornecedorExcluido.Ativo = False
    FornecedorExcluido.save(update_fields=["Ativo"])
    DefinirMensagemFornecedor(
        Request,
        f"{FornecedorExcluido.Nome} foi inativado. Seus produtos foram preservados.",
    )
    return redirect("Fornecedores")
