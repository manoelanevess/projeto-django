"""Testes da divisão da venda entre PIX e dinheiro."""
from datetime import datetime, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model as ObterModeloUsuario
from django.test import TestCase
from django.utils import timezone

from features.fornecedor.models import Fornecedor
from features.produtos.models import Produto

from .LogicaVenda import ConsolidarVendasDeMesesAnteriores, ObterResumoFinanceiro
from .models import ContaCliente, RegistroVendaAntiga, Venda


class TestePagamentoMisto(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.Usuario = ObterModeloUsuario().objects.create_user(username="pagamento_misto")
        FornecedorTeste = Fornecedor.objects.create(Nome="Fornecedor pagamento misto")
        cls.Produto = Produto.objects.create(
            Nome="Produto pagamento misto", Fornecedor=FornecedorTeste,
            QuantidadeEstoque=Decimal("10.000"), PrecoCusto=Decimal("6.00"),
            PrecoVenda=Decimal("20.00"),
        )

    def setUp(self):
        self.client.force_login(self.Usuario)
        self.client.post("/carrinho/adicionar", {
            "carrinho": "1", "produto": self.Produto.id, "quantidade": "1",
        })

    def Pagar(self, Pix="10,00", Dinheiro="10,00", **Dados):
        return self.client.post("/carrinho/concluir", {
            "carrinho": "1", "forma_pagamento": Venda.PIX_DINHEIRO,
            "valor_pix": Pix, "valor_recebido": Dinheiro, **Dados,
        }, follow=True)

    def test_MetadeNoPixEMetadeEmDinheiroRegistraUmaVendaEBaixaUmaVez(self):
        self.Pagar()

        VendaConcluida = Venda.objects.get()
        self.assertEqual(VendaConcluida.FormaPagamento, Venda.PIX_DINHEIRO)
        self.assertEqual(VendaConcluida.ValorPix, Decimal("10.00"))
        self.assertEqual(VendaConcluida.ValorRecebido, Decimal("10.00"))
        self.assertEqual(VendaConcluida.Troco, Decimal("0.00"))
        self.assertEqual(VendaConcluida.Total, Decimal("20.00"))
        self.assertEqual(VendaConcluida.Lucro, Decimal("14.00"))
        self.assertEqual(VendaConcluida.Itens.count(), 1)
        self.Produto.refresh_from_db()
        self.assertEqual(self.Produto.QuantidadeEstoque, Decimal("9.000"))
        self.assertNotIn("1", self.client.session.get("CarrinhosVenda", {}))
        self.assertFalse(ContaCliente.objects.exists())
        Resumo = ObterResumoFinanceiro(self.Usuario)
        self.assertEqual(Resumo["TotalVendidoHoje"], Decimal("20.00"))
        self.assertEqual(Resumo["LucroHoje"], Decimal("14.00"))

    def test_DivisaoPersonalizadaCalculaTrocoSomenteDaParteEmDinheiro(self):
        Resposta = self.Pagar(Pix="7,50", Dinheiro="20,00", retorno="pagina-principal")
        self.assertEqual(Resposta.request["PATH_INFO"], "/")
        VendaConcluida = Venda.objects.get()
        self.assertEqual(VendaConcluida.ValorPix, Decimal("7.50"))
        self.assertEqual(VendaConcluida.ValorRecebido, Decimal("20.00"))
        self.assertEqual(VendaConcluida.Troco, Decimal("7.50"))
        self.assertEqual(
            VendaConcluida.ValorPix + VendaConcluida.ValorRecebido - VendaConcluida.Troco,
            VendaConcluida.Total,
        )
        for Rota in ("/dashboard", "/vendas/historico?pagamento=pix_dinheiro"):
            with self.subTest(Rota=Rota):
                Pagina = self.client.get(Rota)
                self.assertContains(Pagina, "PIX + dinheiro")
                self.assertContains(Pagina, "PIX: R$ 7,50")
                self.assertContains(Pagina, "Dinheiro: R$ 12,50")
                self.assertContains(Pagina, "Recebido em dinheiro: R$ 20,00")
                self.assertContains(Pagina, "Troco: R$ 7,50")

    def test_DinheiroInsuficienteMantemCarrinhoEEstoque(self):
        Resposta = self.Pagar(Pix="10,00", Dinheiro="9,99")
        self.assertContains(Resposta, "Faltam R$ 0,01 para concluir a compra.")
        self.assertFalse(Venda.objects.exists())
        self.Produto.refresh_from_db()
        self.assertEqual(self.Produto.QuantidadeEstoque, Decimal("10.000"))
        self.assertIn("1", self.client.session["CarrinhosVenda"])

    def test_CompraDeQuinzeAceitaDezEmDinheiroECincoNoPix(self):
        self.Produto.LotesEstoque.update(PrecoVenda=Decimal("15.00"))
        self.Produto.SincronizarResumoLotes()
        self.Pagar(Pix="5", Dinheiro="10")
        VendaConcluida = Venda.objects.get()
        self.assertEqual(VendaConcluida.Total, Decimal("15.00"))
        self.assertEqual(VendaConcluida.ValorRecebido, Decimal("10.00"))
        self.assertEqual(VendaConcluida.ValorPix, Decimal("5.00"))
        self.assertEqual(VendaConcluida.Troco, Decimal("0.00"))

    def test_RejeitaPixAusenteZeroNegativoTotalOuSuperior(self):
        for Pix in ("", "0", "-1", "20", "21"):
            with self.subTest(Pix=Pix):
                Resposta = self.Pagar(Pix=Pix, Dinheiro="20")
                self.assertContains(Resposta, 'class="MensagemOperacao Erro"')
                self.assertFalse(Venda.objects.exists())
                self.assertIn("1", self.client.session["CarrinhosVenda"])
        self.Produto.refresh_from_db()
        self.assertEqual(self.Produto.QuantidadeEstoque, Decimal("10.000"))

    def test_RejeitaValoresInvalidosSemErroDeServidor(self):
        for Campo in ("Pix", "Dinheiro"):
            for Valor in ("", "abc", "NaN", "Infinity", "1e999999", "99999999999,99", "-1"):
                with self.subTest(Campo=Campo, Valor=Valor):
                    Resposta = self.Pagar(**{Campo: Valor})
                    self.assertEqual(Resposta.status_code, 200)
                    self.assertContains(Resposta, 'class="MensagemOperacao Erro"')
                    self.assertFalse(Venda.objects.exists())
        self.Produto.refresh_from_db()
        self.assertEqual(self.Produto.QuantidadeEstoque, Decimal("10.000"))
        self.assertIn("1", self.client.session["CarrinhosVenda"])

    def test_AceitaCentavosEValoresComSeparadorDeMilhar(self):
        self.Pagar(Pix="7.01", Dinheiro="1.000,00")
        VendaConcluida = Venda.objects.get()
        self.assertEqual(VendaConcluida.ValorPix, Decimal("7.01"))
        self.assertEqual(VendaConcluida.Troco, Decimal("987.01"))

    def test_AsDuasTelasOferecemPagamentoMisto(self):
        self.client.post("/carrinho/adicionar", {
            "carrinho": "2", "produto": self.Produto.id, "quantidade": "1",
        })
        for Rota, Quantidade in (("/carrinho", 1), ("/", 2)):
            with self.subTest(Rota=Rota):
                Resposta = self.client.get(Rota)
                self.assertContains(Resposta, 'value="pix_dinheiro"', count=Quantidade)
                self.assertContains(Resposta, 'name="valor_pix"')
                self.assertNotContains(Resposta, "Restante em dinheiro")
                self.assertContains(Resposta, 'name="valor_recebido"')
                Html = Resposta.content.decode()
                self.assertLess(Html.index('name="valor_recebido"'), Html.index('name="valor_pix"'))

    def test_ConsolidacaoPreservaDivisaoETrocoNoHistoricoArquivado(self):
        self.Pagar(Pix="8,00", Dinheiro="15,00")
        VendaConcluida = Venda.objects.get()
        DiaAnterior = timezone.localdate().replace(day=1) - timedelta(days=1)
        DataVenda = timezone.make_aware(datetime.combine(DiaAnterior, datetime.min.time()))
        Venda.objects.filter(pk=VendaConcluida.pk).update(CriadaEm=DataVenda)
        self.assertEqual(ConsolidarVendasDeMesesAnteriores(), 1)
        Registro = RegistroVendaAntiga.objects.get()
        self.assertEqual(Registro.ValorPix, Decimal("8.00"))
        self.assertEqual(Registro.ValorRecebido, Decimal("15.00"))
        self.assertEqual(Registro.Troco, Decimal("3.00"))
        self.assertEqual(Registro.Itens.count(), 1)
        Pagina = self.client.get("/vendas/historico", {"pagamento": "pix_dinheiro"})
        self.assertContains(Pagina, "PIX: R$ 8,00")
        self.assertContains(Pagina, "Dinheiro: R$ 12,00")
        self.assertContains(Pagina, "Troco: R$ 3,00")

    def test_PixEDinheiroSeparadosContinuamFuncionando(self):
        for Forma, ValorPix, Recebido, Troco in (
            (Venda.PIX, "20.00", None, "0.00"),
            (Venda.DINHEIRO, "0.00", "25.00", "5.00"),
        ):
            with self.subTest(Forma=Forma):
                self.client.post("/carrinho/concluir", {
                    "carrinho": "1", "forma_pagamento": Forma,
                    "valor_pix": "invalido", "valor_recebido": Recebido or "invalido",
                })
                VendaConcluida = Venda.objects.latest("id")
                self.assertEqual(VendaConcluida.FormaPagamento, Forma)
                self.assertEqual(VendaConcluida.ValorPix, Decimal(ValorPix))
                self.assertEqual(VendaConcluida.Troco, Decimal(Troco))
                self.assertEqual(
                    VendaConcluida.ValorRecebido, Decimal(Recebido) if Recebido else None
                )
                self.client.post("/carrinho/adicionar", {
                    "carrinho": "1", "produto": self.Produto.id, "quantidade": "1",
                })
