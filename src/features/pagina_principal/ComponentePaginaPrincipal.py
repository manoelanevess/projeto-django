"""Componente da Página Principal orientada ao atendimento."""
import json
from html import escape

from django.http import HttpResponse
from django.middleware.csrf import get_token as ObterTokenCsrf

from componentes.LayoutBase import RenderizarLayoutBase
from features.vendas.ComponenteCarrinho import ConsumirMensagem
from features.vendas.LogicaCarrinho import NumerosCarrinhos

from .LogicaPaginaPrincipal import GerarDadosPaginaPrincipal


def ObterCarrinhosAbertos(Request):
    return list(NumerosCarrinhos)


def RenderizarCartoesCarrinhos(ResumosCarrinhos, CarrinhosAbertos):
    return "".join(
        f"""
        <article class="CartaoAtendimento">
            <button
                class="ConteudoCartaoAtendimento{' Aberto' if Resumo['Numero'] in CarrinhosAbertos else ''}"
                type="button"
                data-abrir-carrinho="{Resumo['Numero']}"
                aria-controls="PainelCarrinho-{Resumo['Numero']}"
                aria-expanded="{'true' if Resumo['Numero'] in CarrinhosAbertos else 'false'}"
            >
                <span>{escape(Resumo['Nome'])}</span>
                <strong>R$ {Resumo['TotalFormatado']}</strong>
                <small>{Resumo['QuantidadeProdutos']} produtos</small>
            </button>
            <button
                class="BotaoEditarNomeCarrinho"
                type="button"
                data-editar-nome
                data-carrinho="{Resumo['Numero']}"
                data-nome-personalizado="{escape(Resumo['NomePersonalizado'])}"
                aria-label="Editar nome do carrinho {Resumo['Numero']}"
                title="Editar nome do cliente"
            >&#9998;</button>
        </article>
        """
        for Resumo in ResumosCarrinhos
    )


def RenderizarCamposRetorno(TokenCsrf, NumeroCarrinho, CarrinhosAbertos):
    return f"""
    <input type="hidden" name="csrfmiddlewaretoken" value="{TokenCsrf}">
    <input type="hidden" name="carrinho" value="{NumeroCarrinho}">
    <input type="hidden" name="retorno" value="pagina-principal">
    <input class="CampoCarrinhosAbertos" type="hidden" name="carrinhos_abertos" value="{CarrinhosAbertos}">
    """


def RenderizarItensPainel(ResumoCarrinho, TokenCsrf, CarrinhosAbertos):
    NumeroCarrinho = ResumoCarrinho["Numero"]

    if not ResumoCarrinho["Itens"]:
        return """
        <div class="PainelCarrinhoVazio">
            <strong>Carrinho vazio</strong>
            <span>Pesquise um produto para começar.</span>
        </div>
        """

    LinhasItens = []

    for Item in ResumoCarrinho["Itens"]:
        ProdutoVenda = Item["Produto"]
        LoteVenda = Item["Lote"]
        CamposRetorno = RenderizarCamposRetorno(
            TokenCsrf,
            NumeroCarrinho,
            CarrinhosAbertos,
        )
        LinhasItens.append(
            f"""
            <div class="ItemPainelCarrinho">
                <div>
                    <div class="LinhaNomeProduto">
                        <strong>{escape(ProdutoVenda.Nome)}</strong>
                        <span class="MarcaProduto">{escape(ProdutoVenda.Marca or 'Sem marca')}</span>
                    </div>
                    <small>Lote #{Item['NumeroLote']} · {escape(LoteVenda.Fornecedor.Nome)}</small>
                    <small>{Item['QuantidadeFormatada']} {Item['Unidade']} × R$ {Item['PrecoFormatado']}</small>
                </div>
                <span>R$ {Item['SubtotalFormatado']}</span>
                <form method="post" action="/carrinho/remover">
                    {CamposRetorno}
                    <input type="hidden" name="item" value="{escape(Item['ChaveItem'])}">
                    <button class="BotaoRemoverPainel" type="submit" aria-label="Remover {escape(ProdutoVenda.Nome)}">×</button>
                </form>
            </div>
            """
        )

    return f'<div class="ListaItensPainel">{"".join(LinhasItens)}</div>'


