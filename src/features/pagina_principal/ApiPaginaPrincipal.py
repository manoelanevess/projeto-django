"""Dados de apoio da Página Principal."""


AtalhosOperacionais = [
    {
        "Titulo": "Estoque",
        "Descricao": "Cadastrar produtos e ajustar quantidades",
        "Rota": "/estoque",
        "Sigla": "ES",
    },
    {
        "Titulo": "Dashboard",
        "Descricao": "Acompanhar indicadores e vendas",
        "Rota": "/dashboard",
        "Sigla": "DB",
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
