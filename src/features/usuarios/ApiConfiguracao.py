"""Leitura da identidade visual compartilhada pelas páginas do comércio."""
from .models import ConfiguracaoComercio, PerfilUsuario


NomeComercioPadrao = "Controle de Estoque"


def ObterNomeComercio(Request=None):
    if Request is None:
        return NomeComercioPadrao
    if not hasattr(Request, "NomeComercioAtual"):
        Request.NomeComercioAtual = (ConfiguracaoComercio.objects.filter(pk=1)
                                    .values_list("NomeComercio", flat=True).first() or NomeComercioPadrao)
    return Request.NomeComercioAtual


def ObterFotoPerfilUrl(Request=None):
    Usuario = getattr(Request, "user", None)
    if not Usuario or not Usuario.is_authenticated:
        return ""
    if not hasattr(Request, "FotoPerfilUrlAtual"):
        Perfil = PerfilUsuario.objects.filter(Usuario=Usuario).only("FotoTipo", "FotoVersao").first()
        Request.FotoPerfilUrlAtual = f"/configuracoes/foto-perfil?v={Perfil.FotoVersao}" if Perfil and Perfil.FotoTipo else ""
    return Request.FotoPerfilUrlAtual


def ObterSiglaComercio(Nome):
    Palavras = [Palavra for Palavra in Nome.split() if Palavra.casefold() not in {"de", "da", "do", "das", "dos", "e"}]
    if len(Palavras) > 1:
        return "".join(Palavra[0] for Palavra in Palavras[:2]).upper()
    return Nome[:2].upper()
