"""Componente da tela de fornecedores."""
from django.http import HttpResponse

from componentes.LayoutBase import RenderizarLayoutBase


FornecedoresIniciais = [
    {"Nome": "Papelaria Central", "Contato": "compras@central.test", "Cidade": "São Paulo"},
    {"Nome": "Tech Distribuidora", "Contato": "vendas@tech.test", "Cidade": "Campinas"},
]


def ComponenteFornecedores(request):
    LinhasFornecedores = "".join(
        f"""
        <tr>
            <td>{Fornecedor["Nome"]}</td>
            <td>{Fornecedor["Contato"]}</td>
            <td>{Fornecedor["Cidade"]}</td>
        </tr>
        """
        for Fornecedor in FornecedoresIniciais
    )

    ConteudoPrincipal = f"""
    <h1>Fornecedores</h1>

    <section class="PainelTabela" aria-label="Fornecedores cadastrados">
        <table>
            <thead>
                <tr>
                    <th>Fornecedor</th>
                    <th>Contato</th>
                    <th>Cidade</th>
                </tr>
            </thead>
            <tbody>
                {LinhasFornecedores}
            </tbody>
        </table>
    </section>
    """

    return HttpResponse(
        RenderizarLayoutBase(
            "Fornecedores",
            ConteudoPrincipal,
            RotaAtiva="fornecedores",
        )
    )
