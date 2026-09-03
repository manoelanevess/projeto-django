"""Componente inicial da feature de produtos."""
from django.http import HttpResponse

from .LogicaProduto import GerarResumoProdutos


def ComponenteListaProdutos(request):
    ResumoProdutos = GerarResumoProdutos()
    LinhasProdutos = "".join(
        f"""
        <tr>
            <td>{Produto["Nome"]}</td>
            <td>{Produto["Categoria"]}</td>
            <td>{Produto["Quantidade"]}</td>
        </tr>
        """
        for Produto in ResumoProdutos["Produtos"]
    )

    ConteudoHtml = f"""
    <!doctype html>
    <html lang="pt-br">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Controle de Estoque</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 40px;
                color: #1f2933;
                background: #f7f9fb;
            }}

            main {{
                max-width: 860px;
                margin: 0 auto;
            }}

            table {{
                width: 100%;
                border-collapse: collapse;
                background: #ffffff;
            }}

            th,
            td {{
                padding: 12px;
                border: 1px solid #d9e2ec;
                text-align: left;
            }}

            th {{
                background: #e6f0f5;
            }}
        </style>
    </head>
    <body>
        <main>
            <h1>Controle de Estoque</h1>
            <p>Total de produtos: {ResumoProdutos["TotalProdutos"]}</p>
            <p>Total de itens em estoque: {ResumoProdutos["TotalItens"]}</p>
            <table>
                <thead>
                    <tr>
                        <th>Produto</th>
                        <th>Categoria</th>
                        <th>Quantidade</th>
                    </tr>
                </thead>
                <tbody>
                    {LinhasProdutos}
                </tbody>
            </table>
        </main>
    </body>
    </html>
    """

    return HttpResponse(ConteudoHtml)
