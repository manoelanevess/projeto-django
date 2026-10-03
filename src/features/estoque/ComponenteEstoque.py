"""Componente da tela unificada de produtos e controle de estoque."""
from html import escape

from django.http import HttpResponse
from django.middleware.csrf import get_token as ObterTokenCsrf

from componentes.LayoutBase import RenderizarLayoutBase
from features.fornecedor.ApiFornecedor import BuscarFornecedoresParaFiltroEstoque
from features.produtos.ApiProduto import BuscarCategoriasProdutos
from features.produtos.ComponenteProduto import ConsumirMensagemProduto
from features.produtos.LogicaProduto import GerarResumoProdutos


def RenderizarOpcoesCategorias(Categorias, CategoriaSelecionada):
    Opcoes = ['<option value="">Todas as categorias</option>']

    for Categoria in Categorias:
        CategoriaSegura = escape(Categoria)
        Selecionada = " selected" if Categoria == CategoriaSelecionada else ""
        Opcoes.append(
            f'<option value="{CategoriaSegura}"{Selecionada}>{CategoriaSegura}</option>'
        )

    return "".join(Opcoes)


def RenderizarOpcoesFornecedores(Fornecedores, FornecedorSelecionado):
    Opcoes = ['<option value="">Todos os fornecedores</option>']

    for FornecedorEstoque in Fornecedores:
        Identificador = str(FornecedorEstoque.id)
        Selecionado = " selected" if Identificador == FornecedorSelecionado else ""
        Opcoes.append(
            f'<option value="{Identificador}"{Selecionado}>'
            f'{escape(FornecedorEstoque.Nome)}</option>'
        )

    return "".join(Opcoes)


def RenderizarProdutos(Produtos, TokenCsrf):
    if not Produtos:
        return """
        <section class="EstadoVazio">
            <h2>Nenhum produto encontrado</h2>
            <p>Altere os filtros ou cadastre o primeiro produto do estoque.</p>
            <a class="BotaoPrimario" href="/estoque/novo">Adicionar produto</a>
            <a class="BotaoSecundario" href="/estoque">Limpar filtros</a>
        </section>
        """

    LinhasProdutos = []

    for ProdutoEstoque in Produtos:
        if not ProdutoEstoque["Disponivel"]:
            ClasseSituacao = "Indisponivel"
            Situacao = "Indisponível"
        elif ProdutoEstoque["EstoqueBaixo"]:
            ClasseSituacao = "Alerta"
            Situacao = "Estoque baixo"
        else:
            ClasseSituacao = "Disponivel"
            Situacao = "Disponível"
        EstoqueMinimo = ""

        if ProdutoEstoque["ControlaQuantidade"]:
            EstoqueMinimo = (
                f'<small>Mínimo: {escape(ProdutoEstoque["EstoqueMinimoFormatado"])} '
                f'{escape(ProdutoEstoque["Unidade"])}</small>'
            )

        LinhasProdutos.append(
            f"""
            <tr>
                <td class="DadosProduto">
                    <strong>{escape(ProdutoEstoque["Nome"])}</strong>
                </td>
                <td>{escape(ProdutoEstoque["Marca"])}</td>
                <td>{escape(ProdutoEstoque["Categoria"])}</td>
                <td>{escape(ProdutoEstoque["Fornecedor"])}</td>
                <td>{escape(ProdutoEstoque["TipoVenda"])}</td>
                <td class="DadosEstoque">
                    <span>{escape(ProdutoEstoque["EstoqueDescricao"])}</span>
                    {EstoqueMinimo}
                </td>
                <td>R$ {escape(ProdutoEstoque["PrecoCustoFormatado"])}</td>
                <td>R$ {escape(ProdutoEstoque["PrecoVendaFormatado"])}</td>
                <td><span class="SituacaoProduto {ClasseSituacao}">{Situacao}</span></td>
                <td>
                    <div class="AcoesProduto">
                        <a
                            class="BotaoIcone Editar"
                            href="/estoque/{ProdutoEstoque['Id']}/editar"
                            aria-label="Editar {escape(ProdutoEstoque['Nome'])}"
                            title="Editar produto"
                        >&#9998;</a>
                        <form
                            method="post"
                            action="/estoque/{ProdutoEstoque['Id']}/excluir"
                            onsubmit="return confirm('Remover este produto do estoque?');"
                        >
                            <input type="hidden" name="csrfmiddlewaretoken" value="{TokenCsrf}">
                            <button
                                class="BotaoIcone Excluir"
                                type="submit"
                                aria-label="Excluir {escape(ProdutoEstoque['Nome'])}"
                                title="Excluir produto"
                            >&#128465;</button>
                        </form>
                    </div>
                </td>
            </tr>
            """
        )

    return f"""
    <section class="PainelTabela TabelaEstoque" aria-label="Produtos do estoque">
        <table>
            <thead>
                <tr>
                    <th>Produto</th>
                    <th>Marca</th>
                    <th>Categoria</th>
                    <th>Fornecedor</th>
                    <th>Venda</th>
                    <th>Estoque</th>
                    <th>Preço de custo</th>
                    <th>Preço de venda</th>
                    <th>Situação</th>
                    <th><span class="SomenteLeitorTela">Ações</span></th>
                </tr>
            </thead>
            <tbody>{''.join(LinhasProdutos)}</tbody>
        </table>
    </section>
    """


