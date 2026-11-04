"""Dados sintéticos somente para a cópia isolada de produção."""
import os
import json
import sys
from decimal import Decimal

from django.contrib.auth import get_user_model as ObterModeloUsuario
from features.fornecedor.models import Fornecedor
from features.produtos.models import CategoriaProduto, Produto

if os.environ.get("AMBIENTE_DIAGNOSTICO") != "1":
    raise RuntimeError("A preparação só pode rodar no Compose de diagnóstico.")

# Dados é recebido por stdin pelo comando administrativo, sem gravar a senha no Git.
Dados = json.load(sys.stdin)
Usuario, _ = ObterModeloUsuario().objects.get_or_create(username=Dados["usuario"])
Usuario.set_password(Dados["senha"])
Usuario.save()
FornecedorTeste, _ = Fornecedor.objects.get_or_create(Nome="Fornecedor Diagnostico")
CategoriaProduto.objects.get_or_create(Nome="Diagnostico")
for Numero in range(1, 61):
    Produto.objects.get_or_create(
        Nome=f"Produto Diagnostico {Numero:03}",
        defaults={
            "Categoria": "Diagnostico", "Marca": "Marca Teste",
            "Fornecedor": FornecedorTeste, "QuantidadeEstoque": Decimal("10.000"),
            "PrecoCusto": Decimal("2.50"), "PrecoVenda": Decimal("5.00"),
            "EstoqueMinimo": Decimal("1.000"),
        },
    )
print("Diagnostico preparado: usuario de teste, categoria, fornecedor e 60 produtos sinteticos.")
