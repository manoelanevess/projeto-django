"""Dados de apoio da Página Principal."""


AtalhosOperacionais = [
    {
        "Titulo": "Produtos",
        "Descricao": "Consultar cadastro e preços",
        "Rota": "/produtos",
        "Sigla": "PR",
    },
    {
        "Titulo": "Estoque",
        "Descricao": "Acompanhar quantidades",
        "Rota": "/estoque",
        "Sigla": "ES",
    },
    {
        "Titulo": "Fornecedores",
        "Descricao": "Consultar fornecedores",
        "Rota": "/fornecedores",
        "Sigla": "FO",
    },
]


def BuscarAtalhosOperacionais():
    return AtalhosOperacionais
