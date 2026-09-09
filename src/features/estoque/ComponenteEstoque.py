"""Componente da tela de controle de estoque."""
from django.http import HttpResponse

from componentes.LayoutBase import RenderizarLayoutBase
from features.produtos.LogicaProduto import GerarResumoProdutos


def ComponenteEstoque(request):
    ResumoProdutos = GerarResumoProdutos()

    ConteudoPrincipal = f"""
    <h1>Estoque</h1>

    <section class="GridIndicadores" aria-label="Indicadores do estoque">
        <article class="CardIndicador" style="--CorDestaque: #2d74d8;">
            <div>
                <strong>Total de itens</strong>
                <span>{ResumoProdutos["TotalItens"]}</span>
            </div>
            <div class="IconeIndicador" aria-hidden="true">QT</div>
        </article>

        <article class="CardIndicador" style="--CorDestaque: #f59f18;">
            <div>
                <strong>Produtos em alerta</strong>
                <span>{ResumoProdutos["TotalEstoqueBaixo"]}</span>
            </div>
            <div class="IconeIndicador" aria-hidden="true">!</div>
        </article>

        <article class="CardIndicador" style="--CorDestaque: #00a889;">
            <div>
                <strong>Movimentações hoje</strong>
                <span>0</span>
            </div>
            <div class="IconeIndicador" aria-hidden="true">MV</div>
        </article>
    </section>

    <section class="EstadoVazio">
        <h2>Movimentações de estoque</h2>
        <p>As entradas e saídas serão exibidas aqui depois que os models e migrations forem criados.</p>
        <a class="BotaoPrimario" href="/produtos?estoque=baixo">Ver produtos com estoque baixo</a>
    </section>
    """

    return HttpResponse(
        RenderizarLayoutBase("Estoque", ConteudoPrincipal, RotaAtiva="estoque")
    )
