"""Componente da listagem de produtos."""
from html import escape

from django.http import HttpResponse

from componentes.LayoutBase import RenderizarLayoutBase

from .LogicaProduto import GerarResumoProdutos


def ComponenteListaProdutos(request):
    Busca = request.GET.get("busca", "").strip()
    Estoque = request.GET.get("estoque", "").strip()
    ResumoProdutos = GerarResumoProdutos(Busca=Busca, Estoque=Estoque)
    BuscaSegura = escape(Busca)
    OpcaoTodos = "selected" if Estoque == "" else ""
    OpcaoBaixo = "selected" if Estoque == "baixo" else ""

    if ResumoProdutos["Produtos"]:
        LinhasProdutos = "".join(
            f"""
            <tr>
                <td>{Produto["Nome"]}</td>
                <td>{Produto["Categoria"]}</td>
                <td>{Produto["Quantidade"]}</td>
                <td>{Produto["EstoqueMinimo"]}</td>
            </tr>
            """
            for Produto in ResumoProdutos["Produtos"]
        )
        ResultadoProdutos = f"""
        <section class="PainelTabela" aria-label="Produtos cadastrados">
            <table>
                <thead>
                    <tr>
                        <th>Produto</th>
                        <th>Categoria</th>
                        <th>Quantidade</th>
                        <th>Estoque mínimo</th>
                    </tr>
                </thead>
                <tbody>
                    {LinhasProdutos}
                </tbody>
            </table>
        </section>
        """
    else:
        ResultadoProdutos = """
        <section class="EstadoVazio">
            <h2>Nenhum produto encontrado</h2>
            <p>Altere os filtros ou cadastre um novo produto quando essa tela estiver conectada ao banco.</p>
            <a class="BotaoSecundario" href="/produtos">Limpar filtros</a>
        </section>
        """

    ConteudoPrincipal = f"""
    <h1>Produtos</h1>

    <form class="BarraFiltros" method="get" action="/produtos">
        <input
            class="CampoFormulario"
            type="search"
            name="busca"
            value="{BuscaSegura}"
            placeholder="Buscar produto ou categoria"
            aria-label="Buscar produto ou categoria"
        >
        <select class="CampoFormulario" name="estoque" aria-label="Filtrar por estoque">
            <option value="" {OpcaoTodos}>Todos os estoques</option>
            <option value="baixo" {OpcaoBaixo}>Estoque baixo</option>
        </select>
        <button class="BotaoPrimario" type="submit">Filtrar</button>
        <a class="BotaoSecundario" href="/produtos">Limpar</a>
    </form>

    <section class="GridIndicadores" aria-label="Resumo de produtos">
        <article class="CardIndicador" style="--CorDestaque: #2d74d8;">
            <div>
                <strong>Produtos encontrados</strong>
                <span>{ResumoProdutos["TotalProdutos"]}</span>
            </div>
            <div class="IconeIndicador" aria-hidden="true">PR</div>
        </article>

        <article class="CardIndicador" style="--CorDestaque: #f59f18;">
            <div>
                <strong>Itens em estoque</strong>
                <span>{ResumoProdutos["TotalItens"]}</span>
            </div>
            <div class="IconeIndicador" aria-hidden="true">QT</div>
        </article>

        <article class="CardIndicador" style="--CorDestaque: #00a889;">
            <div>
                <strong>Estoque baixo</strong>
                <span>{ResumoProdutos["TotalEstoqueBaixo"]}</span>
            </div>
            <div class="IconeIndicador" aria-hidden="true">!</div>
        </article>
    </section>

    {ResultadoProdutos}
    """

    return HttpResponse(
        RenderizarLayoutBase("Produtos", ConteudoPrincipal, RotaAtiva="produtos")
    )
