"""Testes da manutenção de produtos na área de estoque."""
from decimal import Decimal

from django.contrib.auth import get_user_model as ObterModeloUsuario
from django.test import TestCase

from features.fornecedor.models import Fornecedor

from .models import LoteEstoque, Produto


class TesteManutencaoEstoque(TestCase):
    def setUp(self):
        self.Usuario = ObterModeloUsuario().objects.create_user(
            username="proprietario_estoque",
            password="SenhaTeste123!",
        )
        self.client.force_login(self.Usuario)
        self.Distribuidora = Fornecedor.objects.create(
            Nome="Distribuidora Central",
            Cidade="Porto Alegre",
        )
        self.Hortifruti = Fornecedor.objects.create(
            Nome="Hortifruti Silva",
            Cidade="Canoas",
        )
        self.Arroz = Produto.objects.create(
            Nome="Arroz Branco",
            Categoria="Mercearia",
            Marca="Sabor da Terra",
            Fornecedor=self.Distribuidora,
            UnidadeVenda=Produto.UNIDADE,
            QuantidadeEstoque=Decimal("12.000"),
            EstoqueMinimo=Decimal("3.000"),
            PrecoCusto=Decimal("5.00"),
            PrecoVenda=Decimal("8.50"),
        )

    def test_ProdutosRedirecionaParaEstoque(self):
        Resposta = self.client.get("/produtos")

        self.assertRedirects(Resposta, "/estoque")

    def test_CadastraProdutoPorPesoSemQuantidadeExata(self):
        Resposta = self.client.post(
            "/estoque/novo",
            {
                "Nome": "Tomate Italiano",
                "Categoria": "Hortifruti",
                "Marca": "Produto a granel",
                "Fornecedor": self.Hortifruti.id,
                "UnidadeVenda": Produto.QUILOGRAMA,
                "PrecoCusto": "4.20",
                "PrecoVenda": "6.90",
                "QuantidadeEstoque": "99",
                "EstoqueMinimo": "5",
                "Disponivel": "on",
            },
        )

        self.assertRedirects(Resposta, "/estoque")
        Tomate = Produto.objects.get(Nome="Tomate Italiano")
        self.assertIsNone(Tomate.QuantidadeEstoque)
        self.assertIsNone(Tomate.EstoqueMinimo)
        self.assertTrue(Tomate.Disponivel)
        self.assertEqual(Tomate.Fornecedor, self.Hortifruti)

    def test_BuscaPorFornecedorEFiltroDeCategoria(self):
        RespostaFornecedor = self.client.get(
            "/estoque",
            {"busca": "Distribuidora Central"},
        )
        RespostaCategoria = self.client.get(
            "/estoque",
            {"categoria": "Mercearia"},
        )
        RespostaFiltroFornecedor = self.client.get(
            "/estoque",
            {"fornecedor": self.Distribuidora.id},
        )

        self.assertContains(RespostaFornecedor, "Arroz Branco")
        self.assertContains(RespostaCategoria, "Arroz Branco")
        self.assertContains(RespostaCategoria, "Sabor da Terra")
        self.assertContains(RespostaFiltroFornecedor, "Arroz Branco")
        self.assertContains(
            RespostaFiltroFornecedor,
            '<option value="{}" selected>'.format(self.Distribuidora.id),
            html=False,
        )

    def test_EditaProduto(self):
        Resposta = self.client.post(
            f"/estoque/{self.Arroz.id}/editar",
            {
                "acao": "salvar_produto",
                "Nome": "Arroz Branco 1 kg",
                "Categoria": "Alimentos",
                "Marca": "Sabor da Terra",
                "UnidadeVenda": Produto.UNIDADE,
                "EstoqueMinimo": "4",
            },
        )

        self.assertRedirects(Resposta, f"/estoque/{self.Arroz.id}/editar")
        self.Arroz.refresh_from_db()
        self.assertEqual(self.Arroz.Nome, "Arroz Branco 1 kg")
        self.assertEqual(self.Arroz.Categoria, "Alimentos")
        self.assertEqual(self.Arroz.PrecoCusto, Decimal("5.00"))
        self.assertEqual(self.Arroz.QuantidadeEstoque, Decimal("12.000"))

    def test_AdicionaNovaEntradaSemAlterarLoteAnterior(self):
        LoteAnterior = self.Arroz.LotesEstoque.get()

        Resposta = self.client.post(
            f"/estoque/{self.Arroz.id}/editar",
            {
                "acao": "adicionar_lote",
                "Lote-Fornecedor": self.Distribuidora.id,
                "Lote-PrecoCusto": "5.75",
                "Lote-PrecoVenda": "9.25",
                "Lote-QuantidadeEntrada": "6",
            },
        )

        self.assertRedirects(Resposta, f"/estoque/{self.Arroz.id}/editar")
        self.assertEqual(self.Arroz.LotesEstoque.count(), 2)
        LoteAnterior.refresh_from_db()
        self.assertEqual(LoteAnterior.QuantidadeDisponivel, Decimal("12.000"))
        self.assertEqual(LoteAnterior.PrecoCusto, Decimal("5.00"))

        NovoLote = LoteEstoque.objects.exclude(pk=LoteAnterior.pk).get()
        self.assertEqual(NovoLote.QuantidadeDisponivel, Decimal("6.000"))
        self.assertEqual(NovoLote.PrecoCusto, Decimal("5.75"))
        self.assertEqual(NovoLote.PrecoVenda, Decimal("9.25"))
        self.Arroz.refresh_from_db()
        self.assertEqual(self.Arroz.QuantidadeEstoque, Decimal("18.000"))
        self.assertContains(self.client.get(Resposta.url), "Entradas de estoque")

    def test_ExclusaoLogicaPreservaProdutoEEscondeDaLista(self):
        Resposta = self.client.post(f"/estoque/{self.Arroz.id}/excluir")

        self.assertRedirects(Resposta, "/estoque")
        self.Arroz.refresh_from_db()
        self.assertFalse(self.Arroz.Ativo)
        self.assertFalse(self.Arroz.Disponivel)
        self.assertNotContains(self.client.get("/estoque"), "Arroz Branco")

    def test_DashboardMantemIndicadoresEHistorico(self):
        Resposta = self.client.get("/dashboard")

        self.assertContains(Resposta, "Dashboard")
        self.assertContains(Resposta, "Produtos cadastrados")
        self.assertContains(Resposta, "Valor do estoque")
        self.assertContains(Resposta, "R$ 60,00")
        self.assertContains(Resposta, "Faturamento hoje")
        self.assertContains(Resposta, "Entradas, custos e lucro dos produtos")
        self.assertContains(Resposta, "Vendas recentes")

    def test_TabelasDeProdutosExibemCustoAoLadoDaVenda(self):
        PaginaEstoque = self.client.get("/estoque")
        PaginaPrincipal = self.client.get("/")

        for Resposta in [PaginaEstoque, PaginaPrincipal]:
            with self.subTest(Rota=Resposta.request["PATH_INFO"]):
                self.assertContains(Resposta, "Preço de custo")
                self.assertContains(Resposta, "Preço de venda")
                self.assertContains(Resposta, "R$ 5,00")
                self.assertContains(Resposta, "R$ 8,50")
