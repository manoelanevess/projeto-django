"""Layout compartilhado pelas telas principais do sistema."""


MenusNavegacao = [
    {"Chave": "dashboard", "Nome": "Dashboard", "Rota": "/", "Sigla": "DA"},
    {"Chave": "produtos", "Nome": "Produtos", "Rota": "/produtos", "Sigla": "PR"},
    {"Chave": "estoque", "Nome": "Estoque", "Rota": "/estoque", "Sigla": "ES"},
    {
        "Chave": "fornecedores",
        "Nome": "Fornecedores",
        "Rota": "/fornecedores",
        "Sigla": "FO",
    },
    {"Chave": "login", "Nome": "Login", "Rota": "/login", "Sigla": "LG"},
]


def GerarMenuNavegacao(RotaAtiva):
    ItensMenu = []

    for Menu in MenusNavegacao:
        ClasseAtiva = " Ativo" if Menu["Chave"] == RotaAtiva else ""
        AtributoAtual = ' aria-current="page"' if Menu["Chave"] == RotaAtiva else ""
        ItensMenu.append(
            f"""
            <a class="ItemMenu{ClasseAtiva}" href="{Menu["Rota"]}"{AtributoAtual}>
                <span class="IconeMenu">{Menu["Sigla"]}</span>
                <span>{Menu["Nome"]}</span>
            </a>
            """
        )

    return "".join(ItensMenu)


