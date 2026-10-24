"""Catalogo persistente separado de produtos, precos e lotes da loja."""
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from componentes.NomesCadastro import NormalizarNomeCadastro
from .LogicaCatalogoProduto import LimparTextoCatalogo
from .LogicaCodigoBarras import EhCodigoGtin
from .models import IdentificacaoProduto


def ObterIdentificacaoProduto(Codigo):
    if not EhCodigoGtin(Codigo):
        return None
    Registro = IdentificacaoProduto.objects.filter(CodigoBarras=Codigo.zfill(14)).first()
    if Registro is None or (not Registro.Confirmada and Registro.AtualizadaEm < timezone.now() - timedelta(hours=24)):
        return None
    return Registro


def SerializarIdentificacaoProduto(Registro):
    Dados = {Campo: getattr(Registro, Campo) for Campo in ("Nome", "Marca") if getattr(Registro, Campo)}
    Fontes = []
    for Campo in Dados:
        Fonte = Registro.Fontes.get(Campo)
        if Fonte and Fonte not in Fontes:
            Fontes.append(Fonte)
    return {"Situacao": "encontrado", "Dados": Dados, "Fontes": Fontes,
            "Completo": Registro.Confirmada or bool(Registro.Nome and Registro.Marca)}


@transaction.atomic
def GuardarIdentificacaoProduto(Codigo, Resultado, Confirmada=False):
    if not EhCodigoGtin(Codigo):
        return Resultado
    Dados = Resultado.get("Dados", {})
    Dados = {
        "Nome": LimparTextoCatalogo(NormalizarNomeCadastro(LimparTextoCatalogo(Dados.get("Nome"), 120)), 120),
        "Marca": LimparTextoCatalogo(NormalizarNomeCadastro(LimparTextoCatalogo(Dados.get("Marca"), 80)), 80),
    }
    if not any(Dados.values()):
        Registro = ObterIdentificacaoProduto(Codigo)
        return SerializarIdentificacaoProduto(Registro) if Registro is not None else {"Situacao": "nao_encontrado", "Dados": {}}
    Registro, _ = IdentificacaoProduto.objects.get_or_create(CodigoBarras=Codigo.zfill(14))
    Registro = IdentificacaoProduto.objects.select_for_update().get(pk=Registro.pk)
    if Registro.Confirmada and not Confirmada:
        return SerializarIdentificacaoProduto(Registro)
    ValoresAnteriores = (Registro.Nome, Registro.Marca, Registro.Fontes.copy(), Registro.Confirmada)
    Expirou = not Registro.Confirmada and Registro.AtualizadaEm < timezone.now() - timedelta(hours=24)
    if Expirou:
        Registro.Nome = Registro.Marca = ""
        Registro.Fontes = {}
    for Campo, Valor in Dados.items():
        if Confirmada or (Valor and not getattr(Registro, Campo)):
            if Confirmada and Valor != getattr(Registro, Campo):
                Registro.Fontes.pop(Campo, None)
            setattr(Registro, Campo, Valor)
            Fonte = Resultado.get("Fonte")
            if Fonte and not Confirmada:
                Registro.Fontes[Campo] = Fonte
    Registro.Confirmada = Confirmada
    if Expirou or ValoresAnteriores != (Registro.Nome, Registro.Marca, Registro.Fontes, Registro.Confirmada):
        Registro.save()
    return SerializarIdentificacaoProduto(Registro)


def ConfirmarIdentificacaoProduto(Produto):
    GuardarIdentificacaoProduto(Produto.CodigoBarras, {
        "Dados": {"Nome": Produto.Nome, "Marca": Produto.Marca},
    }, Confirmada=True)
