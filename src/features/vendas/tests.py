"""Testes do carrinho, pagamento e baixa automática do estoque."""
from decimal import Decimal

from django.contrib.auth import get_user_model as ObterModeloUsuario
from django.test import TestCase

from features.fornecedor.models import Fornecedor
from features.produtos.models import Produto

from .models import Venda


class TesteCarrinhosVenda(TestCase):
    def setUp(self):
        self.Usuario = ObterModeloUsuario().objects.create_user(
            username="proprietario_vendas",
            password="SenhaTeste123!",
        )
        self.client.force_login(self.Usuario)
        self.Distribuidora = Fornecedor.objects.create(
            Nome="Distribuidora Central"
        )
        self.Hortifruti = Fornecedor.objects.create(Nome="Hortifruti Silva")
        self.Arroz = Produto.objects.create(
            Nome="Arroz 1 kg",
            Categoria="Mercearia",
            Fornecedor=self.Distribuidora,
            UnidadeVenda=Produto.UNIDADE,
            QuantidadeEstoque=Decimal("10.000"),
            EstoqueMinimo=Decimal("2.000"),
            PrecoVenda=Decimal("10.00"),
        )
        self.Batata = Produto.objects.create(
            Nome="Batata",
            Categoria="Hortifruti",
            Marca="Produto a granel",
            Fornecedor=self.Hortifruti,
            UnidadeVenda=Produto.QUILOGRAMA,
            QuantidadeEstoque=None,
            EstoqueMinimo=None,
            PrecoVenda=Decimal("4.00"),
            Disponivel=True,
        )

    def AdicionarProduto(self, NumeroCarrinho, ProdutoVenda, Quantidade):
        return self.client.post(
            "/carrinho/adicionar",
            {
                "carrinho": NumeroCarrinho,
                "produto": ProdutoVenda.id,
                "quantidade": Quantidade,
            },
        )

    def test_PesquisaIncrementalFiltraProdutosACadaTrechoDigitado(self):
        RespostaA = self.client.get("/carrinho/pesquisar", {"busca": "A"})
        RespostaAr = self.client.get("/carrinho/pesquisar", {"busca": "Ar"})
        RespostaArroz = self.client.get("/carrinho/pesquisar", {"busca": "Arroz"})

        self.assertEqual(RespostaA.status_code, 200)
        self.assertCountEqual(
            [Produto["Nome"] for Produto in RespostaA.json()["Produtos"]],
            ["Arroz 1 kg", "Batata"],
        )
        self.assertEqual(
            [Produto["Nome"] for Produto in RespostaAr.json()["Produtos"]],
            ["Arroz 1 kg"],
        )
        self.assertEqual(
            [Produto["Nome"] for Produto in RespostaArroz.json()["Produtos"]],
            ["Arroz 1 kg"],
        )

    def test_PesquisaIncrementalVaziaRetornaListaVaziaEFormularioContinuaDisponivel(self):
        RespostaBusca = self.client.get("/carrinho/pesquisar", {"busca": ""})
        PaginaCarrinho = self.client.get("/carrinho?carrinho=1")

        self.assertEqual(RespostaBusca.json(), {"Produtos": []})
        self.assertContains(PaginaCarrinho, 'id="BuscaProdutoCarrinho"')
        self.assertContains(PaginaCarrinho, "/carrinho/pesquisar")
        self.assertContains(PaginaCarrinho, 'type="submit">Pesquisar</button>')

    def test_TresCarrinhosMantemAtendimentosIndependentes(self):
        self.AdicionarProduto("1", self.Arroz, "1")
        self.AdicionarProduto("2", self.Batata, "0.750")

        Carrinhos = self.client.session["CarrinhosVenda"]

        self.assertEqual(Carrinhos["1"][str(self.Arroz.id)], "1.000")
        self.assertEqual(Carrinhos["2"][str(self.Batata.id)], "0.750")
        self.assertNotIn("3", Carrinhos)

        self.client.post("/carrinho/cancelar", {"carrinho": "1"})
        CarrinhosAposCancelar = self.client.session["CarrinhosVenda"]

        self.assertNotIn("1", CarrinhosAposCancelar)
        self.assertIn("2", CarrinhosAposCancelar)
        self.Arroz.refresh_from_db()
        self.assertEqual(self.Arroz.QuantidadeEstoque, Decimal("10.000"))

    def test_DinheiroCalculaTrocoEBaixaUnidadeSemBaixarProdutoPorPeso(self):
        self.AdicionarProduto("1", self.Arroz, "2")
        self.AdicionarProduto("1", self.Batata, "1.500")

        Resposta = self.client.post(
            "/carrinho/concluir",
            {
                "carrinho": "1",
                "forma_pagamento": Venda.DINHEIRO,
                "valor_recebido": "30,00",
            },
        )

        self.assertEqual(Resposta.status_code, 302)
        VendaConcluida = Venda.objects.get()
        self.assertEqual(VendaConcluida.Total, Decimal("26.00"))
        self.assertEqual(VendaConcluida.ValorRecebido, Decimal("30.00"))
        self.assertEqual(VendaConcluida.Troco, Decimal("4.00"))
        self.assertEqual(VendaConcluida.Itens.count(), 2)

        self.Arroz.refresh_from_db()
        self.Batata.refresh_from_db()
        self.assertEqual(self.Arroz.QuantidadeEstoque, Decimal("8.000"))
        self.assertIsNone(self.Batata.QuantidadeEstoque)
        self.assertTrue(self.Batata.Disponivel)
        self.assertNotIn("1", self.client.session.get("CarrinhosVenda", {}))

    def test_PixNaoExigeValorRecebido(self):
        self.AdicionarProduto("3", self.Arroz, "1")

        self.client.post(
            "/carrinho/concluir",
            {
                "carrinho": "3",
                "forma_pagamento": Venda.PIX,
            },
        )

        VendaConcluida = Venda.objects.get()
        self.assertEqual(VendaConcluida.Total, Decimal("10.00"))
        self.assertIsNone(VendaConcluida.ValorRecebido)
        self.assertEqual(VendaConcluida.Troco, Decimal("0.00"))

    def test_EstoqueInsuficienteImpedeTodaABaixa(self):
        self.AdicionarProduto("2", self.Arroz, "2")
        self.AdicionarProduto("2", self.Batata, "1")
        self.Arroz.QuantidadeEstoque = Decimal("1.000")
        self.Arroz.save(update_fields=["QuantidadeEstoque"])

        self.client.post(
            "/carrinho/concluir",
            {
                "carrinho": "2",
                "forma_pagamento": Venda.PIX,
            },
        )

        self.assertFalse(Venda.objects.exists())
        self.Arroz.refresh_from_db()
        self.Batata.refresh_from_db()
        self.assertEqual(self.Arroz.QuantidadeEstoque, Decimal("1.000"))
        self.assertIsNone(self.Batata.QuantidadeEstoque)
        self.assertIn("2", self.client.session["CarrinhosVenda"])

    def test_ProdutoPorUnidadeNaoAceitaFracao(self):
        self.AdicionarProduto("1", self.Arroz, "0.500")

        self.assertNotIn("CarrinhosVenda", self.client.session)

    def test_NumeroDeCarrinhoInvalidoNaoAlteraOutroAtendimento(self):
        self.AdicionarProduto("1", self.Arroz, "1")

        self.client.post("/carrinho/cancelar", {"carrinho": "4"})

        self.assertIn("1", self.client.session["CarrinhosVenda"])

    def test_PaginaPrincipalMantemCarrinhosAbertosAposAdicionar(self):
        Resposta = self.client.post(
            "/carrinho/adicionar",
            {
                "carrinho": "2",
                "produto": self.Arroz.id,
                "quantidade": "1",
                "retorno": "pagina-principal",
                "carrinhos_abertos": "1,2",
                "busca": "arroz",
            },
        )

        self.assertEqual(
            Resposta.url,
            "/?carrinho=2&carrinhos_abertos=1%2C2&busca_carrinho=arroz",
        )
        PaginaPrincipal = self.client.get(Resposta.url)
        self.assertContains(PaginaPrincipal, "PainelCarrinho-1")
        self.assertContains(PaginaPrincipal, "PainelCarrinho-2")
        self.assertContains(PaginaPrincipal, "Arroz 1 kg")

    def test_ConsultaDaPaginaPrincipalNaoExibeAcoesDeEdicao(self):
        Resposta = self.client.get("/?busca=arroz")

        self.assertContains(Resposta, "Consulta do estoque")
        self.assertContains(Resposta, "Arroz 1 kg")
        self.assertContains(Resposta, "Marca")
        self.assertNotContains(Resposta, "Editar produto")
        self.assertNotContains(Resposta, "Excluir produto")

    def test_NomeDoClienteEGravadoNaVendaEResetadoNoCarrinho(self):
        self.client.post(
            "/carrinho/nome",
            {
                "carrinho": "2",
                "nome_cliente": "  Maria   da Silva  ",
                "retorno": "pagina-principal",
                "carrinhos_abertos": "2",
            },
        )

        self.assertEqual(
            self.client.session["NomesCarrinhosVenda"]["2"],
            "Maria da Silva",
        )
        self.assertContains(self.client.get("/"), "Maria da Silva")
        PaginaCarrinho = self.client.get("/carrinho?carrinho=2")
        self.assertContains(PaginaCarrinho, "Maria da Silva")
        self.assertContains(PaginaCarrinho, "Editar nome do carrinho 2")

        self.AdicionarProduto("2", self.Arroz, "1")
        self.client.post(
            "/carrinho/concluir",
            {
                "carrinho": "2",
                "forma_pagamento": Venda.PIX,
            },
        )

        VendaConcluida = Venda.objects.get()
        self.assertEqual(VendaConcluida.NomeCliente, "Maria da Silva")
        self.assertNotIn("2", self.client.session.get("NomesCarrinhosVenda", {}))
        self.assertNotContains(self.client.get("/"), "Maria da Silva")
        self.assertContains(self.client.get("/dashboard"), "Maria da Silva")

    def test_CancelarCarrinhoTambemResetaONome(self):
        self.client.post(
            "/carrinho/nome",
            {"carrinho": "1", "nome_cliente": "Cliente conhecido"},
        )

        self.client.post("/carrinho/cancelar", {"carrinho": "1"})

        self.assertNotIn("1", self.client.session.get("NomesCarrinhosVenda", {}))
        self.assertContains(self.client.get("/"), "Carrinho 1")
