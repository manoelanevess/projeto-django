"""Consulta somente leitura a referencias verificadas e a familia Open Food Facts."""
import json
from functools import lru_cache as ArmazenarEmMemoria
from http.client import HTTPException
from pathlib import Path as Caminho
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit as SepararUrl
from urllib.request import Request as RequisicaoHttp, urlopen as AbrirUrl

from django.core.cache import cache as Cache

from .LogicaCatalogoProduto import ExtrairDadosCatalogo
from .LogicaCodigoBarras import EhCodigoGtin


PrefixoCacheCatalogo = "CatalogoProduto:v3:"
LimiteRespostaCatalogo = 65536
CatalogosPermitidos = {
    "openfoodfacts.org": ("food", "Open Food Facts"),
    "openbeautyfacts.org": ("beauty", "Open Beauty Facts"),
    "openproductsfacts.org": ("product", "Open Products Facts"),
    "openpetfoodfacts.org": ("petfood", "Open Pet Food Facts"),
}


def ObterFonteCatalogo(UrlResposta, Codigo):
    Url = SepararUrl(UrlResposta)
    DominioResposta = Url.hostname or ""
    for Dominio, (Tipo, Nome) in CatalogosPermitidos.items():
        if Url.scheme == "https" and (DominioResposta == Dominio or DominioResposta.endswith(f".{Dominio}")):
            return Tipo, {"Nome": Nome, "Url": f"https://world.{Dominio}/product/{Codigo}"}
    raise ValueError("O catalogo retornou uma fonte desconhecida.")


@ArmazenarEmMemoria(maxsize=1)
def ObterCatalogoComplementar():
    with Caminho(__file__).with_name("CatalogoComplementar.json").open(encoding="utf-8") as Arquivo:
        return json.load(Arquivo)


def ConsultarCatalogoProduto(Codigo):
    if not EhCodigoGtin(Codigo):
        return {"Situacao": "codigo_nao_consultavel", "Dados": {}}

    Referencia = ObterCatalogoComplementar().get(Codigo.lstrip("0"))
    if Referencia is not None:
        return {
            "Situacao": "encontrado",
            "Dados": Referencia["Dados"].copy(),
            "Fonte": Referencia["Fonte"].copy(),
        }

    ChaveCache = f"{PrefixoCacheCatalogo}{Codigo}"
    Resultado = Cache.get(ChaveCache)
    if Resultado is not None:
        return Resultado

    # Espaca as consultas novas; leituras repetidas usam o resultado em cache.
    if not Cache.add(f"{PrefixoCacheCatalogo}Intervalo", True, timeout=5):
        return {"Situacao": "indisponivel", "Dados": {}}

    Parametros = urlencode({
        "lc": "pt", "cc": "br", "tags_lc": "pt", "product_type": "all",
        "fields": "code,product_type,product_name,product_name_pt,brands,categories_tags,categories_tags_pt",
    })
    Requisicao = RequisicaoHttp(
        f"https://world.openfoodfacts.org/api/v3.6/product/{Codigo}?{Parametros}",
        headers={
            "Accept": "application/json",
            "User-Agent": "ControleEstoque/1.0 (https://github.com/manoelanevess/projeto-django)",
        },
    )
    Resultado = {"Situacao": "indisponivel", "Dados": {}}
    DuracaoCache = 30

    try:
        with AbrirUrl(Requisicao, timeout=4) as Resposta:
            TipoCatalogo, Fonte = ObterFonteCatalogo(Resposta.geturl(), Codigo)
            Conteudo = Resposta.read(LimiteRespostaCatalogo + 1)
        if len(Conteudo) > LimiteRespostaCatalogo:
            raise ValueError("Resposta do catalogo excedeu o limite.")
        DadosResposta = json.loads(Conteudo)
        if not isinstance(DadosResposta, dict):
            raise ValueError("Resposta do catalogo invalida.")
        ProdutoCatalogo = DadosResposta.get("product")
        if DadosResposta.get("status") == "success" and isinstance(ProdutoCatalogo, dict):
            CodigoResposta = str(ProdutoCatalogo.get("code", ""))
            if CodigoResposta.lstrip("0") != Codigo.lstrip("0"):
                raise ValueError("Codigo retornado pelo catalogo diverge da consulta.")
            Resultado = {
                "Situacao": "encontrado",
                "Dados": ExtrairDadosCatalogo(ProdutoCatalogo, TipoCatalogo),
                "Fonte": Fonte,
            }
            DuracaoCache = 86400
    except HTTPError as Erro:
        if Erro.code == 404:
            Resultado = {"Situacao": "nao_encontrado", "Dados": {}}
            DuracaoCache = 900
        Erro.close()
    except (URLError, OSError, HTTPException, ValueError):
        pass

    Cache.set(ChaveCache, Resultado, timeout=DuracaoCache)
    return Resultado