def RenderizarPagamentoPainel(ResumoCarrinho, TokenCsrf, CarrinhosAbertos):
    if not ResumoCarrinho["Itens"]:
        return ""

    NumeroCarrinho = ResumoCarrinho["Numero"]
    CamposRetorno = RenderizarCamposRetorno(
        TokenCsrf,
        NumeroCarrinho,
        CarrinhosAbertos,
    )

    return f"""
    <section class="PagamentoPainel" aria-label="Pagamento do carrinho {NumeroCarrinho}">
        <form
            method="post"
            action="/carrinho/concluir"
            data-formulario-pagamento
            data-total="{ResumoCarrinho['Total']}"
        >
            {CamposRetorno}
            <fieldset>
                <legend>Pagamento</legend>
                <label>
                    <input type="radio" name="forma_pagamento" value="dinheiro" checked>
                    Dinheiro
                </label>
                <label>
                    <input type="radio" name="forma_pagamento" value="pix">
                    PIX
                </label>
                <label>
                    <input type="radio" name="forma_pagamento" value="conta_cliente">
                    Conta do cliente
                </label>
            </fieldset>

            <div class="DinheiroPainel" data-area-dinheiro>
                <label for="ValorRecebido-{NumeroCarrinho}">Valor recebido</label>
                <input
                    id="ValorRecebido-{NumeroCarrinho}"
                    class="CampoFormulario"
                    name="valor_recebido"
                    type="text"
                    inputmode="decimal"
                    placeholder="R$ 0,00"
                    autocomplete="off"
                    data-valor-recebido
                    required
                >
                <div class="TrocoPainel">
                    <span>Troco</span>
                    <output data-troco>R$ 0,00</output>
                </div>
            </div>

            <button class="BotaoConcluirPainel" type="submit">Concluir compra</button>
        </form>

        <form method="post" action="/carrinho/cancelar" onsubmit="return confirm('Cancelar este carrinho?');">
            {CamposRetorno}
            <button class="BotaoCancelarPainel" type="submit">Cancelar carrinho</button>
        </form>
    </section>
    """


def RenderizarPaineisCarrinhos(
    ResumosCarrinhos,
    CarrinhosAbertos,
    TokenCsrf,
):
    NumerosAbertos = ",".join(CarrinhosAbertos)
    Paineis = []

    for Resumo in ResumosCarrinhos:
        Numero = Resumo["Numero"]
        ItensPainel = RenderizarItensPainel(
            Resumo,
            TokenCsrf,
            NumerosAbertos,
        )
        PagamentoPainel = RenderizarPagamentoPainel(
            Resumo,
            TokenCsrf,
            NumerosAbertos,
        )
        Paineis.append(
            f"""
            <aside
                class="PainelCarrinhoFlutuante"
                id="PainelCarrinho-{Numero}"
                data-painel-carrinho="{Numero}"
            >
                <header class="CabecalhoPainelCarrinho">
                    <div>
                        <span>Carrinho {Numero}</span>
                        <div class="TituloNomeCarrinho">
                            <h2>{escape(Resumo['Nome'])}</h2>
                            <button
                                class="BotaoEditarNomePainel"
                                type="button"
                                data-editar-nome
                                data-carrinho="{Numero}"
                                data-nome-personalizado="{escape(Resumo['NomePersonalizado'])}"
                                aria-label="Editar nome do carrinho {Numero}"
                                title="Editar nome do cliente"
                            >&#9998;</button>
                        </div>
                    </div>
                </header>

                <section class="AdicionarProdutoPainel">
                    <label for="BuscaCarrinho-{Numero}">Adicionar produtos</label>
                    <input
                        id="BuscaCarrinho-{Numero}"
                        class="CampoFormulario"
                        type="search"
                        placeholder="Pesquisar arroz, feijão..."
                        autocomplete="off"
                        data-busca-produto="{Numero}"
                    >
                    <div class="ResultadosPainel" data-resultados-produtos="{Numero}"></div>
                </section>

                {ItensPainel}

                <div class="TotalPainelCarrinho">
                    <span>Total</span>
                    <strong>R$ {Resumo['TotalFormatado']}</strong>
                </div>

                {PagamentoPainel}
                <a class="LinkCarrinhoCompleto" href="/carrinho?carrinho={Numero}">Abrir carrinho completo</a>
            </aside>
            """
        )

    return "".join(Paineis)


