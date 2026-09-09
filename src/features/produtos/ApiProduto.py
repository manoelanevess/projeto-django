"""Camada de API inicial da feature de produtos."""


ProdutosIniciais = [
    {
        "Nome": "Caderno",
        "Categoria": "Papelaria",
        "Quantidade": 24,
        "EstoqueMinimo": 10,
        "ValorUnitario": 18.9,
    },
    {
        "Nome": "Caneta",
        "Categoria": "Papelaria",
        "Quantidade": 8,
        "EstoqueMinimo": 15,
        "ValorUnitario": 2.5,
    },
    {
        "Nome": "Mouse",
        "Categoria": "Informática",
        "Quantidade": 12,
        "EstoqueMinimo": 6,
        "ValorUnitario": 59.9,
    },
    {
        "Nome": "Teclado",
        "Categoria": "Informática",
        "Quantidade": 5,
        "EstoqueMinimo": 8,
        "ValorUnitario": 86.0,
    },
]


def BuscarProdutosIniciais():
    return ProdutosIniciais
