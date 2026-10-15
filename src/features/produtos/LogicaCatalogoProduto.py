"""Normalizacao das sugestoes de cadastro recebidas do catalogo."""
import re
from unicodedata import combining as EhCombinante, normalize as NormalizarUnicode

from django.utils.html import strip_tags as RemoverMarcacoes


TermosCategoriasCatalogo = {
    "Alimentos": (
        "alimento", "alimentos", "food", "foods", "bebidas", "beverages",
    ),
    "Farmácia": (
        "farmacia", "pharmacy", "medicamento", "medicamentos", "medicine", "medicines",
        "medication", "medications", "pharmaceutical", "pharmaceuticals", "higiene", "hygiene",
        "cosmetico", "cosmeticos", "cosmetics", "personal care", "oral care", "mouthwash",
        "sabonete", "sabonetes", "shampoo", "shampoos", "desodorante", "desodorantes",
        "creme dental", "toothpaste", "protetor solar", "sunscreen", "curativo", "curativos",
    ),
    "Ferragem": (
        "ferragem", "ferragens", "ferramenta", "ferramentas", "hardware", "tools", "fasteners",
        "parafuso", "parafusos", "screws", "prego", "pregos", "alicate", "alicates",
        "martelo", "martelos", "furadeira", "furadeiras", "broca", "brocas", "trena", "trenas",
        "building materials", "materiais de construcao", "plumbing", "electrical supplies",
    ),
    "Limpeza": (
        "limpeza", "cleaning products", "household cleaners", "household cleaning",
        "detergente", "detergentes", "detergent", "detergents", "dishwashing",
        "limpador sanitario", "toilet cleaner", "toilet cleaners", "laundry",
        "agua sanitaria", "bleach", "amaciante", "amaciantes", "fabric softeners",
        "desinfetante de uso geral", "desinfetante sanitario", "sabao em po",
    ),
}


def LimparTextoCatalogo(Valor, Limite):
    if not isinstance(Valor, str):
        return ""
    Texto = " ".join(RemoverMarcacoes(Valor).split())
    if len(Texto) > Limite or any(ord(Caractere) < 32 for Caractere in Texto):
        return ""
    return Texto


def NormalizarTextoClassificacao(Texto):
    SemAcentos = "".join(
        Caractere for Caractere in NormalizarUnicode("NFKD", Texto.casefold())
        if not EhCombinante(Caractere)
    )
    return " ".join(re.findall(r"[a-z0-9]+", SemAcentos))


def IdentificarCategoriaPorTexto(Textos):
    Texto = f" {' '.join(NormalizarTextoClassificacao(Valor) for Valor in Textos)} "
    Categorias = {
        Categoria for Categoria, Termos in TermosCategoriasCatalogo.items()
        if any(f" {Termo} " in Texto for Termo in Termos)
    }
    return Categorias.pop() if len(Categorias) == 1 else ""


def ClassificarCategoriaCatalogo(ProdutoCatalogo, TipoCatalogo=""):
    Tipo = LimparTextoCatalogo(ProdutoCatalogo.get("product_type"), 20).lower() or TipoCatalogo
    if Tipo in ("food", "petfood"):
        return "Alimentos"

    Categorias = []
    for Campo in ("categories_tags", "categories_tags_pt"):
        Valores = ProdutoCatalogo.get(Campo, [])
        if isinstance(Valores, list):
            Categorias.extend(
                Texto for Valor in Valores if (Texto := LimparTextoCatalogo(Valor, 160))
            )
    if Categorias:
        Categoria = IdentificarCategoriaPorTexto(Categorias)
        if Categoria:
            return Categoria
        return "Farmácia" if Tipo == "beauty" else ""

    Nome = LimparTextoCatalogo(ProdutoCatalogo.get("product_name_pt"), 120)
    Nome = Nome or LimparTextoCatalogo(ProdutoCatalogo.get("product_name"), 120)
    Categoria = IdentificarCategoriaPorTexto([Nome])
    return Categoria or ("Farmácia" if Tipo == "beauty" else "")


def ExtrairDadosCatalogo(ProdutoCatalogo, TipoCatalogo=""):
    Nome = LimparTextoCatalogo(ProdutoCatalogo.get("product_name_pt"), 120)
    Nome = Nome or LimparTextoCatalogo(ProdutoCatalogo.get("product_name"), 120)
    Marca = LimparTextoCatalogo(LimparTextoCatalogo(ProdutoCatalogo.get("brands"), 80).lower(), 80)
    Categoria = ClassificarCategoriaCatalogo(ProdutoCatalogo, TipoCatalogo)
    return {
        Campo: Valor for Campo, Valor in {"Nome": Nome, "Marca": Marca, "Categoria": Categoria}.items()
        if Valor
    }
