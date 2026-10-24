"""Valores mascarados precisam manter o mesmo significado no servidor."""
from decimal import Decimal

from django import forms
from django.contrib.auth import get_user_model as ObterModeloUsuario
from django.test import SimpleTestCase, TestCase

from componentes.MascarasNumericas import EntradaNumerica
from features.fornecedor.models import Fornecedor
from features.vendas.LogicaCarrinho import ConverterQuantidade, ConverterValorRecebido
from features.vendas.LogicaContaCliente import ConverterValorConta

from .models import CategoriaProduto, Produto


class TesteValoresMascarados(SimpleTestCase):
    def test_MoedaAceitaFormatoBrasileiroEDecimalCanonico(self):
        class FormularioTeste(forms.Form):
            Valor = forms.DecimalField(max_digits=10, decimal_places=2, widget=EntradaNumerica(attrs={"step": "0.01"}))

        for Texto in ("1.234,56", "1234.56", "1234,56"):
            with self.subTest(Texto=Texto):
                Formulario = FormularioTeste({"Valor": Texto})
                self.assertTrue(Formulario.is_valid(), Formulario.errors)
                self.assertEqual(Formulario.cleaned_data["Valor"], Decimal("1234.56"))

    def test_QuantidadeMantemTresCasasEPagamentosMantemCentavos(self):
        self.assertEqual(ConverterQuantidade("1.234,567"), Decimal("1234.567"))
        self.assertEqual(ConverterQuantidade("10.000"), Decimal("10.000"))
        self.assertEqual(ConverterValorRecebido("1.234,56"), Decimal("1234.56"))
        self.assertEqual(ConverterValorConta("1.234,56"), Decimal("1234.56"))

    def test_PagamentoInvalidoContinuaRejeitado(self):
        for Texto in ("NaN", "Infinity", "-1,00"):
            with self.subTest(Texto=Texto):
                with self.assertRaises(ValueError):
                    ConverterValorConta(Texto)

    def test_EdicaoNaoTransformaMilharesEmFracoes(self):
        Moeda = EntradaNumerica(attrs={"step": "0.01"})
        Quantidade = EntradaNumerica(attrs={"step": "0.001"})
        Inteiro = EntradaNumerica(attrs={"step": "1"})
        self.assertEqual(Moeda.format_value(Decimal("1234.56")), "1.234,56")
        self.assertEqual(Quantidade.format_value(Decimal("1234.567")), "1.234,567")
        self.assertEqual(Inteiro.format_value(Decimal("1234.000")), "1234")


class TesteCadastroComMascara(TestCase):
    def test_CadastroSalvaPrecosEQuantidadeMascaradosEPreservaCodigo(self):
        Usuario = ObterModeloUsuario().objects.create_user(username="mascaras_numericas")
        self.client.force_login(Usuario)
        FornecedorTeste = Fornecedor.objects.create(Nome="Fornecedor máscaras")
        CategoriaProduto.objects.create(Nome="Material")
        Resposta = self.client.post("/estoque/novo", {
            "Nome": "Produto com máscara", "Categoria": "Material", "Marca": "Marca",
            "Fornecedor": FornecedorTeste.id, "CodigoBarras": "0012345678905",
            "UnidadeVenda": Produto.METRO, "PrecoCusto": "1.234,56", "PrecoVenda": "2.345,67",
            "QuantidadeEstoque": "1.000,250", "EstoqueMinimo": "2,500",
        })
        self.assertEqual(Resposta.status_code, 302)
        ProdutoCriado = Produto.objects.get(Nome="Produto Com Máscara")
        self.assertEqual(ProdutoCriado.PrecoCusto, Decimal("1234.56"))
        self.assertEqual(ProdutoCriado.PrecoVenda, Decimal("2345.67"))
        self.assertEqual(ProdutoCriado.QuantidadeEstoque, Decimal("1000.250"))
        self.assertEqual(ProdutoCriado.EstoqueMinimo, Decimal("2.500"))
        self.assertEqual(ProdutoCriado.CodigoBarras, "0012345678905")