def RenderizarConsultaEstoque(ConsultaEstoque):
    if not ConsultaEstoque["Produtos"]:
        return """
        <section class="EstadoVazio">
            <h2>Nenhum produto encontrado</h2>
            <p>Confira o termo pesquisado ou o cadastro em Estoque.</p>
        </section>
        """

    Linhas = "".join(
        f"""
        <tr>
            <td><strong>{escape(ProdutoEstoque['Nome'])}</strong></td>
            <td>{escape(ProdutoEstoque['Marca'])}</td>
            <td>{escape(ProdutoEstoque['Categoria'])}</td>
            <td>{escape(ProdutoEstoque['Fornecedor'])}</td>
            <td>{escape(ProdutoEstoque['EstoqueDescricao'])}</td>
            <td>R$ {ProdutoEstoque['PrecoCustoFormatado']}</td>
            <td>R$ {ProdutoEstoque['PrecoVendaFormatado']} / {ProdutoEstoque['Unidade']}</td>
        </tr>
        """
        for ProdutoEstoque in ConsultaEstoque["Produtos"]
    )

    return f"""
    <section class="PainelTabela" aria-label="Consulta do estoque">
        <table>
            <thead>
                <tr>
                    <th>Produto</th>
                    <th>Marca</th>
                    <th>Categoria</th>
                    <th>Fornecedor</th>
                    <th>Disponível</th>
                    <th>Preço de custo</th>
                    <th>Preço de venda</th>
                </tr>
            </thead>
            <tbody>{Linhas}</tbody>
        </table>
    </section>
    """


