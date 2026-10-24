"""Configurações do comércio e envio da foto do proprietário."""
from django import forms

from componentes.NomesCadastro import NormalizarNomeCadastro


LimiteFotoPerfil = 2 * 1024 * 1024


def IdentificarTipoFoto(Conteudo):
    if Conteudo.startswith(b"\x89PNG\r\n\x1a\n") and Conteudo[12:16] == b"IHDR" and Conteudo.endswith(b"IEND\xaeB`\x82"):
        return "image/png"
    if Conteudo.startswith(b"\xff\xd8\xff") and Conteudo.endswith(b"\xff\xd9"):
        return "image/jpeg"
    if len(Conteudo) >= 20 and Conteudo[:4] == b"RIFF" and Conteudo[8:12] == b"WEBP" and Conteudo[12:16] in {b"VP8 ", b"VP8L", b"VP8X"}:
        if int.from_bytes(Conteudo[4:8], "little") + 8 == len(Conteudo):
            return "image/webp"
    raise forms.ValidationError("Escolha uma foto nos formatos JPG, PNG ou WebP.")


class FormularioConfiguracao(forms.Form):
    NomeComercio = forms.CharField(
        label="Nome do comércio", max_length=120,
        widget=forms.TextInput(attrs={"class": "CampoFormulario", "placeholder": "Ex.: Mercado Da Família", "autofocus": True}),
    )
    FotoPerfil = forms.FileField(
        label="Foto de perfil", required=False,
        widget=forms.FileInput(attrs={"class": "CampoFormulario", "accept": "image/jpeg,image/png,image/webp"}),
    )

    def clean_NomeComercio(self):
        Nome = NormalizarNomeCadastro(self.cleaned_data["NomeComercio"])
        if not Nome:
            raise forms.ValidationError("Informe o nome do comércio.")
        if len(Nome) > 120:
            raise forms.ValidationError("Use no máximo 120 caracteres.")
        return Nome

    def clean_FotoPerfil(self):
        Foto = self.cleaned_data.get("FotoPerfil")
        if Foto is None:
            return None
        if Foto.size > LimiteFotoPerfil:
            raise forms.ValidationError("A foto deve ter no máximo 2 MB.")
        Conteudo = Foto.read(LimiteFotoPerfil + 1)
        if len(Conteudo) > LimiteFotoPerfil:
            raise forms.ValidationError("A foto deve ter no máximo 2 MB.")
        return {"Conteudo": Conteudo, "Tipo": IdentificarTipoFoto(Conteudo)}
