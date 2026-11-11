"""A carga de demonstração deve preencher somente um banco vazio."""
from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from features.fornecedor.models import Fornecedor
from .models import CategoriaProduto, LoteEstoque, Produto


class TesteCargaDadosDemo(TestCase):
    def test_CriaDadosEExecutarNovamenteNaoDuplica(self):
        call_command("carregar_dados_demo", stdout=StringIO())

        self.assertEqual(Fornecedor.objects.count(), 3)
        self.assertEqual(CategoriaProduto.objects.count(), 5)
        self.assertEqual(Produto.objects.count(), 11)
        self.assertEqual(LoteEstoque.objects.count(), 11)

        call_command("carregar_dados_demo", stdout=StringIO())
        self.assertEqual(Fornecedor.objects.count(), 3)
        self.assertEqual(CategoriaProduto.objects.count(), 5)
        self.assertEqual(Produto.objects.count(), 11)
        self.assertEqual(LoteEstoque.objects.count(), 11)

    def test_NaoAlteraBancoComDadosExistentes(self):
        Fornecedor.objects.create(Nome="Fornecedor já cadastrado")

        call_command("carregar_dados_demo", stdout=StringIO())

        self.assertEqual(Fornecedor.objects.count(), 1)
        self.assertFalse(CategoriaProduto.objects.exists())
        self.assertFalse(Produto.objects.exists())