def ObterEstilosPaginaPrincipal():
    return """
    <style>
        .TituloSecao {
            margin: 24px 0 12px;
            display: flex;
            align-items: baseline;
            justify-content: space-between;
            gap: 12px;
        }

        .TituloAtendimentos { margin-top: 0; }
        .TituloSecao h2 { margin: 0; }
        .TituloSecao span { color: #667482; font-size: 13px; }

        .GradeAtendimentos {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 14px;
        }

        .CartaoAtendimento {
            position: relative;
            min-width: 0;
        }

        .ConteudoCartaoAtendimento {
            width: 100%;
            min-height: 104px;
            padding: 17px 54px 17px 17px;
            display: grid;
            align-content: center;
            gap: 6px;
            border: 1px solid #d6e0e6;
            border-radius: 6px;
            color: #26313d;
            background: #ffffff;
            text-align: left;
            font: inherit;
            cursor: pointer;
        }

        .ConteudoCartaoAtendimento:hover,
        .ConteudoCartaoAtendimento:focus-visible,
        .ConteudoCartaoAtendimento.Aberto {
            border-color: #0784ca;
            outline: 2px solid rgba(7, 132, 202, 0.15);
        }

        .ConteudoCartaoAtendimento span {
            overflow: hidden;
            color: #52616f;
            font-weight: 700;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .ConteudoCartaoAtendimento strong { color: #0784ca; font-size: 22px; }
        .ConteudoCartaoAtendimento small { color: #667482; }

        .BotaoEditarNomeCarrinho {
            position: absolute;
            z-index: 1;
            top: 12px;
            right: 12px;
            width: 34px;
            height: 34px;
            border: 1px solid #cad8e1;
            border-radius: 4px;
            color: #3f596a;
            background: #f4f8fa;
            font-size: 19px;
            cursor: pointer;
        }

        .BotaoEditarNomeCarrinho:hover,
        .BotaoEditarNomeCarrinho:focus-visible {
            border-color: #0784ca;
            color: #0784ca;
            outline: 2px solid rgba(7, 132, 202, 0.15);
        }

        .ConsultaEstoqueCabecalho {
            margin-bottom: 14px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 16px;
        }

        .ConsultaEstoqueCabecalho h2 { margin: 0; }
        .ConsultaEstoqueCabecalho .BarraFiltros { margin: 0; width: min(560px, 100%); }

        .AreaPaineisCarrinhos {
            width: 100%;
            margin-top: 14px;
            padding: 2px 2px 14px;
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            align-items: start;
            gap: 14px;
        }

        .PainelCarrinhoFlutuante {
            min-width: 0;
            max-height: 620px;
            overflow-y: auto;
            border: 1px solid #b8c8d2;
            border-radius: 6px;
            background: #ffffff;
            box-shadow: 0 18px 44px rgba(22, 43, 56, 0.24);
        }

        .CabecalhoPainelCarrinho {
            position: sticky;
            z-index: 2;
            top: 0;
            padding: 14px 16px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-bottom: 1px solid #d6e0e6;
            color: #ffffff;
            background: #0784ca;
        }

        .CabecalhoPainelCarrinho span { color: #d8f1ff; font-size: 11px; text-transform: uppercase; }
        .CabecalhoPainelCarrinho h2 { margin: 2px 0 0; font-size: 18px; }

        .TituloNomeCarrinho {
            display: flex;
            align-items: center;
            gap: 7px;
        }

        .TituloNomeCarrinho h2 {
            overflow: hidden;
            max-width: 210px;
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        .BotaoEditarNomePainel {
            width: 28px;
            height: 28px;
            border: 0;
            border-radius: 4px;
            color: #ffffff;
            background: rgba(255, 255, 255, 0.16);
            font-size: 17px;
            cursor: pointer;
        }

        .BotaoEditarNomePainel:hover,
        .BotaoEditarNomePainel:focus-visible {
            background: rgba(255, 255, 255, 0.28);
            outline: 2px solid rgba(255, 255, 255, 0.55);
        }

        .AdicionarProdutoPainel { padding: 15px; border-bottom: 1px solid #e0e7eb; }
        .AdicionarProdutoPainel > label {
            display: block;
            margin-bottom: 7px;
            color: #3f4f5f;
            font-size: 13px;
            font-weight: 700;
        }

        .ResultadosPainel { display: grid; gap: 7px; }
        .ResultadoProdutoPainel {
            margin-top: 8px;
            padding: 10px;
            display: grid;
            gap: 8px;
            border: 1px solid #d6e0e6;
            border-radius: 5px;
            background: #f8fafb;
        }

        .ResultadoProdutoPainel strong,
        .ResultadoProdutoPainel small { display: block; }
        .ResultadoProdutoPainel small { margin-top: 3px; color: #667482; }
        .LinhaNomeProduto { display: flex; align-items: baseline; gap: 7px; flex-wrap: wrap; }
        .MarcaProduto { color: #202b36; font-size: 12px; font-weight: 600; }
        .FormularioResultadoPainel { display: grid; grid-template-columns: 82px 1fr; gap: 7px; }
        .FormularioResultadoPainel input[type="number"] {
            min-width: 0;
            min-height: 38px;
            padding: 0 8px;
            border: 1px solid #cbd6df;
            border-radius: 5px;
            font: inherit;
        }

        .FormularioResultadoPainel button {
            border: 0;
            border-radius: 5px;
            color: #ffffff;
            background: #0784ca;
            font-weight: 700;
            cursor: pointer;
        }

        .ListaItensPainel { padding: 4px 15px; }
        .ItemPainelCarrinho {
            padding: 11px 0;
            display: grid;
            grid-template-columns: minmax(0, 1fr) auto auto;
            align-items: center;
            gap: 8px;
            border-bottom: 1px solid #e0e7eb;
        }

        .ItemPainelCarrinho strong,
        .ItemPainelCarrinho small { display: block; }
        .ItemPainelCarrinho small { margin-top: 3px; color: #667482; }
        .ItemPainelCarrinho > span { font-weight: 700; }

        .BotaoRemoverPainel {
            width: 28px;
            height: 28px;
            border: 0;
            border-radius: 4px;
            color: #a12c25;
            background: #fde9e7;
            font-size: 19px;
            cursor: pointer;
        }

        .PainelCarrinhoVazio {
            min-height: 90px;
            padding: 18px;
            display: grid;
            place-content: center;
            gap: 5px;
            color: #667482;
            text-align: center;
        }

        .TotalPainelCarrinho {
            margin: 0 15px;
            padding: 14px 0;
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-top: 2px solid #d6e0e6;
        }

        .TotalPainelCarrinho span { color: #52616f; font-weight: 700; }
        .TotalPainelCarrinho strong { color: #0784ca; font-size: 21px; }

        .PagamentoPainel { padding: 0 15px 12px; }
        .PagamentoPainel fieldset {
            margin: 0 0 12px;
            padding: 0;
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            border: 0;
        }

        .PagamentoPainel legend { margin-bottom: 7px; color: #52616f; font-size: 13px; font-weight: 700; }
        .PagamentoPainel fieldset label { display: flex; align-items: center; gap: 5px; font-size: 13px; }
        .DinheiroPainel > label { display: block; margin-bottom: 6px; color: #52616f; font-size: 12px; font-weight: 700; }
        .TrocoPainel { margin: 8px 0 12px; display: flex; justify-content: space-between; font-size: 13px; }
        .TrocoPainel output { font-weight: 700; }

        .BotaoConcluirPainel,
        .BotaoCancelarPainel {
            width: 100%;
            min-height: 40px;
            border-radius: 5px;
            font: inherit;
            font-weight: 700;
            cursor: pointer;
        }

        .BotaoConcluirPainel { border: 0; color: #ffffff; background: #0784ca; }
        .BotaoCancelarPainel { margin-top: 7px; border: 1px solid #c53b32; color: #a12c25; background: #ffffff; }
        .LinkCarrinhoCompleto { display: block; padding: 0 15px 15px; color: #0784ca; text-align: center; font-size: 12px; }

        .MensagemOperacao {
            margin-bottom: 16px;
            padding: 12px 14px;
            border-left: 4px solid;
            border-radius: 4px;
        }

        .MensagemOperacao.Sucesso { border-color: #14866d; color: #0c614f; background: #e7f7f2; }
        .MensagemOperacao.Erro { border-color: #c53b32; color: #8b241e; background: #fff0ef; }

        .DialogoNomeCarrinho {
            width: min(430px, calc(100vw - 32px));
            padding: 0;
            border: 1px solid #b8c8d2;
            border-radius: 6px;
            color: #26313d;
            background: #ffffff;
            box-shadow: 0 22px 60px rgba(22, 43, 56, 0.32);
        }

        .DialogoNomeCarrinho::backdrop { background: rgba(21, 36, 47, 0.48); }
        .FormularioNomeCarrinho { padding: 22px; }
        .FormularioNomeCarrinho h2 { margin: 0 0 18px; font-size: 21px; }
        .FormularioNomeCarrinho label {
            display: block;
            margin-bottom: 7px;
            color: #3f4f5f;
            font-size: 13px;
            font-weight: 700;
        }
        .AcoesDialogoNome {
            margin-top: 20px;
            display: flex;
            justify-content: flex-end;
            gap: 9px;
        }
        .AcoesDialogoNome button { min-height: 40px; }

        [hidden] { display: none !important; }

        @media (max-width: 760px) {
            .GradeAtendimentos { grid-template-columns: 1fr; }
            .AreaPaineisCarrinhos { grid-template-columns: 1fr; }
            .TituloSecao { align-items: flex-start; flex-direction: column; gap: 4px; }
            .ConsultaEstoqueCabecalho { align-items: stretch; flex-direction: column; }
            .PainelCarrinhoFlutuante {
                max-height: 560px;
            }
        }
    </style>
    """


