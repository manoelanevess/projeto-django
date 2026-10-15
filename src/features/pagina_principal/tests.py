"""Testes da consulta de estoque somente leitura na pagina principal."""
from copy import deepcopy
from decimal import Decimal

from django.contrib.auth import get_user_model as ObterModeloUsuario
from django.test import RequestFactory, TestCase

from features.fornecedor.models import Fornecedor
from features.produtos.models import Produto

from .LogicaPaginaPrincipal import GerarDadosPaginaPrincipal


class TesteConsultaEstoquePaginaPrincipal(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.Usuario = ObterModeloUsuario().objects.create_user(username="consulta_pagina_principal")
        cls.FornecedorTeste = Fornecedor.objects.create(Nome="Distribuidora Agua")
        cls.Agua = Produto.objects.create(
            Nome="Água mineral", CodigoBarras="0012345678905", Categoria="Alimentos",
            Fornecedor=cls.FornecedorTeste, QuantidadeEstoque=Decimal("5.000"),
            PrecoCusto=Decimal("2.00"), PrecoVenda=Decimal("3.00"),
        )
        Produto.objects.create(
            Nome="Pacote Água", Fornecedor=cls.FornecedorTeste,
            QuantidadeEstoque=Decimal("2.000"), PrecoVenda=Decimal("4.00"),
        )
        Produto.objects.create(
            Nome="Água inativa", Ativo=False, Fornecedor=cls.FornecedorTeste, PrecoVenda=Decimal("3.00"),
        )

    def setUp(self):
        self.client.force_login(self.Usuario)

    def ObterNomesConsulta(self, Busca):
        Request = RequestFactory().get("/", {"busca": Busca, "inicio": "1"})
        Request.session = self.client.session
        Dados = GerarDadosPaginaPrincipal(Request, BuscaEstoque=Busca)
        return [Item["Nome"] for Item in Dados["ConsultaEstoque"]["Produtos"]]

    def test_BuscaPorInicioIgnoraAcentosEMaiusculasSemIncluirMarcaOuFornecedor(self):
        self.assertEqual(self.ObterNomesConsulta("AGU"), ["Água mineral"])
        self.assertEqual(self.ObterNomesConsulta("00123"), ["Água mineral"])
        self.assertEqual(self.ObterNomesConsulta("Distribuidora"), [])

    def test_LimparMostraTodosOsAtivosETermoAusenteRetornaVazio(self):
        self.assertCountEqual(self.ObterNomesConsulta(""), ["Água mineral", "Pacote Água"])
        self.assertEqual(self.ObterNomesConsulta("inexistente"), [])

    def test_FormularioIncrementalMantemConsultaSomenteLeitura(self):
        Resposta = self.client.get("/", {"busca": "AGU", "inicio": "1"})
        for Identificador in ("FormularioConsultaEstoque", "BuscaConsultaEstoque", "ResultadosConsultaEstoque", "ErroConsultaEstoque"):
            self.assertContains(Resposta, f'id="{Identificador}"')
        self.assertContains(Resposta, 'Campo.addEventListener("input"')
        self.assertContains(Resposta, "Endereco.search = window.location.search")
        self.assertNotContains(Resposta, f'href="/estoque/{self.Agua.id}/editar"')
        Vazio = self.client.get("/", {"busca": "inexistente", "inicio": "1"})
        self.assertContains(Vazio, "Nenhum produto encontrado")

    def test_PesquisarNaoAlteraCarrinhoNemEstoque(self):
        self.client.get("/")
        self.client.post("/carrinho/adicionar", {"carrinho": "1", "produto": self.Agua.id, "quantidade": "1"})
        CarrinhosAntes = deepcopy(self.client.session.get("CarrinhosVenda"))
        NumerosAntes = deepcopy(self.client.session.get("NumerosCarrinhosVenda"))
        self.assertTrue(CarrinhosAntes)
        for Busca in ("agu", "", "inexistente"):
            self.client.get("/", {"busca": Busca, "inicio": "1"})
        self.assertEqual(self.client.session.get("CarrinhosVenda"), CarrinhosAntes)
        self.assertEqual(self.client.session.get("NumerosCarrinhosVenda"), NumerosAntes)
        self.Agua.refresh_from_db()
        self.assertEqual(self.Agua.QuantidadeEstoque, Decimal("5.000"))
        self.assertEqual(self.Agua.LotesEstoque.count(), 1)
