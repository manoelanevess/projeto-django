"""Componentes de autenticação do proprietário."""
from html import escape

from django.contrib.auth import authenticate as AutenticarUsuario
from django.contrib.auth import login as IniciarSessao
from django.contrib.auth import logout as EncerrarSessao
from django.http import HttpResponse
from django.middleware.csrf import get_token as ObterTokenCsrf
from django.shortcuts import redirect as Redirecionar


def ComponenteLogin(Request):
    if Request.user.is_authenticated:
        return Redirecionar("Dashboard")

    MensagemErro = ""
    NomeUsuario = ""

    if Request.method == "POST":
        NomeUsuario = Request.POST.get("usuario", "").strip()
        Senha = Request.POST.get("senha", "")
        UsuarioAutenticado = AutenticarUsuario(
            Request,
            username=NomeUsuario,
            password=Senha,
        )

        if UsuarioAutenticado is not None:
            IniciarSessao(Request, UsuarioAutenticado)
            return Redirecionar("Dashboard")

        MensagemErro = """
        <div class="MensagemErro" role="alert">
            Usuário ou senha inválidos. Verifique os dados e tente novamente.
        </div>
        """

    TokenCsrf = escape(ObterTokenCsrf(Request))
    NomeUsuarioSeguro = escape(NomeUsuario)


    return HttpResponse(
        f"""
        <!doctype html>
        <html lang="pt-br">
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>Login · Controle de Estoque</title>
            <style>
                * {{
                    box-sizing: border-box;
                }}

                body {{
                    margin: 0;
                    min-height: 100vh;
                    display: grid;
                    place-items: center;
                    padding: 24px;
                    color: #26313d;
                    background: #e7edf1;
                    font-family: Arial, Helvetica, sans-serif;
                }}

                .TelaLogin {{
                    width: min(880px, 100%);
                    min-height: 520px;
                    display: grid;
                    grid-template-columns: minmax(260px, 0.85fr) minmax(360px, 1.15fr);
                    overflow: hidden;
                    border-radius: 8px;
                    background: #ffffff;
                    box-shadow: 0 18px 48px rgba(31, 49, 61, 0.16);
                }}

                .MarcaLogin {{
                    padding: 48px 40px;
                    display: flex;
                    flex-direction: column;
                    justify-content: space-between;
                    color: #ffffff;
                    background: #0784ca;
                }}

                .SimboloMarca {{
                    width: 52px;
                    height: 52px;
                    display: grid;
                    place-items: center;
                    border: 2px solid rgba(255, 255, 255, 0.7);
                    border-radius: 8px;
                    font-size: 16px;
                    font-weight: 700;
                }}

                .MarcaLogin h1 {{
                    margin: 0 0 12px;
                    font-size: 30px;
                    letter-spacing: 0;
                }}

                .MarcaLogin p {{
                    margin: 0;
                    color: #d9f1ff;
                    line-height: 1.5;
                }}

                .AreaFormulario {{
                    padding: 64px 56px;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                }}

                .AreaFormulario h2 {{
                    margin: 0 0 8px;
                    color: #202b36;
                    font-size: 26px;
                    letter-spacing: 0;
                }}

                .Subtitulo {{
                    margin: 0 0 30px;
                    color: #667482;
                    line-height: 1.5;
                }}

                .CampoGrupo {{
                    margin-bottom: 18px;
                }}

                label {{
                    display: block;
                    margin-bottom: 7px;
                    color: #3f4f5f;
                    font-size: 14px;
                    font-weight: 700;
                }}

                input {{
                    width: 100%;
                    min-height: 46px;
                    padding: 0 13px;
                    border: 1px solid #bccbd5;
                    border-radius: 6px;
                    color: #26313d;
                    background: #ffffff;
                    font: inherit;
                }}

                input:focus {{
                    border-color: #0784ca;
                    outline: 3px solid rgba(7, 132, 202, 0.15);
                }}

                button {{
                    width: 100%;
                    min-height: 46px;
                    margin-top: 8px;
                    border: 0;
                    border-radius: 6px;
                    color: #ffffff;
                    background: #0784ca;
                    font: inherit;
                    font-weight: 700;
                    cursor: pointer;
                }}

                button:hover,
                button:focus-visible {{
                    background: #056da8;
                }}

                .MensagemErro {{
                    margin-bottom: 18px;
                    padding: 11px 13px;
                    border-left: 4px solid #c53b32;
                    border-radius: 4px;
                    color: #8b241e;
                    background: #fff0ef;
                    font-size: 14px;
                    line-height: 1.4;
                }}

                @media (max-width: 700px) {{
                    body {{
                        padding: 0;
                        place-items: stretch;
                    }}

                    .TelaLogin {{
                        width: 100%;
                        min-height: 100vh;
                        grid-template-columns: 1fr;
                        border-radius: 0;
                    }}

                    .MarcaLogin {{
                        min-height: 190px;
                        padding: 28px 24px;
                        gap: 28px;
                    }}

                    .MarcaLogin h1 {{
                        font-size: 25px;
                    }}

                    .AreaFormulario {{
                        padding: 38px 24px;
                    }}
                }}
            </style>
        </head>
        <body>
            <main class="TelaLogin">
                <section class="MarcaLogin" aria-label="Controle de Estoque">
                    <div class="SimboloMarca">EN</div>
                    <div>
                        <h1>Estoque Nuvem</h1>
                        <p>Controle de estoque do seu comércio em um só lugar.</p>
                    </div>
                </section>

                <section class="AreaFormulario">
                    <h2>Acesso do proprietário</h2>
                    <p class="Subtitulo">Entre com seu usuário e sua senha.</p>
                    {MensagemErro}
                    <form method="post" action="/login">
                        <input type="hidden" name="csrfmiddlewaretoken" value="{TokenCsrf}">

                        <div class="CampoGrupo">
                            <label for="usuario">Usuário</label>
                            <input
                                id="usuario"
                                name="usuario"
                                type="text"
                                value="{NomeUsuarioSeguro}"
                                autocomplete="username"
                                required
                                autofocus
                            >
                        </div>

                        <div class="CampoGrupo">
                            <label for="senha">Senha</label>
                            <input
                                id="senha"
                                name="senha"
                                type="password"
                                autocomplete="current-password"
                                required
                            >
                        </div>

                        <button type="submit">Entrar</button>
                    </form>
                </section>
            </main>
        </body>
        </html>
        """
    )


def ComponenteLogout(Request):
    EncerrarSessao(Request)
    return Redirecionar("Login")
