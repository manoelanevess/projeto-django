"""Consulta opcional ao catalogo geral Cosmos, sem enviar dados da loja."""
import json
from hashlib import sha256
from http.client import HTTPException
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request as RequisicaoHttp, build_opener as CriarClienteHttp

from django.conf import settings as Configuracoes
from django.core.cache import cache as Cache
from django.utils import timezone

from .LogicaCatalogoProduto import LimparTextoCatalogo
from .LogicaCodigoBarras import EhCodigoGtin


LimiteRespostaEan = 65536


class RecusarRedirecionamento(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Nao encaminhar credenciais para outro endereco.
        return None


AbrirUrl = CriarClienteHttp(RecusarRedirecionamento()).open


def CatalogoEanEstaConfigurado():
    return bool(Configuracoes.COSMOS_API_TOKEN and Configuracoes.COSMOS_API_USER_AGENT)


def ConsultarCatalogoEan(Codigo):
    if not EhCodigoGtin(Codigo):
        return {"Situacao": "codigo_nao_consultavel", "Dados": {}}
    if not CatalogoEanEstaConfigurado():
        return {"Situacao": "nao_configurada", "Dados": {}}
    Identificador = sha256(Configuracoes.COSMOS_API_TOKEN.encode()).hexdigest()[:16]
    Prefixo = f"CatalogoEan:v1:{Identificador}:"
    Chave = f"{Prefixo}{Codigo.zfill(14)}"
    Resultado = Cache.get(Chave)
    if Resultado is not None:
        return Resultado
    if not Cache.add(f"{Prefixo}Intervalo", True, timeout=1):
        return {"Situacao": "limite", "Dados": {}}
    ChaveLimite = f"{Prefixo}Dia:{timezone.now().date().isoformat()}"
    Cache.add(ChaveLimite, 0, timeout=86400)
    try:
        Consultas = Cache.incr(ChaveLimite)
    except ValueError:
        return {"Situacao": "indisponivel", "Dados": {}}
    if Consultas > Configuracoes.COSMOS_LIMITE_DIARIO:
        return {"Situacao": "limite", "Dados": {}}

    Requisicao = RequisicaoHttp(
        f"https://api.cosmos.bluesoft.com.br/gtins/{Codigo}.json",
        headers={"Accept": "application/json", "X-Cosmos-Token": Configuracoes.COSMOS_API_TOKEN,
                 "User-Agent": Configuracoes.COSMOS_API_USER_AGENT},
    )
    Resultado = {"Situacao": "indisponivel", "Dados": {}}
    try:
        with AbrirUrl(Requisicao, timeout=4) as Resposta:
            Conteudo = Resposta.read(LimiteRespostaEan + 1)
        if len(Conteudo) > LimiteRespostaEan:
            raise ValueError("Resposta excedeu o limite.")
        Produto = json.loads(Conteudo)
        if not isinstance(Produto, dict) or str(Produto.get("gtin", "")).zfill(14) != Codigo.zfill(14):
            raise ValueError("Codigo retornado diverge da consulta.")
        Marca = Produto.get("brand")
        Marca = Marca.get("name") if isinstance(Marca, dict) else ""
        Dados = {
            "Nome": LimparTextoCatalogo(Produto.get("description"), 120),
            "Marca": LimparTextoCatalogo(LimparTextoCatalogo(Marca, 80).lower(), 80),
        }
        Dados = {Campo: Valor for Campo, Valor in Dados.items() if Valor}
        Resultado = {
            "Situacao": "encontrado" if Dados else "nao_encontrado", "Dados": Dados,
            "Fonte": {"Nome": "Cosmos", "Url": f"https://cosmos.bluesoft.com.br/produtos/{Codigo}", "CatalogoEan": True},
        }
    except HTTPError as Erro:
        if Erro.code == 404:
            Resultado = {"Situacao": "nao_encontrado", "Dados": {}}
        elif Erro.code == 429:
            Cache.set(f"{Prefixo}Intervalo", True, timeout=60)
            Resultado = {"Situacao": "limite", "Dados": {}}
        Erro.close()
    except (URLError, OSError, HTTPException, ValueError, TypeError):
        pass
    Duracao = 86400 if Resultado["Situacao"] == "encontrado" else 900 if Resultado["Situacao"] == "nao_encontrado" else 30
    Cache.set(Chave, Resultado, timeout=Duracao)
    return Resultado
