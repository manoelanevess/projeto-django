"""Normalizacao das sugestoes de cadastro recebidas do catalogo."""
from django.utils.html import strip_tags as RemoverMarcacoes


def LimparTextoCatalogo(Valor, Limite):
    if not isinstance(Valor, str):
        return ""
    Texto = " ".join(RemoverMarcacoes(Valor).split())
    if len(Texto) > Limite or any(ord(Caractere) < 32 for Caractere in Texto):
        return ""
    return Texto


def ExtrairDadosCatalogo(ProdutoCatalogo):
    Nome = LimparTextoCatalogo(ProdutoCatalogo.get("product_name_pt"), 120)
    Nome = Nome or LimparTextoCatalogo(ProdutoCatalogo.get("product_name"), 120)
    Marca = LimparTextoCatalogo(LimparTextoCatalogo(ProdutoCatalogo.get("brands"), 80).lower(), 80)
    return {
        Campo: Valor for Campo, Valor in {"Nome": Nome, "Marca": Marca}.items()
        if Valor
    }
