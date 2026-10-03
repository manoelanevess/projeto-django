"""Componentes de cadastro e manutenção de produtos."""
from html import escape

from django.http import HttpResponse
from django.middleware.csrf import get_token as ObterTokenCsrf
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST as ExigirPost

from componentes.LayoutBase import RenderizarLayoutBase

from .FormularioProduto import FormularioProduto
from .models import Produto


ChaveMensagemProduto = "MensagemProduto"


def DefinirMensagemProduto(Request, Texto, Tipo="sucesso"):
    Request.session[ChaveMensagemProduto] = {"Texto": Texto, "Tipo": Tipo}


def ConsumirMensagemProduto(Request):
    return Request.session.pop(ChaveMensagemProduto, None)


def ComponenteRedirecionarProdutos(Request):
    return redirect("Estoque")


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


def ComponenteFormularioProduto(Request, ProdutoId=None):
    ProdutoEdicao = None

    if ProdutoId is not None:
        ProdutoEdicao = get_object_or_404(Produto, pk=ProdutoId, Ativo=True)

    if Request.method == "POST":
        Formulario = FormularioProduto(Request.POST, instance=ProdutoEdicao)

        if Formulario.is_valid():
            ProdutoSalvo = Formulario.save()
            Acao = "atualizado" if ProdutoEdicao else "cadastrado"
            DefinirMensagemProduto(
                Request,
                f"{ProdutoSalvo.Nome} foi {Acao} com sucesso.",
            )
            return redirect("Estoque")
    else:
        Formulario = FormularioProduto(instance=ProdutoEdicao)

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
        .GrupoCampo .CampoFormulario {{ width: 100%; }}
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

        [hidden] {{ display: none !important; }}
    </style>

    <div class="CabecalhoFormulario">
        <h1>{Titulo}</h1>
        <a class="BotaoSecundario" href="/estoque">Voltar ao estoque</a>
    </div>

    <form class="PainelFormulario" method="post">
        <input type="hidden" name="csrfmiddlewaretoken" value="{TokenCsrf}">
        {ErrosGerais}
        {AvisoFornecedor}

        <div class="GradeFormulario">
            {RenderizarCampo(Formulario, "Nome", "Nome do produto")}
            {RenderizarCampo(Formulario, "Categoria", "Categoria", "Ex.: Alimentos, ferramentas ou papelaria.")}
            {RenderizarCampo(Formulario, "Marca", "Marca", "Opcional para produtos sem marca definida.")}
            {RenderizarCampo(Formulario, "Fornecedor", "Fornecedor", "Escolha um fornecedor cadastrado na área Fornecedores.")}
            {RenderizarCampo(Formulario, "PrecoCusto", "Preço de custo (R$)")}
            {RenderizarCampo(Formulario, "PrecoVenda", "Preço de venda (R$)")}
            {RenderizarCampo(Formulario, "UnidadeVenda", "Forma de venda")}
            {RenderizarCampo(Formulario, "QuantidadeEstoque", "Quantidade em estoque")}
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
        }})();
    </script>
    """

    return HttpResponse(
        RenderizarLayoutBase(Titulo, ConteudoPrincipal, RotaAtiva="estoque")
    )


@ExigirPost
def ComponenteExcluirProduto(Request, ProdutoId):
    ProdutoExcluido = get_object_or_404(Produto, pk=ProdutoId, Ativo=True)
    ProdutoExcluido.Ativo = False
    ProdutoExcluido.Disponivel = False
    ProdutoExcluido.save(update_fields=["Ativo", "Disponivel"])
    DefinirMensagemProduto(
        Request,
        f"{ProdutoExcluido.Nome} foi removido do estoque.",
    )
    return redirect("Estoque")
