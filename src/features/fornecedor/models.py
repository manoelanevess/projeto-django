"""Modelos persistidos da feature de fornecedores."""
from django.db import models


class Fornecedor(models.Model):
    Nome = models.CharField(max_length=120, unique=True)
    Telefone = models.CharField(max_length=20, blank=True)
    Email = models.EmailField(blank=True)
    Cidade = models.CharField(max_length=80, blank=True)
    Ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ["Nome"]
        verbose_name = "fornecedor"
        verbose_name_plural = "fornecedores"

    def __str__(self):
        return self.Nome
