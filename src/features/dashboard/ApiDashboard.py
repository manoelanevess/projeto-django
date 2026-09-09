"""Camada de API inicial da feature de dashboard."""


AtalhosDashboard = [
    {
        "Titulo": "Produtos",
        "Descricao": "Cadastro de produtos",
        "Sigla": "PR",
        "Rota": "/produtos",
    },
    {
        "Titulo": "Estoque",
        "Descricao": "Controlar quantidades",
        "Sigla": "ES",
        "Rota": "/estoque",
    },
    {
        "Titulo": "Fornecedores",
        "Descricao": "Cadastro de fornecedores",
        "Sigla": "FO",
        "Rota": "/fornecedores",
    },
]


def BuscarAtalhosDashboard():
    return AtalhosDashboard