def RenderizarLayoutBase(TituloPagina, ConteudoPrincipal, RotaAtiva="dashboard"):
    ItensMenu = GerarMenuNavegacao(RotaAtiva)

    return f"""
    <!doctype html>
    <html lang="pt-br">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>{TituloPagina} · Controle de Estoque</title>
        <style>
            * {{
                box-sizing: border-box;
            }}

            body {{
                margin: 0;
                min-height: 100vh;
                color: #26313d;
                background: #dfe7ec;
                font-family: Arial, Helvetica, sans-serif;
            }}

            a {{
                color: inherit;
            }}

            .TelaDashboard {{
                min-height: 100vh;
                display: grid;
                grid-template-columns: 92px 1fr;
                background: #eef3f6;
            }}

            .BarraLateral {{
                background: #0784ca;
                color: #ffffff;
                padding: 14px 10px;
                display: flex;
                flex-direction: column;
                gap: 8px;
                box-shadow: 3px 0 16px rgba(22, 40, 52, 0.18);
                z-index: 2;
            }}

            .MarcaLateral {{
                width: 42px;
                height: 42px;
                margin: 0 auto 8px;
                border-radius: 50%;
                display: grid;
                place-items: center;
                background: #ffffff;
                color: #0784ca;
                font-weight: 700;
            }}

            .ItemMenu {{
                min-height: 52px;
                padding: 6px 4px;
                border-radius: 6px;
                color: #ffffff;
                text-decoration: none;
                display: grid;
                place-items: center;
                gap: 4px;
                font-size: 10px;
            }}

            .ItemMenu.Ativo,
            .ItemMenu:hover,
            .ItemMenu:focus-visible {{
                background: rgba(255, 255, 255, 0.17);
                outline: none;
            }}

            .IconeMenu {{
                width: 24px;
                height: 24px;
                border-radius: 5px;
                display: grid;
                place-items: center;
                background: rgba(255, 255, 255, 0.18);
                font-size: 9px;
                font-weight: 700;
            }}

            .AreaPrincipal {{
                min-width: 0;
                display: flex;
                flex-direction: column;
            }}

            .Topo {{
                min-height: 56px;
                padding: 0 24px;
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 16px;
                background: #ffffff;
                border-bottom: 1px solid #d6e0e6;
                box-shadow: 0 2px 10px rgba(30, 45, 56, 0.08);
            }}

            .MarcaTopo {{
                display: flex;
                align-items: center;
                gap: 10px;
                font-size: 17px;
                font-weight: 700;
                color: #2b3843;
            }}

            .MarcaTopo span {{
                width: 34px;
                height: 24px;
                border-radius: 999px;
                display: grid;
                place-items: center;
                color: #ffffff;
                background: #0784ca;
                font-size: 12px;
            }}

            .AcoesTopo {{
                display: flex;
                align-items: center;
                gap: 16px;
                color: #3f4f5f;
                font-size: 13px;
            }}

            .AcoesTopo a {{
                text-decoration: none;
            }}

            main {{
                width: min(1120px, 100%);
                margin: 0 auto;
                padding: 26px;
            }}

            h1 {{
                margin: 0 0 18px;
                font-size: 26px;
                font-weight: 500;
            }}

            h2 {{
                margin: 0 0 14px;
                font-size: 22px;
                font-weight: 500;
            }}

            table {{
                width: 100%;
                border-collapse: collapse;
                background: #ffffff;
                border-radius: 6px;
                overflow: hidden;
                box-shadow: 0 10px 22px rgba(31, 49, 61, 0.08);
            }}

            th,
            td {{
                padding: 12px;
                border-bottom: 1px solid #d9e2ec;
                text-align: left;
                font-size: 14px;
            }}

            th {{
                background: #eff5f8;
                color: #52616f;
                font-size: 12px;
                text-transform: uppercase;
            }}

            .GridIndicadores {{
                display: grid;
                grid-template-columns: repeat(3, minmax(0, 1fr));
                gap: 18px;
                margin-bottom: 24px;
            }}

            .CardIndicador {{
                min-height: 108px;
                padding: 18px;
                display: flex;
                align-items: flex-start;
                justify-content: space-between;
                gap: 14px;
                background: #ffffff;
                border-radius: 6px;
                border-top: 4px solid var(--CorDestaque);
                box-shadow: 0 10px 22px rgba(31, 49, 61, 0.08);
            }}

            .CardIndicador strong {{
                display: block;
                margin-bottom: 8px;
                color: var(--CorDestaque);
                font-size: 12px;
                text-transform: uppercase;
                line-height: 1.25;
            }}

            .CardIndicador span {{
                font-size: 24px;
                font-weight: 700;
                color: #202b36;
            }}

            .IconeIndicador {{
                width: 42px;
                height: 42px;
                border-radius: 6px;
                display: grid;
                place-items: center;
                color: #778394;
                background: #eef2f5;
                font-weight: 700;
            }}

            .GridAtalhos {{
                display: grid;
                grid-template-columns: repeat(3, minmax(0, 1fr));
                gap: 18px;
                margin-bottom: 24px;
            }}

            .CardAtalho {{
                min-height: 136px;
                padding: 20px 16px;
                display: grid;
                place-items: center;
                gap: 8px;
                text-align: center;
                text-decoration: none;
                background: #ffffff;
                border-radius: 6px;
                box-shadow: 0 10px 22px rgba(31, 49, 61, 0.08);
            }}

            .CardAtalho:hover,
            .CardAtalho:focus-visible {{
                transform: translateY(-1px);
                outline: 2px solid #0784ca;
                outline-offset: 2px;
            }}

            .IconeAtalho {{
                width: 58px;
                height: 50px;
                border-radius: 6px;
                display: grid;
                place-items: center;
                color: #ffffff;
                background: #8d98a8;
                font-weight: 700;
            }}

            .CardAtalho strong {{
                min-width: 86px;
                padding: 6px 10px;
                border-radius: 4px;
                color: #ffffff;
                background: #0784ca;
                font-size: 13px;
            }}

            .CardAtalho span {{
                color: #667482;
                font-size: 12px;
            }}

            .PainelTabela {{
                margin-top: 2px;
            }}

            .BarraFiltros {{
                margin-bottom: 20px;
                display: flex;
                flex-wrap: wrap;
                gap: 10px;
            }}

            .CampoFormulario {{
                min-height: 42px;
                padding: 0 12px;
                border: 1px solid #cbd6df;
                border-radius: 6px;
                background: #ffffff;
                color: #26313d;
                font: inherit;
            }}

            .CampoFormulario[type="search"] {{
                min-width: min(320px, 100%);
                flex: 1;
            }}

            .BotaoPrimario,
            .BotaoSecundario {{
                min-height: 42px;
                padding: 0 16px;
                border: 0;
                border-radius: 6px;
                display: inline-flex;
                align-items: center;
                justify-content: center;
                text-decoration: none;
                font-weight: 700;
                cursor: pointer;
            }}

            .BotaoPrimario {{
                color: #ffffff;
                background: #0784ca;
            }}

            .BotaoSecundario {{
                color: #0784ca;
                background: #d9edf7;
            }}

            .EstadoVazio {{
                padding: 24px;
                border-radius: 6px;
                background: #ffffff;
                box-shadow: 0 10px 22px rgba(31, 49, 61, 0.08);
            }}

            .EstadoVazio p {{
                margin: 0 0 16px;
                color: #667482;
            }}

            @media (max-width: 760px) {{
                .TelaDashboard {{
                    grid-template-columns: 1fr;
                }}

                .BarraLateral {{
                    position: sticky;
                    top: 0;
                    flex-direction: row;
                    overflow-x: auto;
                    padding: 10px;
                }}

                .MarcaLateral {{
                    flex: 0 0 42px;
                    margin: 0;
                }}

                .ItemMenu {{
                    flex: 0 0 76px;
                }}

                .Topo {{
                    height: auto;
                    padding: 14px 18px;
                    align-items: flex-start;
                    flex-direction: column;
                }}

                main {{
                    padding: 20px 14px;
                }}

                .GridIndicadores,
                .GridAtalhos {{
                    grid-template-columns: 1fr;
                }}

                table {{
                    min-width: 640px;
                }}

                .PainelTabela {{
                    overflow-x: auto;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="TelaDashboard">
            <aside class="BarraLateral" aria-label="Menu principal">
                <div class="MarcaLateral">EN</div>
                {ItensMenu}
            </aside>

            <div class="AreaPrincipal">
                <header class="Topo">
                    <div class="MarcaTopo"><span>EN</span> Estoque Nuvem</div>
                    <nav class="AcoesTopo" aria-label="Ações rápidas">
                        <a href="/">Início</a>
                        <a href="/login">Conta</a>
                    </nav>
                </header>

                <main tabindex="-1">
                    {ConteudoPrincipal}
                </main>
            </div>
        </div>
    </body>
    </html>
    """