def ObterScriptPaginaPrincipal(
    ProdutosJson,
    TokenCsrf,
    CarrinhosAbertos,
    CarrinhoPesquisado,
    BuscaCarrinho,
):
    Script = """
    <script>
        (() => {
            const Produtos = __PRODUTOS__;
            const TokenCsrf = __TOKEN_CSRF__;
            const AreaPaineis = document.getElementById("AreaPaineisCarrinhos");
            const Abertos = new Set(__CARRINHOS_ABERTOS__);

            const Normalizar = (Valor) => Valor
                .normalize("NFD")
                .replace(/[\u0300-\u036f]/g, "")
                .toLowerCase();

            const ObterListaAbertos = () => Array.from(Abertos).sort().join(",");

            const AtualizarCamposAbertos = () => {
                const Valor = ObterListaAbertos();
                document.querySelectorAll(".CampoCarrinhosAbertos").forEach((Campo) => {
                    Campo.value = Valor;
                });
            };

            const AtualizarPaineis = () => {
                document.querySelectorAll("[data-painel-carrinho]").forEach((Painel) => {
                    Painel.hidden = false;
                });
                document.querySelectorAll("[data-abrir-carrinho]").forEach((Botao) => {
                    Botao.classList.add("Aberto");
                    Botao.setAttribute("aria-expanded", "true");
                });
                AreaPaineis.hidden = false;
                AtualizarCamposAbertos();
            };

            const AdicionarCampo = (Formulario, Nome, Valor, Classe = "") => {
                const Campo = document.createElement("input");
                Campo.type = "hidden";
                Campo.name = Nome;
                Campo.value = Valor;
                if (Classe) Campo.className = Classe;
                Formulario.appendChild(Campo);
                return Campo;
            };

            const CriarResultadoProduto = (Produto, NumeroCarrinho, TermoBusca) => {
                const Resultado = document.createElement("article");
                Resultado.className = "ResultadoProdutoPainel";

                const Dados = document.createElement("div");
                const LinhaNome = document.createElement("div");
                LinhaNome.className = "LinhaNomeProduto";
                const Nome = document.createElement("strong");
                Nome.textContent = Produto.Nome;
                const Marca = document.createElement("span");
                Marca.className = "MarcaProduto";
                Marca.textContent = Produto.Marca;
                LinhaNome.append(Nome, Marca);
                const Detalhes = document.createElement("small");
                Detalhes.textContent = `${Produto.Categoria} · ${Produto.Fornecedor} · Venda R$ ${Produto.Preco} / ${Produto.Unidade} · ${Produto.Estoque}`;
                Dados.append(LinhaNome, Detalhes);

                const Formulario = document.createElement("form");
                Formulario.className = "FormularioResultadoPainel";
                Formulario.method = "post";
                Formulario.action = "/carrinho/adicionar";
                AdicionarCampo(Formulario, "csrfmiddlewaretoken", TokenCsrf);
                AdicionarCampo(Formulario, "carrinho", NumeroCarrinho);
                AdicionarCampo(Formulario, "produto", Produto.Id);
                AdicionarCampo(Formulario, "retorno", "pagina-principal");
                AdicionarCampo(Formulario, "carrinhos_abertos", ObterListaAbertos(), "CampoCarrinhosAbertos");
                AdicionarCampo(Formulario, "busca", TermoBusca);

                const Quantidade = document.createElement("input");
                Quantidade.type = "number";
                Quantidade.name = "quantidade";
                Quantidade.min = Produto.Passo;
                if (Produto.EstoqueMaximo) Quantidade.max = Produto.EstoqueMaximo;
                Quantidade.step = Produto.Passo;
                Quantidade.value = Produto.QuantidadeInicial;
                Quantidade.setAttribute("aria-label", Produto.RotuloQuantidade);
                Quantidade.required = true;

                const Adicionar = document.createElement("button");
                Adicionar.type = "submit";
                Adicionar.textContent = "Adicionar";
                Formulario.append(Quantidade, Adicionar);
                Resultado.append(Dados, Formulario);
                return Resultado;
            };

            const RenderizarResultados = (NumeroCarrinho) => {
                const CampoBusca = document.querySelector(`[data-busca-produto="${NumeroCarrinho}"]`);
                const AreaResultados = document.querySelector(`[data-resultados-produtos="${NumeroCarrinho}"]`);
                const Termo = CampoBusca.value.trim();
                AreaResultados.replaceChildren();

                if (!Termo) return;

                const TermoNormalizado = Normalizar(Termo);
                const Encontrados = Produtos.filter((Produto) =>
                    Normalizar(`${Produto.Nome} ${Produto.Categoria} ${Produto.Marca} ${Produto.Fornecedor}`).includes(TermoNormalizado)
                ).slice(0, 8);

                if (!Encontrados.length) {
                    const Vazio = document.createElement("small");
                    Vazio.textContent = "Nenhum produto disponível.";
                    AreaResultados.appendChild(Vazio);
                    return;
                }

                Encontrados.forEach((Produto) => {
                    AreaResultados.appendChild(CriarResultadoProduto(Produto, NumeroCarrinho, Termo));
                });
            };

            document.querySelectorAll("[data-abrir-carrinho]").forEach((Botao) => {
                Botao.addEventListener("click", () => {
                    const Numero = Botao.dataset.abrirCarrinho;
                    Abertos.add(Numero);
                    document.querySelector(`[data-busca-produto="${Numero}"]`).focus();
                });
            });

            const DialogoNome = document.getElementById("DialogoNomeCarrinho");
            const CampoNumeroCarrinho = document.getElementById("NumeroCarrinhoNome");
            const CampoNomeCliente = document.getElementById("NomeClienteCarrinho");

            document.querySelectorAll("[data-editar-nome]").forEach((Botao) => {
                Botao.addEventListener("click", () => {
                    CampoNumeroCarrinho.value = Botao.dataset.carrinho;
                    CampoNomeCliente.value = Botao.dataset.nomePersonalizado;
                    AtualizarCamposAbertos();
                    DialogoNome.showModal();
                    CampoNomeCliente.focus();
                    CampoNomeCliente.select();
                });
            });

            document.querySelector("[data-fechar-dialogo-nome]").addEventListener("click", () => {
                DialogoNome.close();
            });

            document.querySelectorAll("[data-busca-produto]").forEach((Campo) => {
                Campo.addEventListener("input", () => RenderizarResultados(Campo.dataset.buscaProduto));
            });

            document.querySelectorAll("form").forEach((Formulario) => {
                Formulario.addEventListener("submit", AtualizarCamposAbertos);
            });

            document.querySelectorAll("[data-formulario-pagamento]").forEach((Formulario) => {
                const Total = Number(Formulario.dataset.total);
                const AreaDinheiro = Formulario.querySelector("[data-area-dinheiro]");
                const ValorRecebido = Formulario.querySelector("[data-valor-recebido]");
                const Troco = Formulario.querySelector("[data-troco]");

                const FormatarMoeda = (Valor) => Valor.toLocaleString("pt-BR", {
                    style: "currency",
                    currency: "BRL",
                });

                const AtualizarTroco = () => {
                    const Recebido = Number(ValorRecebido.value.replace(".", "").replace(",", "."));
                    if (!Number.isFinite(Recebido)) {
                        Troco.textContent = "R$ 0,00";
                        return;
                    }
                    const Diferenca = Recebido - Total;
                    Troco.textContent = Diferenca >= 0
                        ? FormatarMoeda(Diferenca)
                        : `Faltam ${FormatarMoeda(Math.abs(Diferenca))}`;
                };

                const AtualizarPagamento = () => {
                    const Forma = Formulario.querySelector('[name="forma_pagamento"]:checked').value;
                    const Dinheiro = Forma === "dinheiro";
                    AreaDinheiro.hidden = !Dinheiro;
                    ValorRecebido.required = Dinheiro;
                    if (Dinheiro) AtualizarTroco();
                };

                Formulario.querySelectorAll('[name="forma_pagamento"]').forEach((Opcao) => {
                    Opcao.addEventListener("change", AtualizarPagamento);
                });
                ValorRecebido.addEventListener("input", AtualizarTroco);
                AtualizarPagamento();
            });

            const CarrinhoPesquisado = __CARRINHO_PESQUISADO__;
            const BuscaInicial = __BUSCA_CARRINHO__;
            if (CarrinhoPesquisado && BuscaInicial) {
                const CampoInicial = document.querySelector(`[data-busca-produto="${CarrinhoPesquisado}"]`);
                if (CampoInicial) {
                    CampoInicial.value = BuscaInicial;
                    RenderizarResultados(CarrinhoPesquisado);
                }
            }

            AtualizarPaineis();
        })();
    </script>
    """

    return (
        Script.replace("__PRODUTOS__", ProdutosJson)
        .replace("__TOKEN_CSRF__", json.dumps(TokenCsrf))
        .replace("__CARRINHOS_ABERTOS__", json.dumps(CarrinhosAbertos))
        .replace("__CARRINHO_PESQUISADO__", json.dumps(CarrinhoPesquisado))
        .replace("__BUSCA_CARRINHO__", json.dumps(BuscaCarrinho))
    )


