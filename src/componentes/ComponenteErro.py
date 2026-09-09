"""Componentes compartilhados para páginas de erro."""
from django.http import HttpResponseNotFound

from .LayoutBase import RenderizarLayoutBase


def ComponentePaginaNaoEncontrada(request, CaminhoNaoEncontrado=None, exception=None):
    ConteudoPrincipal = """
    <section class="EstadoVazio">
        <h1>Página não encontrada</h1>
        <p>A rota solicitada não existe ou ainda não foi implementada no projeto.</p>
        <a class="BotaoPrimario" href="/">Voltar para o dashboard</a>
    </section>
    """

    return HttpResponseNotFound(
        RenderizarLayoutBase(
            "Página não encontrada",
            ConteudoPrincipal,
            RotaAtiva="",
        )
    )
