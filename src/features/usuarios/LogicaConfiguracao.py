"""Gravação conjunta das configurações e da foto validada."""
from hashlib import sha256 as GerarSha256

from django.db import transaction

from .models import ConfiguracaoComercio, PerfilUsuario


@transaction.atomic
def SalvarConfiguracao(Usuario, Dados):
    Configuracao, _ = ConfiguracaoComercio.objects.get_or_create(pk=1)
    Configuracao.NomeComercio = Dados["NomeComercio"]
    Configuracao.save(update_fields=["NomeComercio"])
    Foto = Dados.get("FotoPerfil")
    if Foto is not None:
        Perfil, _ = PerfilUsuario.objects.get_or_create(Usuario=Usuario)
        Perfil.FotoConteudo = Foto["Conteudo"]
        Perfil.FotoTipo = Foto["Tipo"]
        Perfil.FotoVersao = GerarSha256(Foto["Conteudo"]).hexdigest()
        Perfil.save(update_fields=["FotoConteudo", "FotoTipo", "FotoVersao"])
