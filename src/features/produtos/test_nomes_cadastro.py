"""Os nomes são padronizados no servidor, inclusive sem JavaScript."""
from decimal import Decimal

from django.contrib.auth import get_user_model as ObterModeloUsuario
from django.test import SimpleTestCase, TestCase

from componentes.NomesCadastro import NormalizarNomeCadastro
from features.fornecedor.models import Fornecedor
from features.vendas.models import ContaCliente, Venda

from .models import CategoriaProduto, IdentificacaoProduto, Produto


class TesteNormalizacaoNomes(SimpleTestCase):
    def test_CapitalizaTodasAsPalavrasPreservandoAcentos(self):
        for Informado, Esperado in (
            ("  arroz   branco  ", "Arroz Branco"),
            ("sabor da terra", "Sabor Da Terra"),
            ("DISTRIBUIDORA SÃO JOSÉ", "Distribuidora São José"),
            ("joão d'ávila", "João D'Ávila"),
            ("água-mineral", "Água-Mineral"),
            ("ac\u0327u\u0301car cristal", "Açúcar Cristal"),
            (None, ""),
        ):
            with self.subTest(Informado=Informado):
                self.assertEqual(NormalizarNomeCadastro(Informado), Esperado)


class TesteNomesCadastro(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.Usuario = ObterModeloUsuario().objects.create_user(username="nomes_cadastro")
        cls.Fornecedor = Fornecedor.objects.create(Nome="distribuidora são josé", Cidade="porto alegre")
        CategoriaProduto.objects.create(Nome="alimentos secos")
        CategoriaProduto.objects.create(Nome="alimentos integrais")

    def setUp(self):
        self.client.force_login(self.Usuario)

    def DadosProduto(self, **Dados):
        return {
            "Nome": "arroz branco", "Marca": "sabor da terra", "Categoria": "alimentos secos",
            "Fornecedor": self.Fornecedor.pk, "UnidadeVenda": Produto.UNIDADE,
            "PrecoCusto": "4,00", "PrecoVenda": "7,00", "QuantidadeEstoque": "10", "EstoqueMinimo": "1",
            **Dados,
        }

    def test_ProdutoMarcaECategoriaSaoSalvosComIniciaisMaiusculas(self):
        self.assertEqual(self.client.post("/estoque/novo", self.DadosProduto()).status_code, 302)
        ProdutoSalvo = Produto.objects.get()
        self.assertEqual((ProdutoSalvo.Nome, ProdutoSalvo.Marca, ProdutoSalvo.Categoria),
                         ("Arroz Branco", "Sabor Da Terra", "Alimentos Secos"))
        self.client.post(f"/estoque/{ProdutoSalvo.pk}/editar", {
            "Nome": "arroz integral", "Marca": "marca nova", "Categoria": "alimentos integrais", "EstoqueMinimo": "2",
        })
        ProdutoSalvo.refresh_from_db()
        self.assertEqual((ProdutoSalvo.Nome, ProdutoSalvo.Marca, ProdutoSalvo.Categoria),
                         ("Arroz Integral", "Marca Nova", "Alimentos Integrais"))

    def test_FornecedorECidadeNormalizamNoFormularioENoModelo(self):
        self.Fornecedor.refresh_from_db()
        self.assertEqual((self.Fornecedor.Nome, self.Fornecedor.Cidade), ("Distribuidora São José", "Porto Alegre"))
        self.assertEqual(self.client.post("/fornecedores/novo", {
            "Nome": "casa das embalagens", "Cidade": "são leopoldo", "Email": "VENDAS@EXEMPLO.TEST",
        }).status_code, 302)
        FornecedorSalvo = Fornecedor.objects.get(Nome="Casa Das Embalagens")
        self.assertEqual(FornecedorSalvo.Cidade, "São Leopoldo")
        self.assertEqual(FornecedorSalvo.Email, "vendas@exemplo.test")

    def test_ClienteDaSessaoDaVendaEDaContinhaSegueAMesmaRegra(self):
        self.client.post("/estoque/novo", self.DadosProduto())
        ProdutoSalvo = Produto.objects.get()
        self.client.post("/carrinho/nome", {"carrinho": "1", "nome_cliente": "maria da silva"})
        self.assertEqual(self.client.session["NomesCarrinhosVenda"]["1"], "Maria Da Silva")
        self.client.post("/carrinho/adicionar", {"carrinho": "1", "produto": ProdutoSalvo.pk, "quantidade": "1"})
        self.client.post("/carrinho/concluir", {"carrinho": "1", "forma_pagamento": Venda.CONTA_CLIENTE})
        VendaSalva = Venda.objects.get()
        self.assertEqual(VendaSalva.NomeCliente, "Maria Da Silva")
        self.assertEqual(VendaSalva.ContaCliente.NomeCliente, "Maria Da Silva")
        self.assertEqual(VendaSalva.Itens.get().NomeProduto, "Arroz Branco")

    def test_NaoCriaDuplicatasSoPelaCapitalizacao(self):
        self.client.post("/estoque/novo", self.DadosProduto())
        Resposta = self.client.post("/estoque/novo", self.DadosProduto(Nome="ARROZ BRANCO"))
        self.assertContains(Resposta, "Já existe um produto com este nome.")
        self.assertEqual(Produto.objects.count(), 1)
        Resposta = self.client.post("/fornecedores/novo", {"Nome": "DISTRIBUIDORA SÃO JOSÉ"})
        self.assertContains(Resposta, "Já existe um fornecedor com este nome.")
        self.assertEqual(Fornecedor.objects.count(), 1)

    def test_SaveParcialECatalogoTambemNormalizam(self):
        self.Fornecedor.Nome = "fornecedor de materiais"
        self.Fornecedor.Cidade = "novo hamburgo"
        self.Fornecedor.Ativo = False
        self.Fornecedor.save(update_fields=["Nome", "Cidade", "Ativo"])
        self.Fornecedor.refresh_from_db()
        self.assertEqual((self.Fornecedor.Nome, self.Fornecedor.Cidade), ("Fornecedor De Materiais", "Novo Hamburgo"))
        Registro = IdentificacaoProduto.objects.create(CodigoBarras="00012345678905", Nome="água mineral", Marca="fonte da serra")
        Registro.refresh_from_db()
        self.assertEqual((Registro.Nome, Registro.Marca), ("Água Mineral", "Fonte Da Serra"))
        Conta = ContaCliente.objects.create(Proprietario=self.Usuario, NomeCliente="joão da padaria")
        Conta.refresh_from_db()
        self.assertEqual(Conta.NomeCliente, "João Da Padaria")

    def test_CodigoEValoresNumericosSaoPreservados(self):
        self.client.post("/estoque/novo", self.DadosProduto(CodigoBarras="aB-001234"))
        ProdutoSalvo = Produto.objects.get()
        self.assertEqual(ProdutoSalvo.CodigoBarras, "aB-001234")
        self.assertEqual(ProdutoSalvo.PrecoVenda, Decimal("7.00"))
