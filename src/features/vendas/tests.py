"""Testes do carrinho, pagamento e baixa automática do estoque."""
from datetime import date, datetime
from decimal import Decimal

from django.contrib.auth import get_user_model as ObterModeloUsuario
from django.test import TestCase
from django.utils import timezone

from features.fornecedor.models import Fornecedor
from features.produtos.models import LoteEstoque, Produto

from .LogicaCarrinho import ObterChaveLote
from .LogicaVenda import ConsolidarVendasDeMesesAnteriores, ObterResumoFinanceiro
from .models import (
    ContaCliente,
    LancamentoContaCliente,
    RegistroVendaAntiga,
    ResumoVendaMensal,
    Venda,
)


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
            PrecoCusto=Decimal("6.00"),
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
            PrecoCusto=Decimal("2.50"),
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

    def CriarNovoLoteArroz(self):
        LoteNovo = LoteEstoque.objects.create(
            Produto=self.Arroz,
            Fornecedor=self.Distribuidora,
            QuantidadeInicial=Decimal("5.000"),
            QuantidadeDisponivel=Decimal("5.000"),
            PrecoCusto=Decimal("7.00"),
            PrecoVenda=Decimal("12.00"),
        )
        self.Arroz.SincronizarResumoLotes()
        return LoteNovo

    def test_PesquisaDoCarrinhoIgnoraAcentos(self):
        Produto.objects.create(
            Nome="Feijão Carioca",
            Categoria="Alimentos",
            Marca="Sabor da Terra",
            Fornecedor=self.Distribuidora,
            UnidadeVenda=Produto.UNIDADE,
            QuantidadeEstoque=Decimal("8.000"),
            EstoqueMinimo=Decimal("2.000"),
            PrecoCusto=Decimal("4.00"),
            PrecoVenda=Decimal("7.00"),
        )

        Resposta = self.client.get("/carrinho/pesquisar", {"busca": "feijao"})

        self.assertEqual(
            [ProdutoVenda["Nome"] for ProdutoVenda in Resposta.json()["Produtos"]],
            ["Feijão Carioca"],
        )

    def test_CarrinhoMostraMarcaAoLadoDoNomeDoProduto(self):
        self.Arroz.Marca = "Tordilho"
        self.Arroz.save(update_fields=["Marca"])
        self.AdicionarProduto("1", self.Arroz, "1")

        Resposta = self.client.get("/carrinho", {"busca": "Arroz"})

        self.assertContains(
            Resposta,
            '<span class="MarcaProduto">Tordilho</span>',
            html=True,
        )

    def test_NaoExcluiLoteUsadoEmVenda(self):
        Lote = self.Arroz.LotesEstoque.get()
        self.AdicionarProduto("1", self.Arroz, "1")
        self.client.post(
            "/carrinho/concluir",
            {"carrinho": "1", "forma_pagamento": Venda.PIX},
        )

        Resposta = self.client.post(
            f"/estoque/{self.Arroz.id}/lotes/{Lote.id}/excluir",
            follow=True,
        )

        self.assertTrue(LoteEstoque.objects.filter(pk=Lote.pk).exists())
        self.assertContains(Resposta, "possui vendas registradas")

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

        ChaveLoteArroz = ObterChaveLote(self.Arroz.LotesEstoque.get().id)
        ChaveLoteBatata = ObterChaveLote(self.Batata.LotesEstoque.get().id)
        self.assertEqual(Carrinhos["1"][ChaveLoteArroz], "1.000")
        self.assertEqual(Carrinhos["2"][ChaveLoteBatata], "0.750")
        self.assertNotIn("3", Carrinhos)

        self.client.post("/carrinho/cancelar", {"carrinho": "1"})
        CarrinhosAposCancelar = self.client.session["CarrinhosVenda"]

        self.assertNotIn("1", CarrinhosAposCancelar)
        self.assertIn("2", CarrinhosAposCancelar)
        self.Arroz.refresh_from_db()
        self.assertEqual(self.Arroz.QuantidadeEstoque, Decimal("10.000"))

    def test_CarrinhoAntigoEConvertidoParaOLoteInicial(self):
        Sessao = self.client.session
        Sessao["CarrinhosVenda"] = {
            "1": {str(self.Arroz.id): "2.000"}
        }
        Sessao.save()

        Resposta = self.client.get("/carrinho?carrinho=1")

        self.assertContains(Resposta, "Arroz 1 kg")
        ChaveEsperada = ObterChaveLote(self.Arroz.LotesEstoque.get().id)
        self.assertEqual(
            self.client.session["CarrinhosVenda"]["1"],
            {ChaveEsperada: "2.000"},
        )

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
        self.assertEqual(VendaConcluida.Lucro, Decimal("10.25"))
        self.assertEqual(VendaConcluida.ValorRecebido, Decimal("30.00"))
        self.assertEqual(VendaConcluida.Troco, Decimal("4.00"))
        self.assertEqual(VendaConcluida.Itens.count(), 2)
        self.assertEqual(
            VendaConcluida.Itens.get(Produto=self.Arroz).CustoUnitario,
            Decimal("6.00"),
        )

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

    def test_DashboardDistingueFaturamentoCustoELucroDosProdutos(self):
        self.AdicionarProduto("1", self.Arroz, "1")
        self.client.post(
            "/carrinho/concluir",
            {"carrinho": "1", "forma_pagamento": Venda.PIX},
        )

        Resposta = self.client.get("/dashboard")

        self.assertContains(Resposta, "Faturamento hoje")
        self.assertContains(Resposta, "Entradas, custos e lucro dos produtos")
        self.assertContains(Resposta, "Custo dos produtos vendidos")
        self.assertContains(Resposta, "R$ 4,00")
        self.assertContains(Resposta, "R$ 6,00")
        self.assertContains(Resposta, "Total da compra")
        self.assertContains(Resposta, "R$ 10,00")
        self.assertContains(Resposta, "Itens da venda")
        self.assertContains(Resposta, "1 un")
        self.assertContains(Resposta, 'data-detalhe-venda="DetalhesVenda')
        self.assertContains(Resposta, 'aria-expanded="false"')
        self.assertNotContains(Resposta, "Preço de custo")

    def test_LucroHojeReiniciaAsSeteDaManha(self):
        VendaAntesDaVirada = Venda.objects.create(
            Proprietario=self.Usuario,
            FormaPagamento=Venda.PIX,
            Total=Decimal("10.00"),
            Lucro=Decimal("3.00"),
        )
        VendaDepoisDaVirada = Venda.objects.create(
            Proprietario=self.Usuario,
            FormaPagamento=Venda.PIX,
            Total=Decimal("20.00"),
            Lucro=Decimal("8.00"),
        )
        Venda.objects.filter(pk=VendaAntesDaVirada.pk).update(
            CriadaEm=timezone.make_aware(datetime(2026, 10, 2, 6, 59))
        )
        Venda.objects.filter(pk=VendaDepoisDaVirada.pk).update(
            CriadaEm=timezone.make_aware(datetime(2026, 10, 2, 7, 0))
        )

        ResumoAntesDasSete = ObterResumoFinanceiro(
            self.Usuario,
            timezone.make_aware(datetime(2026, 10, 2, 6, 59)),
        )
        ResumoDepoisDasSete = ObterResumoFinanceiro(
            self.Usuario,
            timezone.make_aware(datetime(2026, 10, 2, 8, 0)),
        )

        self.assertEqual(ResumoAntesDasSete["LucroHoje"], Decimal("3.00"))
        self.assertEqual(ResumoDepoisDasSete["LucroHoje"], Decimal("8.00"))
        self.assertEqual(
            ResumoDepoisDasSete["TotalVendidoHoje"],
            Decimal("20.00"),
        )
        self.assertEqual(
            ResumoDepoisDasSete["CustoProdutosHoje"],
            Decimal("12.00"),
        )

    def test_EstoqueInsuficienteImpedeTodaABaixa(self):
        self.AdicionarProduto("2", self.Arroz, "2")
        self.AdicionarProduto("2", self.Batata, "1")
        LoteArroz = self.Arroz.LotesEstoque.get()
        LoteArroz.QuantidadeDisponivel = Decimal("1.000")
        LoteArroz.save(update_fields=["QuantidadeDisponivel"])
        self.Arroz.SincronizarResumoLotes()

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

    def test_LotePorPesoPodeSerEncerradoManualmente(self):
        LoteBatata = self.Batata.LotesEstoque.get()

        Resposta = self.client.post(
            f"/estoque/{self.Batata.id}/lotes/{LoteBatata.id}/encerrar"
        )

        self.assertRedirects(Resposta, f"/estoque/{self.Batata.id}/editar")
        LoteBatata.refresh_from_db()
        self.Batata.refresh_from_db()
        self.assertFalse(LoteBatata.Ativo)
        self.assertFalse(self.Batata.Disponivel)
        Pesquisa = self.client.get("/carrinho/pesquisar", {"busca": "Batata"})
        self.assertEqual(Pesquisa.json(), {"Produtos": []})

    def test_VendaPodeDeixarProdutoAbaixoDoMinimoEGeraAlerta(self):
        LoteArroz = self.Arroz.LotesEstoque.get()
        LoteArroz.QuantidadeInicial = Decimal("8.000")
        LoteArroz.QuantidadeDisponivel = Decimal("8.000")
        LoteArroz.save(
            update_fields=["QuantidadeInicial", "QuantidadeDisponivel"]
        )
        self.Arroz.EstoqueMinimo = Decimal("5.000")
        self.Arroz.save(update_fields=["EstoqueMinimo"])
        self.Arroz.SincronizarResumoLotes()

        self.AdicionarProduto("1", self.Arroz, "5")
        RespostaVenda = self.client.post(
            "/carrinho/concluir",
            {"carrinho": "1", "forma_pagamento": Venda.PIX},
        )

        self.assertEqual(RespostaVenda.status_code, 302)
        self.Arroz.refresh_from_db()
        self.assertEqual(self.Arroz.QuantidadeEstoque, Decimal("3.000"))
        PaginaEstoque = self.client.get("/estoque")
        PaginaDashboard = self.client.get("/dashboard")
        self.assertContains(PaginaEstoque, "Estoque baixo")
        self.assertContains(PaginaDashboard, "Arroz 1 kg")
        self.assertContains(PaginaDashboard, "3 un")
        self.assertContains(PaginaDashboard, "5 un")

    def test_CarrinhoDistribuiQuantidadeEntreLotesComPrecosDiferentes(self):
        LoteAntigo = self.Arroz.LotesEstoque.get()
        LoteNovo = self.CriarNovoLoteArroz()

        Pesquisa = self.client.get("/carrinho/pesquisar", {"busca": "Arroz"})
        Opcoes = Pesquisa.json()["Produtos"]
        self.assertEqual(len(Opcoes), 1)
        self.assertEqual(Opcoes[0]["Preco"], "10,00")
        self.assertEqual(Opcoes[0]["Estoque"], "15 un")
        self.assertEqual(Decimal(Opcoes[0]["EstoqueMaximo"]), Decimal("15.000"))
        self.assertNotIn("LoteId", Opcoes[0])
        self.assertNotIn("NumeroLote", Opcoes[0])
        self.assertNotIn("PrecoCusto", Opcoes[0])

        PaginaCarrinho = self.client.get("/carrinho", {"busca": "Arroz"})
        self.assertContains(PaginaCarrinho, '<article class="ProdutoResultado">', count=1)
        self.assertNotContains(PaginaCarrinho, 'name="lote"')
        self.assertNotContains(PaginaCarrinho, "Lote #")
        self.assertNotContains(PaginaCarrinho, "Custo R$")

        self.AdicionarProduto("2", self.Arroz, "1")
        CarrinhoPadrao = self.client.session["CarrinhosVenda"]["2"]
        self.assertEqual(
            CarrinhoPadrao,
            {ObterChaveLote(LoteAntigo.id): "1.000"},
        )
        self.client.post("/carrinho/cancelar", {"carrinho": "2"})

        self.AdicionarProduto("1", self.Arroz, "2")
        self.AdicionarProduto("1", self.Arroz, "9")
        self.assertEqual(
            self.client.session["CarrinhosVenda"]["1"],
            {
                ObterChaveLote(LoteAntigo.id): "10.000",
                ObterChaveLote(LoteNovo.id): "1.000",
            },
        )
        LoteAntigo.refresh_from_db()
        LoteNovo.refresh_from_db()
        self.assertEqual(LoteAntigo.QuantidadeDisponivel, Decimal("10.000"))
        self.assertEqual(LoteNovo.QuantidadeDisponivel, Decimal("5.000"))

        self.client.post(
            "/carrinho/concluir",
            {"carrinho": "1", "forma_pagamento": Venda.PIX},
        )

        VendaConcluida = Venda.objects.get()
        self.assertEqual(VendaConcluida.Total, Decimal("112.00"))
        self.assertEqual(VendaConcluida.Lucro, Decimal("45.00"))
        self.assertEqual(VendaConcluida.Itens.count(), 2)
        self.assertEqual(
            VendaConcluida.Itens.get(Lote=LoteAntigo).CustoUnitario,
            Decimal("6.00"),
        )
        self.assertEqual(
            VendaConcluida.Itens.get(Lote=LoteNovo).PrecoUnitario,
            Decimal("12.00"),
        )
        LoteAntigo.refresh_from_db()
        LoteNovo.refresh_from_db()
        self.Arroz.refresh_from_db()
        self.assertEqual(LoteAntigo.QuantidadeDisponivel, Decimal("0.000"))
        self.assertFalse(LoteAntigo.Ativo)
        self.assertEqual(LoteNovo.QuantidadeDisponivel, Decimal("4.000"))
        self.assertEqual(self.Arroz.QuantidadeEstoque, Decimal("4.000"))

        NovaPesquisa = self.client.get("/carrinho/pesquisar", {"busca": "Arroz"})
        self.assertEqual(NovaPesquisa.json()["Produtos"][0]["Preco"], "12,00")

    def test_QuantidadeInsuficienteEntreLotesNaoAlteraCarrinho(self):
        self.CriarNovoLoteArroz()
        self.AdicionarProduto("1", self.Arroz, "2")
        CarrinhoAnterior = self.client.session["CarrinhosVenda"]["1"].copy()

        Resposta = self.client.post(
            "/carrinho/adicionar",
            {"carrinho": "1", "produto": self.Arroz.id, "quantidade": "14"},
            follow=True,
        )

        self.assertContains(Resposta, "Estoque insuficiente")
        self.assertContains(Resposta, "Disponível: 13 un")
        self.assertEqual(self.client.session["CarrinhosVenda"]["1"], CarrinhoAnterior)
        self.Arroz.refresh_from_db()
        self.assertEqual(self.Arroz.QuantidadeEstoque, Decimal("15.000"))

    def test_AdicionarIgnoraSelecaoManualDeLoteNovo(self):
        LoteAntigo = self.Arroz.LotesEstoque.get()
        LoteNovo = self.CriarNovoLoteArroz()

        self.client.post(
            "/carrinho/adicionar",
            {
                "carrinho": "1",
                "produto": self.Arroz.id,
                "lote": LoteNovo.id,
                "quantidade": "2",
            },
        )

        self.assertEqual(
            self.client.session["CarrinhosVenda"]["1"],
            {ObterChaveLote(LoteAntigo.id): "2.000"},
        )

    def test_AdicionarIgnoraLotesEsgotadosEEncerrados(self):
        LoteAntigo = self.Arroz.LotesEstoque.get()
        LoteAntigo.QuantidadeDisponivel = Decimal("0.000")
        LoteAntigo.save(update_fields=["QuantidadeDisponivel"])
        LoteEncerrado = self.CriarNovoLoteArroz()
        LoteEncerrado.Ativo = False
        LoteEncerrado.save(update_fields=["Ativo"])
        LoteDisponivel = self.CriarNovoLoteArroz()

        self.AdicionarProduto("1", self.Arroz, "3")

        self.assertEqual(
            self.client.session["CarrinhosVenda"]["1"],
            {ObterChaveLote(LoteDisponivel.id): "3.000"},
        )

    def test_ProdutoPorPesoUsaLoteAntigoAteEncerramentoSemBaixaNumerica(self):
        LoteAntigo = self.Batata.LotesEstoque.get()
        LoteNovo = LoteEstoque.objects.create(
            Produto=self.Batata,
            Fornecedor=self.Hortifruti,
            PrecoCusto=Decimal("3.00"),
            PrecoVenda=Decimal("6.00"),
        )
        self.Batata.SincronizarResumoLotes()

        self.AdicionarProduto("1", self.Batata, "12.500")
        self.assertEqual(
            self.client.session["CarrinhosVenda"]["1"],
            {ObterChaveLote(LoteAntigo.id): "12.500"},
        )
        self.client.post(
            "/carrinho/concluir",
            {"carrinho": "1", "forma_pagamento": Venda.PIX},
        )
        LoteAntigo.refresh_from_db()
        self.assertIsNone(LoteAntigo.QuantidadeDisponivel)
        self.assertTrue(LoteAntigo.Ativo)
        self.assertEqual(Venda.objects.get().Total, Decimal("50.00"))

        self.client.post(f"/estoque/{self.Batata.id}/lotes/{LoteAntigo.id}/encerrar")
        self.AdicionarProduto("2", self.Batata, "0.750")
        self.assertEqual(
            self.client.session["CarrinhosVenda"]["2"],
            {ObterChaveLote(LoteNovo.id): "0.750"},
        )

    def test_QuantidadeFracionadaERepartidaEntreLotesPorMetro(self):
        Corda = Produto.objects.create(
            Nome="Corda",
            Fornecedor=self.Distribuidora,
            UnidadeVenda=Produto.METRO,
            QuantidadeEstoque=Decimal("1.250"),
            PrecoCusto=Decimal("1.00"),
            PrecoVenda=Decimal("2.00"),
        )
        LoteAntigo = Corda.LotesEstoque.get()
        LoteNovo = LoteEstoque.objects.create(
            Produto=Corda,
            Fornecedor=self.Distribuidora,
            QuantidadeInicial=Decimal("2.500"),
            QuantidadeDisponivel=Decimal("2.500"),
            PrecoCusto=Decimal("1.50"),
            PrecoVenda=Decimal("3.00"),
        )
        Corda.SincronizarResumoLotes()

        self.AdicionarProduto("1", Corda, "2")
        self.assertEqual(
            self.client.session["CarrinhosVenda"]["1"],
            {
                ObterChaveLote(LoteAntigo.id): "1.250",
                ObterChaveLote(LoteNovo.id): "0.750",
            },
        )
        self.client.post(
            "/carrinho/concluir",
            {"carrinho": "1", "forma_pagamento": Venda.PIX},
        )

        self.assertEqual(Venda.objects.get().Total, Decimal("4.75"))
        LoteNovo.refresh_from_db()
        self.assertEqual(LoteNovo.QuantidadeDisponivel, Decimal("1.750"))

    def test_ConsolidacaoMensalPreservaTotaisAnuaisEApagaDetalhes(self):
        self.AdicionarProduto("1", self.Arroz, "2")
        self.client.post(
            "/carrinho/concluir",
            {"carrinho": "1", "forma_pagamento": Venda.PIX},
        )
        VendaConcluida = Venda.objects.get()
        DataVenda = timezone.make_aware(datetime(2026, 9, 15, 10, 0))
        Venda.objects.filter(pk=VendaConcluida.pk).update(CriadaEm=DataVenda)

        QuantidadeConsolidada = ConsolidarVendasDeMesesAnteriores(
            date(2026, 10, 1)
        )

        self.assertEqual(QuantidadeConsolidada, 1)
        self.assertFalse(Venda.objects.exists())
        RegistroAntigo = RegistroVendaAntiga.objects.get(VendaOriginalId=VendaConcluida.id)
        self.assertEqual(RegistroAntigo.Total, Decimal("20.00"))
        self.assertEqual(RegistroAntigo.Itens.count(), 1)
        self.assertEqual(RegistroAntigo.Itens.get().NomeProduto, "Arroz 1 kg")
        Resumo = ResumoVendaMensal.objects.get(Ano=2026, Mes=9)
        self.assertEqual(Resumo.TotalVendido, Decimal("20.00"))
        self.assertEqual(Resumo.Lucro, Decimal("8.00"))
        ResumoFinanceiro = ObterResumoFinanceiro(
            self.Usuario,
            date(2026, 10, 1),
        )
        self.assertEqual(ResumoFinanceiro["LucroAno"], Decimal("8.00"))
        PaginaHistorico = self.client.get("/vendas/historico?busca=Arroz")
        self.assertContains(PaginaHistorico, "Histórico de vendas")
        self.assertContains(PaginaHistorico, "Arquivada")
        self.assertContains(PaginaHistorico, "Itens preservados")
        self.assertContains(PaginaHistorico, "Arroz 1 kg")

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
            "/?carrinho=2&carrinhos_abertos=1%2C2%2C3&busca_carrinho=arroz",
        )
        PaginaPrincipal = self.client.get(Resposta.url)
        self.assertContains(PaginaPrincipal, "PainelCarrinho-1")
        self.assertContains(PaginaPrincipal, "PainelCarrinho-2")
        self.assertContains(PaginaPrincipal, "PainelCarrinho-3")
        self.assertContains(PaginaPrincipal, "Carrinhos sempre abertos")
        self.assertNotContains(PaginaPrincipal, "<h1>Página Principal</h1>", html=True)
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

    def test_CompraPodeSerLancadaNaContinhaDoCliente(self):
        self.client.post(
            "/carrinho/nome",
            {"carrinho": "1", "nome_cliente": "João da Padaria"},
        )
        self.AdicionarProduto("1", self.Arroz, "2")

        Resposta = self.client.post(
            "/carrinho/concluir",
            {"carrinho": "1", "forma_pagamento": Venda.CONTA_CLIENTE},
        )

        self.assertEqual(Resposta.status_code, 302)
        VendaConcluida = Venda.objects.get()
        Conta = ContaCliente.objects.get(NomeCliente="João da Padaria")
        Lancamento = LancamentoContaCliente.objects.get(Conta=Conta)
        self.assertEqual(VendaConcluida.FormaPagamento, Venda.CONTA_CLIENTE)
        self.assertEqual(VendaConcluida.ContaCliente, Conta)
        self.assertEqual(Lancamento.Tipo, LancamentoContaCliente.COMPRA)
        self.assertEqual(Lancamento.Valor, Decimal("20.00"))
        self.Arroz.refresh_from_db()
        self.assertEqual(self.Arroz.QuantidadeEstoque, Decimal("8.000"))

        PaginaContinhas = self.client.get("/continhas")
        self.assertContains(PaginaContinhas, "João da Padaria")
        self.assertContains(PaginaContinhas, "R$ 20,00")
        self.assertContains(PaginaContinhas, "Venda #")

    def test_ContinhaExigeNomeDoClienteNoCarrinho(self):
        self.AdicionarProduto("1", self.Arroz, "1")

        Resposta = self.client.post(
            "/carrinho/concluir",
            {"carrinho": "1", "forma_pagamento": Venda.CONTA_CLIENTE},
            follow=True,
        )

        self.assertFalse(Venda.objects.exists())
        self.assertFalse(ContaCliente.objects.exists())
        self.assertContains(
            Resposta,
            "Informe o nome do cliente para lançar na continha.",
        )
        self.assertIn("1", self.client.session["CarrinhosVenda"])

    def test_PagamentoDaContinhaReduzSaldoDoCliente(self):
        self.client.post(
            "/carrinho/nome",
            {"carrinho": "1", "nome_cliente": "Cliente Mensalista"},
        )
        self.AdicionarProduto("1", self.Arroz, "2")
        self.client.post(
            "/carrinho/concluir",
            {"carrinho": "1", "forma_pagamento": Venda.CONTA_CLIENTE},
        )
        Conta = ContaCliente.objects.get(NomeCliente="Cliente Mensalista")

        Resposta = self.client.post(
            "/continhas/pagamento",
            {
                "conta": Conta.id,
                "valor": "5,00",
                "descricao": "parcial",
            },
            follow=True,
        )

        self.assertEqual(
            LancamentoContaCliente.objects.filter(
                Conta=Conta,
                Tipo=LancamentoContaCliente.PAGAMENTO,
            ).count(),
            1,
        )
        self.assertContains(Resposta, "R$ 15,00")

    def test_PesquisaContinhasFiltraNomesParciaisERespeitaProprietario(self):
        for Nome in ["Luiz Silva", "Luiz Carlos", "Maria Souza"]:
            ContaCliente.objects.create(Proprietario=self.Usuario, NomeCliente=Nome)
        OutroUsuario = ObterModeloUsuario().objects.create_user(username="outro_proprietario")
        ContaCliente.objects.create(Proprietario=OutroUsuario, NomeCliente="Luiz Oliveira")

        Resposta = self.client.get("/continhas", {"busca": "luiz"})

        self.assertContains(Resposta, "Luiz Silva")
        self.assertContains(Resposta, "Luiz Carlos")
        self.assertNotContains(Resposta, "Maria Souza")
        self.assertNotContains(Resposta, "Luiz Oliveira")
        SemResultados = self.client.get("/continhas", {"busca": "cliente inexistente"})
        self.assertContains(SemResultados, "Nenhuma continha encontrada")
        SemFiltro = self.client.get("/continhas")
        self.assertContains(SemFiltro, "Maria Souza")

    def test_CancelarCarrinhoTambemResetaONome(self):
        self.client.post(
            "/carrinho/nome",
            {"carrinho": "1", "nome_cliente": "Cliente conhecido"},
        )

        self.client.post("/carrinho/cancelar", {"carrinho": "1"})

        self.assertNotIn("1", self.client.session.get("NomesCarrinhosVenda", {}))
        self.assertContains(self.client.get("/"), "Carrinho 1")