def ComponenteEstoque(Request):
    Busca = Request.GET.get("busca", "").strip()
    Estoque = Request.GET.get("estoque", "").strip()
    Categoria = Request.GET.get("categoria", "").strip()
    Fornecedor = Request.GET.get("fornecedor", "").strip()
    ResumoProdutos = GerarResumoProdutos(
        Busca=Busca,
        Estoque=Estoque,
        Categoria=Categoria,
        Fornecedor=Fornecedor,
    )
    TokenCsrf = ObterTokenCsrf(Request)
    ProdutosHtml = RenderizarProdutos(ResumoProdutos["Produtos"], TokenCsrf)
    OpcoesCategorias = RenderizarOpcoesCategorias(
        BuscarCategoriasProdutos(),
        Categoria,
    )
    OpcoesFornecedores = RenderizarOpcoesFornecedores(
        BuscarFornecedoresParaFiltroEstoque(),
        Fornecedor,
    )
    Mensagem = ConsumirMensagemProduto(Request)
    MensagemHtml = ""

    if Mensagem:
        TipoMensagem = "Erro" if Mensagem.get("Tipo") == "erro" else "Sucesso"
        MensagemHtml = (
            f'<div class="MensagemOperacao {TipoMensagem}" role="status">'
            f'{escape(Mensagem.get("Texto", ""))}</div>'
        )

    OpcoesEstoque = {
        "": "Todos os produtos",
        "disponivel": "Disponíveis",
        "baixo": "Estoque baixo",
        "indisponivel": "Indisponíveis",
    }
    OpcoesEstoqueHtml = "".join(
        f'<option value="{Valor}"{" selected" if Estoque == Valor else ""}>{Rotulo}</option>'
        for Valor, Rotulo in OpcoesEstoque.items()
    )

    ConteudoPrincipal = f"""
    <style>
        .CabecalhoEstoque {{
            margin-bottom: 18px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 16px;
        }}
        .CabecalhoEstoque h1 {{ margin: 0; }}
        .BarraFiltrosEstoque {{
            display: grid;
            grid-template-columns: minmax(200px, 1fr) 195px 215px 180px auto auto;
        }}
        .BarraFiltrosEstoque .CampoFormulario {{ min-width: 0; width: 100%; }}

        .MensagemOperacao {{
            margin-bottom: 18px;
            padding: 12px 14px;
            border-left: 4px solid;
            border-radius: 4px;
        }}
        .MensagemOperacao.Sucesso {{ border-color: #14866d; color: #0c614f; background: #e7f7f2; }}
        .MensagemOperacao.Erro {{ border-color: #c53b32; color: #8b241e; background: #fff0ef; }}

        .TabelaEstoque {{ overflow-x: auto; }}
        .TabelaEstoque table {{ min-width: 1060px; }}
        .DadosProduto strong,
        .DadosProduto small,
        .DadosEstoque span,
        .DadosEstoque small {{ display: block; }}
        .DadosProduto small,
        .DadosEstoque small {{ margin-top: 4px; color: #667482; }}

        .SituacaoProduto {{
            display: inline-flex;
            min-height: 26px;
            padding: 0 9px;
            align-items: center;
            border-radius: 999px;
            font-size: 12px;
            font-weight: 700;
        }}
        .SituacaoProduto.Disponivel {{ color: #0c614f; background: #dff4ed; }}
        .SituacaoProduto.Alerta {{ color: #8a5200; background: #fff1d6; }}
        .SituacaoProduto.Indisponivel {{ color: #8b241e; background: #fde9e7; }}

        .AcoesProduto {{ display: flex; justify-content: flex-end; gap: 6px; }}
        .AcoesProduto form {{ margin: 0; }}
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
        .BotaoIcone:hover,
        .BotaoIcone:focus-visible {{ outline: 2px solid rgba(7, 132, 202, 0.2); outline-offset: 1px; }}

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

    <div class="CabecalhoEstoque">
        <h1>Estoque</h1>
        <a class="BotaoPrimario" href="/estoque/novo">+ Adicionar produto</a>
    </div>

    {MensagemHtml}

    <form class="BarraFiltros BarraFiltrosEstoque" method="get" action="/estoque">
        <input
            class="CampoFormulario"
            type="search"
            name="busca"
            value="{escape(Busca)}"
            placeholder="Produto, marca ou fornecedor"
            aria-label="Buscar produto, marca ou fornecedor"
        >
        <select class="CampoFormulario" name="categoria" aria-label="Filtrar por categoria">
            {OpcoesCategorias}
        </select>
        <select class="CampoFormulario" name="fornecedor" aria-label="Filtrar por fornecedor">
            {OpcoesFornecedores}
        </select>
        <select class="CampoFormulario" name="estoque" aria-label="Filtrar pela situação do estoque">
            {OpcoesEstoqueHtml}
        </select>
        <button class="BotaoPrimario" type="submit">Filtrar</button>
        <a class="BotaoSecundario" href="/estoque">Limpar</a>
    </form>

    <section class="GridIndicadores" aria-label="Indicadores do estoque">
        <article class="CardIndicador" style="--CorDestaque: #2d74d8;">
            <div>
                <strong>Produtos encontrados</strong>
                <span>{ResumoProdutos["TotalProdutos"]}</span>
            </div>
            <div class="IconeIndicador" aria-hidden="true">QT</div>
        </article>

        <article class="CardIndicador" style="--CorDestaque: #00a889;">
            <div>
                <strong>Disponíveis para venda</strong>
                <span>{ResumoProdutos["TotalProdutosDisponiveis"]}</span>
            </div>
            <div class="IconeIndicador" aria-hidden="true">OK</div>
        </article>

        <article class="CardIndicador" style="--CorDestaque: #f59f18;">
            <div>
                <strong>Produtos em alerta</strong>
                <span>{ResumoProdutos["TotalEstoqueBaixo"]}</span>
            </div>
            <div class="IconeIndicador" aria-hidden="true">!</div>
        </article>
    </section>

    {ProdutosHtml}
    """

    return HttpResponse(
        RenderizarLayoutBase("Estoque", ConteudoPrincipal, RotaAtiva="estoque")
    )
