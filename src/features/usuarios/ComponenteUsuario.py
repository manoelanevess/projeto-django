"""Componente da tela inicial de acesso dos usuários."""
from django.http import HttpResponse

from componentes.LayoutBase import RenderizarLayoutBase


def ComponenteLogin(request):
    ConteudoPrincipal = """
    <h1>Login</h1>

    <section class="EstadoVazio">
        <h2>Acesso ao sistema</h2>
        <p>O formulário real de autenticação será conectado quando a feature de usuários for implementada.</p>
        <form class="BarraFiltros" method="post" action="/login">
            <input class="CampoFormulario" type="email" placeholder="E-mail" aria-label="E-mail">
            <input class="CampoFormulario" type="password" placeholder="Senha" aria-label="Senha">
            <button class="BotaoPrimario" type="button">Entrar</button>
        </form>
    </section>
    """

    return HttpResponse(
        RenderizarLayoutBase("Login", ConteudoPrincipal, RotaAtiva="login")
    )