def ComponentePaginaPrincipal(Request):
    BuscaEstoque = Request.GET.get("busca", "").strip()
    BuscaCarrinho = Request.GET.get("busca_carrinho", "").strip()
    CarrinhoPesquisado = Request.GET.get("carrinho", "")
    CarrinhosAbertos = ObterCarrinhosAbertos(Request)
    DadosPagina = GerarDadosPaginaPrincipal(Request, BuscaEstoque=BuscaEstoque)
    ResumoProdutos = DadosPagina["ResumoProdutos"]
    ConsultaEstoque = DadosPagina["ConsultaEstoque"]
    TokenCsrf = escape(ObterTokenCsrf(Request))
    NumerosAbertos = ",".join(CarrinhosAbertos)
    Mensagem = ConsumirMensagem(Request)
    HtmlMensagem = ""

    if Mensagem:
        ClasseMensagem = "Erro" if Mensagem["Tipo"] == "erro" else "Sucesso"
        HtmlMensagem = (
            f'<div class="MensagemOperacao {ClasseMensagem}" role="status">'
            f'{escape(Mensagem["Texto"])}</div>'
        )

    CartoesCarrinhos = RenderizarCartoesCarrinhos(
        DadosPagina["ResumosCarrinhos"],
        CarrinhosAbertos,
    )
    PaineisCarrinhos = RenderizarPaineisCarrinhos(
        DadosPagina["ResumosCarrinhos"],
        CarrinhosAbertos,
        TokenCsrf,
    )
    TabelaEstoque = RenderizarConsultaEstoque(ConsultaEstoque)
    ProdutosParaPesquisa = [
        {
            "Id": ProdutoEstoque["Id"],
            "Nome": ProdutoEstoque["Nome"],
            "Categoria": ProdutoEstoque["Categoria"],
            "Marca": ProdutoEstoque["Marca"],
            "Fornecedor": ", ".join(dict.fromkeys(
                Lote["Fornecedor"] for Lote in ProdutoEstoque["Lotes"] if Lote["Disponivel"]
            )),
            "Unidade": ProdutoEstoque["Unidade"],
            "Estoque": ProdutoEstoque["EstoqueDescricao"],
            "EstoqueMaximo": (
                format(ProdutoEstoque["Quantidade"], "f")
                if ProdutoEstoque["ControlaQuantidade"]
                else ""
            ),
            "Preco": ProdutoEstoque["PrecoVendaFormatado"],
            "Passo": "1" if ProdutoEstoque["Unidade"] in {"un", "item"} else "0.001",
            "QuantidadeInicial": "0.100" if ProdutoEstoque["Unidade"] == "kg" else "1",
            "RotuloQuantidade": (
                "Peso em kg"
                if ProdutoEstoque["Unidade"] == "kg"
                else "Comprimento em metros"
                if ProdutoEstoque["Unidade"] == "m"
                else "Quantidade"
            ),
        }
        for ProdutoEstoque in ResumoProdutos["Produtos"]
        if ProdutoEstoque["QuantidadeLotesDisponiveis"] > 0
    ]
    ProdutosJson = json.dumps(
        ProdutosParaPesquisa,
        ensure_ascii=False,
    ).replace("</", "<\\/")
    ScriptPagina = ObterScriptPaginaPrincipal(
        ProdutosJson,
        TokenCsrf,
        CarrinhosAbertos,
        CarrinhoPesquisado,
        BuscaCarrinho,
    )
    ConteudoPrincipal = f"""
    {ObterEstilosPaginaPrincipal()}

    {HtmlMensagem}

    <div class="TituloSecao TituloAtendimentos">
        <h2>Atendimentos em andamento</h2>
        <span>Carrinhos sempre abertos</span>
    </div>
    <section class="GradeAtendimentos" aria-label="Carrinhos em atendimento">
        {CartoesCarrinhos}
    </section>

    <div
        class="AreaPaineisCarrinhos"
        id="AreaPaineisCarrinhos"
        aria-label="Carrinhos abertos"
    >
        {PaineisCarrinhos}
    </div>

    <dialog class="DialogoNomeCarrinho" id="DialogoNomeCarrinho">
        <form class="FormularioNomeCarrinho" method="post" action="/carrinho/nome">
            <input type="hidden" name="csrfmiddlewaretoken" value="{TokenCsrf}">
            <input id="NumeroCarrinhoNome" type="hidden" name="carrinho" value="1">
            <input type="hidden" name="retorno" value="pagina-principal">
            <input class="CampoCarrinhosAbertos" type="hidden" name="carrinhos_abertos" value="{NumerosAbertos}">
            <h2>Identificar atendimento</h2>
            <label for="NomeClienteCarrinho">Nome do cliente</label>
            <input
                id="NomeClienteCarrinho"
                class="CampoFormulario"
                type="text"
                name="nome_cliente"
                maxlength="80"
                autocomplete="off"
                placeholder="Nome do cliente (opcional)"
            >
            <div class="AcoesDialogoNome">
                <button class="BotaoSecundario" type="button" data-fechar-dialogo-nome>Cancelar</button>
                <button class="BotaoPrimario" type="submit">Salvar nome</button>
            </div>
        </form>
    </dialog>

    <div class="TituloSecao">
        <h2>Situação do estoque</h2>
    </div>
    <section class="GridIndicadores" aria-label="Indicadores do estoque">
        <article class="CardIndicador" style="--CorDestaque: #2d74d8;">
            <div>
                <strong>Produtos cadastrados</strong>
                <span>{ResumoProdutos['TotalProdutos']}</span>
            </div>
            <div class="IconeIndicador" aria-hidden="true">PR</div>
        </article>

        <article class="CardIndicador" style="--CorDestaque: #f59f18;">
            <div>
                <strong>Produtos com estoque baixo</strong>
                <span>{ResumoProdutos['TotalEstoqueBaixo']}</span>
            </div>
            <div class="IconeIndicador" aria-hidden="true">!</div>
        </article>

        <article class="CardIndicador" style="--CorDestaque: #00a889;">
            <div>
                <strong>Produtos com saldo</strong>
                <span>{ResumoProdutos['TotalProdutosDisponiveis']}</span>
            </div>
            <div class="IconeIndicador" aria-hidden="true">QT</div>
        </article>
    </section>

    <div class="ConsultaEstoqueCabecalho">
        <h2>Consulta do estoque</h2>
        <form class="BarraFiltros" method="get" action="/">
            <input type="hidden" name="carrinhos_abertos" value="{NumerosAbertos}">
            <input
                class="CampoFormulario"
                type="search"
                name="busca"
                value="{escape(BuscaEstoque)}"
                placeholder="Produto, categoria, marca ou fornecedor"
                aria-label="Pesquisar no estoque"
            >
            <button class="BotaoPrimario" type="submit">Pesquisar</button>
        </form>
    </div>
    {TabelaEstoque}

    {ScriptPagina}
    """

    return HttpResponse(
        RenderizarLayoutBase(
            "Página Principal",
            ConteudoPrincipal,
            RotaAtiva="pagina-principal",
        )
    )
