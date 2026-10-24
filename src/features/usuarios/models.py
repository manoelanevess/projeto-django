"""Identidade do comércio e foto de cada usuário autenticado."""
from django.conf import settings
from django.db import models

from componentes.NomesCadastro import NomesCadastroMixin


class ConfiguracaoComercio(NomesCadastroMixin, models.Model):
    CamposNomesCadastro = ("NomeComercio",)
    id = models.PositiveSmallIntegerField(primary_key=True, default=1, editable=False)
    NomeComercio = models.CharField(max_length=120, default="Controle de Estoque")

    class Meta:
        constraints = [models.CheckConstraint(condition=models.Q(id=1), name="ConfiguracaoComercioUnica")]
        verbose_name = "configuração do comércio"
        verbose_name_plural = "configurações do comércio"


class PerfilUsuario(models.Model):
    Usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="PerfilComercio")
    FotoConteudo = models.BinaryField(default=bytes, blank=True, editable=False)
    FotoTipo = models.CharField(max_length=30, blank=True)
    FotoVersao = models.CharField(max_length=64, blank=True)

    class Meta:
        verbose_name = "perfil do usuário"
        verbose_name_plural = "perfis dos usuários"
