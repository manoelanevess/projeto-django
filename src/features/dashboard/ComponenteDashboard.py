"""Componente da tela inicial do dashboard."""
from django.http import HttpResponse

from componentes.LayoutBase import RenderizarLayoutBase

from .LogicaDashboard import GerarDadosDashboard


def FormatarValorMoeda(Valor):
    return (
        f"{Valor:,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


def ComponenteDashboard(request):
    DadosDashboard = GerarDadosDashboard()
    ResumoProdutos = DadosDashboard["ResumoProdutos"]
    CustoTotalFormatado = FormatarValorMoeda(ResumoProdutos["CustoTotal"])
    CardsAtalho = "".join(
        f"""
        <a class="CardAtalho" href="{Atalho["Rota"]}">
            <div class="IconeAtalho" aria-hidden="true">{Atalho["Sigla"]}</div>
            <strong>{Atalho["Titulo"]}</strong>
            <span>{Atalho["Descricao"]}</span>
        </a>
        """
        for Atalho in DadosDashboard["Atalhos"]
    )

    ConteudoPrincipal = f"""
    <h1>Dashboard</h1>

    <section class="GridIndicadores" aria-label="Indicadores do estoque">
        <article class="CardIndicador" style="--CorDestaque: #f59f18;">
            <div>
                <strong>Produtos com estoque baixo</strong>
                <span>{ResumoProdutos["TotalEstoqueBaixo"]}</span>
            </div>
            <div class="IconeIndicador" aria-hidden="true">!</div>
        </article>

        <article class="CardIndicador" style="--CorDestaque: #2d74d8;">
            <div>
                <strong>Quantidade de produtos no estoque</strong>
                <span>{ResumoProdutos["TotalItens"]}</span>
            </div>
            <div class="IconeIndicador" aria-hidden="true">QT</div>
        </article>

        <article class="CardIndicador" style="--CorDestaque: #00a889;">
            <div>
                <strong>Custo total de produtos</strong>
                <span>R$ {CustoTotalFormatado}</span>
            </div>
            <div class="IconeIndicador" aria-hidden="true">$</div>
        </article>
    </section>

    <h2>Atalhos</h2>
    <section class="GridAtalhos" aria-label="Atalhos do sistema">
        {CardsAtalho}
    </section>
    """

    return HttpResponse(
        RenderizarLayoutBase("Dashboard", ConteudoPrincipal, RotaAtiva="dashboard")
    )
