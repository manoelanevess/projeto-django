"""Testes do carrinho, pagamento e baixa automática do estoque."""
from datetime import date, datetime, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model as ObterModeloUsuario
from django.test import Client, TestCase
from django.utils import timezone

from features.fornecedor.models import Fornecedor
from features.produtos.models import LoteEstoque, Produto

from .LogicaCarrinho import ObterChaveLote
from .LogicaContaCliente import CalcularSaldoConta
from .LogicaVenda import ConsolidarVendasDeMesesAnteriores, ObterResumoFinanceiro
from .models import (
    ContaCliente,
    ItemRegistroVendaAntiga,
    ItemVenda,
    LancamentoContaCliente,
    RegistroVendaAntiga,
    ResumoVendaMensal,
    Venda,
)


class TesteExclusaoContinhas(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.Usuario = ObterModeloUsuario().objects.create_user(username="exclusao_continhas")
        cls.OutroUsuario = ObterModeloUsuario().objects.create_user(username="outras_continhas")
        cls.Quitada = ContaCliente.objects.create(Proprietario=cls.Usuario, NomeCliente="Luiz")
        cls.Aberta = ContaCliente.objects.create(Proprietario=cls.Usuario, NomeCliente="Maria")
        cls.ComCredito = ContaCliente.objects.create(Proprietario=cls.Usuario, NomeCliente="Ana")
        cls.Inativa = ContaCliente.objects.create(Proprietario=cls.Usuario, NomeCliente="Paulo inativo", Ativa=False)
        cls.DeOutroUsuario = ContaCliente.objects.create(Proprietario=cls.OutroUsuario, NomeCliente="Cliente de outro usuario")
        FornecedorTeste = Fornecedor.objects.create(Nome="Fornecedor exclusao continhas")
        cls.Produto = Produto.objects.create(
            Nome="Produto da continha", Fornecedor=FornecedorTeste,
            QuantidadeEstoque=Decimal("10.000"), PrecoCusto=Decimal("7.00"), PrecoVenda=Decimal("10.00"),
        )
        cls.VendaAnterior = Venda.objects.create(
            Proprietario=cls.Usuario, NomeCliente="Luiz", ContaCliente=cls.Quitada,
            FormaPagamento=Venda.CONTA_CLIENTE, Total=Decimal("10.00"), Lucro=Decimal("3.00"),
        )
        ItemVenda.objects.create(
            Venda=cls.VendaAnterior, Produto=cls.Produto, NomeProduto=cls.Produto.Nome,
            UnidadeVenda="unidade", Quantidade=Decimal("1.000"), CustoUnitario=Decimal("7.00"),
            PrecoUnitario=Decimal("10.00"), Subtotal=Decimal("10.00"), Lucro=Decimal("3.00"),
        )
        LancamentoContaCliente.objects.create(Conta=cls.Quitada, Venda=cls.VendaAnterior, Tipo="compra", Valor=Decimal("10.00"))
        LancamentoContaCliente.objects.create(Conta=cls.Quitada, Tipo="pagamento", Valor=Decimal("10.00"))
        LancamentoContaCliente.objects.create(Conta=cls.Aberta, Tipo="compra", Valor=Decimal("10.00"))
        LancamentoContaCliente.objects.create(Conta=cls.ComCredito, Tipo="pagamento", Valor=Decimal("5.00"))
        LancamentoContaCliente.objects.create(Conta=cls.Inativa, Tipo="compra", Valor=Decimal("2.00"))

    def setUp(self):
        self.client.force_login(self.Usuario)

    def Excluir(self, Conta, **Dados):
        return self.client.post(f"/continhas/{Conta.id}/excluir", Dados)

    def test_ExcluiQuitadaDaListaSemApagarVendaItensOuLancamentos(self):
        self.assertRedirects(self.Excluir(self.Quitada), "/continhas")
        self.Quitada.refresh_from_db()
        self.assertIsNotNone(self.Quitada.ExcluidaEm)
        self.assertEqual(self.Quitada.Lancamentos.count(), 2)
        self.assertEqual(CalcularSaldoConta(self.Quitada), Decimal("0.00"))
        self.VendaAnterior.refresh_from_db()
        self.assertEqual(self.VendaAnterior.ContaCliente, self.Quitada)
        self.assertEqual(self.VendaAnterior.Total, Decimal("10.00"))
        self.assertEqual(self.VendaAnterior.Lucro, Decimal("3.00"))
        self.assertEqual(self.VendaAnterior.Itens.count(), 1)
        self.assertNotContains(self.client.get("/continhas", {"busca": "Luiz"}), "Apagar continha de Luiz")
        Historico = self.client.get("/vendas/historico", {"busca": "Luiz"})
        self.assertContains(Historico, "Produto da continha")
        self.assertContains(Historico, "R$ 10,00")

    def test_DividaOuCreditoImpedemExclusaoMesmoComPostDireto(self):
        for Conta in (self.Aberta, self.ComCredito, self.Inativa):
            with self.subTest(Conta=Conta.NomeCliente):
                Resposta = self.Excluir(Conta)
                self.assertRedirects(Resposta, "/continhas", fetch_redirect_response=False)
                Conta.refresh_from_db()
                self.assertIsNone(Conta.ExcluidaEm)
                self.assertContains(self.client.get("/continhas"), "Somente continhas com saldo zerado podem ser apagadas.")

    def test_ReconfereSaldoDepoisDeMostrarBotao(self):
        self.client.get("/continhas")
        LancamentoContaCliente.objects.create(Conta=self.Quitada, Tipo="compra", Valor=Decimal("1.00"))
        self.Excluir(self.Quitada)
        self.Quitada.refresh_from_db()
        self.assertIsNone(self.Quitada.ExcluidaEm)

    def test_ExclusaoExigeLoginEPost(self):
        Endereco = f"/continhas/{self.Quitada.id}/excluir"
        SemLogin = Client().post(Endereco)
        self.assertEqual(SemLogin.status_code, 302)
        self.assertTrue(SemLogin.url.startswith("/login?next="))
        self.assertEqual(self.client.get(Endereco).status_code, 405)
        self.Quitada.refresh_from_db()
        self.assertIsNone(self.Quitada.ExcluidaEm)

    def test_ExclusaoExigeCsrf(self):
        Cliente = Client(enforce_csrf_checks=True)
        Cliente.force_login(self.Usuario)
        Endereco = f"/continhas/{self.Quitada.id}/excluir"
        self.assertEqual(Cliente.post(Endereco).status_code, 403)
        Cliente.get("/continhas")
        Resposta = Cliente.post(Endereco, {"csrfmiddlewaretoken": Cliente.cookies["csrftoken"].value})
        self.assertEqual(Resposta.status_code, 302)

    def test_OutroProprietarioContaInexistenteEOuJaExcluidaRetornam404(self):
        self.assertEqual(self.Excluir(self.DeOutroUsuario).status_code, 404)
        self.assertEqual(self.client.post("/continhas/999999999/excluir").status_code, 404)
        self.Excluir(self.Quitada)
        self.assertEqual(self.Excluir(self.Quitada).status_code, 404)
        self.DeOutroUsuario.refresh_from_db()
        self.assertIsNone(self.DeOutroUsuario.ExcluidaEm)

    def test_ExclusaoPreservaFiltroNaUrl(self):
        self.assertRedirects(self.Excluir(self.Quitada, busca="Luiz Silva"), "/continhas?busca=Luiz+Silva")

    def test_ListaInativaNaoExcluidaContinuaAcessivel(self):
        self.assertContains(self.client.get("/continhas", {"busca": "Paulo"}), "Paulo inativo")

    def test_PagamentoNaoPodeSerAdicionadoAContaExcluida(self):
        self.Excluir(self.Quitada)
        Resposta = self.client.post("/continhas/pagamento", {"conta": self.Quitada.id, "valor": "1.00"}, follow=True)
        self.assertContains(Resposta, "Continha não encontrada.")
        self.assertEqual(self.Quitada.Lancamentos.count(), 2)

    def test_ContaSemLancamentosPodeSerExcluidaEListaFicaVazia(self):
        ContaVazia = ContaCliente.objects.create(Proprietario=self.OutroUsuario, NomeCliente="Vazia")
        self.client.force_login(self.OutroUsuario)
        self.Excluir(self.DeOutroUsuario)
        self.Excluir(ContaVazia)
        self.assertContains(self.client.get("/continhas"), "Nenhuma continha encontrada")

    def test_NovaCompraReabreMesmaContaComHistoricoPreservado(self):
        self.Excluir(self.Quitada)
        self.client.post("/carrinho/nome", {"carrinho": "1", "nome_cliente": "luiz"})
        self.client.post("/carrinho/adicionar", {"carrinho": "1", "produto": self.Produto.id, "quantidade": "1"})
        self.client.post("/carrinho/concluir", {"carrinho": "1", "forma_pagamento": Venda.CONTA_CLIENTE})
        self.Quitada.refresh_from_db()
        self.assertIsNone(self.Quitada.ExcluidaEm)
        self.assertEqual(ContaCliente.objects.filter(Proprietario=self.Usuario).count(), 4)
        self.assertEqual(Venda.objects.filter(ContaCliente=self.Quitada).count(), 2)
        self.assertEqual(self.Quitada.Lancamentos.count(), 3)
        self.assertEqual(CalcularSaldoConta(self.Quitada), Decimal("10.00"))
        self.assertContains(self.client.get("/continhas", {"busca": "Luiz"}), "Apagar continha de Luiz")


class TesteCarrinhosDinamicos(TestCase):
    def setUp(self):
        self.Usuario = ObterModeloUsuario().objects.create_user(username="carrinhos_dinamicos")
        self.client.force_login(self.Usuario)
        self.Fornecedor = Fornecedor.objects.create(Nome="Fornecedor dos carrinhos")
        self.Produto = Produto.objects.create(
            Nome="Produto dos carrinhos", CodigoBarras="0012345678905", Fornecedor=self.Fornecedor,
            QuantidadeEstoque=Decimal("2.000"), PrecoCusto=Decimal("6.00"), PrecoVenda=Decimal("10.00"),
        )
        self.Antigo = self.Produto.LotesEstoque.get()
        self.Novo = LoteEstoque.objects.create(
            Produto=self.Produto, Fornecedor=self.Fornecedor,
            QuantidadeInicial=Decimal("10.000"), QuantidadeDisponivel=Decimal("10.000"),
            PrecoCusto=Decimal("7.00"), PrecoVenda=Decimal("12.00"),
        )
        self.Produto.SincronizarResumoLotes()

    def AbrirAte(self, Ultimo):
        for Numero in range(4, Ultimo + 1):
            Resposta = self.client.post("/carrinho/abrir")
            self.assertEqual(Resposta.url, f"/carrinho?carrinho={Numero}")

    def test_AbreMaisDeTresSemLimiteFixoEPersisteOrdemNumericaNasTelas(self):
        self.AbrirAte(15)
        self.assertEqual(self.client.session["NumerosCarrinhosVenda"], [str(Numero) for Numero in range(1, 16)])
        Carrinho = self.client.get("/carrinho?carrinho=15")
        Principal = self.client.get("/")
        self.assertContains(Carrinho, 'class="ItemAbaCarrinho"', count=15)
        self.assertContains(Principal, 'class="CartaoAtendimento"', count=15)
        self.assertContains(Principal, 'class="PainelCarrinhoFlutuante"', count=15)
        for Pagina in (Carrinho, Principal):
            self.assertContains(Pagina, 'aria-label="Abrir novo carrinho"', count=1)
            Texto = Pagina.content.decode()
            self.assertLess(Texto.index("Carrinho 9"), Texto.index("Carrinho 10"))
        self.assertContains(Carrinho, 'data-leitor-codigo="15"')

    def test_AbrirPreservaItensENomesDeSessoesAnteriores(self):
        self.client.post("/carrinho/ler-codigo", {"carrinho": "2", "codigo": self.Produto.CodigoBarras})
        self.client.post("/carrinho/nome", {"carrinho": "2", "nome_cliente": "Maria"})
        Antes = dict(self.client.session["CarrinhosVenda"])
        Resposta = self.client.post("/carrinho/abrir", {"retorno": "pagina-principal"})
        self.assertEqual(Resposta.url, "/?carrinho=4&carrinhos_abertos=1%2C2%2C3%2C4")
        self.assertEqual(self.client.session["CarrinhosVenda"], Antes)
        self.assertEqual(self.client.session["NomesCarrinhosVenda"], {"2": "Maria"})

    def test_NovosCarrinhosMantemFifoEstoqueENomesIndependentes(self):
        self.AbrirAte(6)
        for Numero in ("4", "6"):
            Resposta = self.client.post("/carrinho/ler-codigo", {
                "carrinho": Numero, "codigo": self.Produto.CodigoBarras, "quantidade": "3",
            })
            self.assertEqual(Resposta.status_code, 200)
            self.client.post("/carrinho/nome", {"carrinho": Numero, "nome_cliente": f"Cliente {Numero}"})
        Carrinho6 = dict(self.client.session["CarrinhosVenda"]["6"])
        self.assertEqual(Carrinho6, {ObterChaveLote(self.Antigo.id): "2.000", ObterChaveLote(self.Novo.id): "1.000"})
        self.Produto.refresh_from_db()
        self.assertEqual(self.Produto.QuantidadeEstoque, Decimal("12.000"))
        self.client.post("/carrinho/concluir", {"carrinho": "4", "forma_pagamento": Venda.CONTA_CLIENTE})
        Concluida = Venda.objects.get()
        self.assertEqual(Concluida.Total, Decimal("32.00"))
        self.assertEqual(Concluida.NomeCliente, "Cliente 4")
        self.assertEqual(Concluida.ContaCliente.NomeCliente, "Cliente 4")
        self.assertEqual(self.client.session["CarrinhosVenda"]["6"], Carrinho6)
        self.assertEqual(self.client.session["NomesCarrinhosVenda"], {"6": "Cliente 6"})
        self.assertIn("4", self.client.session["NumerosCarrinhosVenda"])
        self.Produto.refresh_from_db()
        self.assertEqual(self.Produto.QuantidadeEstoque, Decimal("9.000"))

    def test_CancelarERemoverEmNovoCarrinhoNaoAfetaOutroNemFechaAba(self):
        self.AbrirAte(4)
        for Numero in ("2", "4"):
            self.client.post("/carrinho/ler-codigo", {"carrinho": Numero, "codigo": self.Produto.CodigoBarras})
        Antes = dict(self.client.session["CarrinhosVenda"]["2"])
        self.client.post("/carrinho/remover", {"carrinho": "4", "item": ObterChaveLote(self.Antigo.id)})
        self.assertEqual(self.client.session["CarrinhosVenda"]["4"], {})
        self.client.post("/carrinho/cancelar", {"carrinho": "4"})
        self.assertEqual(self.client.session["CarrinhosVenda"]["2"], Antes)
        self.assertIn("4", self.client.session["NumerosCarrinhosVenda"])

    def test_FecharRemoveSomenteAtendimentoSelecionadoSemBaixa(self):
        self.AbrirAte(6)
        for Numero in ("2", "6"):
            self.client.post("/carrinho/ler-codigo", {"carrinho": Numero, "codigo": self.Produto.CodigoBarras})
            self.client.post("/carrinho/nome", {"carrinho": Numero, "nome_cliente": f"Cliente {Numero}"})
        self.client.post("/carrinho/fechar", {"carrinho": "6", "carrinho_selecionado": "2"})
        self.assertNotIn("6", self.client.session["NumerosCarrinhosVenda"])
        self.assertNotIn("6", self.client.session["CarrinhosVenda"])
        self.assertNotIn("6", self.client.session["NomesCarrinhosVenda"])
        self.assertIn("2", self.client.session["CarrinhosVenda"])
        self.assertNotContains(self.client.get("/"), 'id="PainelCarrinho-6"')
        self.Produto.refresh_from_db()
        self.assertEqual(self.Produto.QuantidadeEstoque, Decimal("12.000"))
        self.assertFalse(Venda.objects.exists())

    def test_PodeFecharTodosInclusiveIniciaisEReabrirPeloMais(self):
        for Numero in ("1", "2", "3"):
            self.client.post("/carrinho/fechar", {"carrinho": Numero})
        self.assertEqual(self.client.session["NumerosCarrinhosVenda"], [])
        for Rota in ("/", "/carrinho", "/carrinho?carrinho=3"):
            Pagina = self.client.get(Rota)
            self.assertContains(Pagina, "Nenhum carrinho aberto.")
            self.assertContains(Pagina, 'aria-label="Abrir novo carrinho"')
        self.assertEqual(self.client.post("/carrinho/abrir").url, "/carrinho?carrinho=1")
        self.assertEqual(self.client.session["NumerosCarrinhosVenda"], ["1"])

    def test_ExigeLoginPostECsrfParaAbrirEFechar(self):
        ClienteCsrf = Client(enforce_csrf_checks=True)
        ClienteCsrf.force_login(self.Usuario)
        for Rota in ("/carrinho/abrir", "/carrinho/fechar"):
            self.assertEqual(self.client.get(Rota).status_code, 405)
            self.assertEqual(ClienteCsrf.post(Rota).status_code, 403)
            self.assertEqual(Client().post(Rota).status_code, 302)

    def test_NumeroInexistenteOuMalformadoNaoCriaCarrinho(self):
        for Numero in ("4", "0", "-1", "04", "1.0", "abc", "١"):
            with self.subTest(Numero=Numero):
                self.assertEqual(self.client.post("/carrinho/ler-codigo", {
                    "carrinho": Numero, "codigo": self.Produto.CodigoBarras,
                }).status_code, 400)
                self.assertContains(self.client.get("/carrinho", {"carrinho": Numero}), 'data-leitor-codigo="1"')
        self.assertNotIn("NumerosCarrinhosVenda", self.client.session)

    def test_RecuperaSessaoLegadaEIgnoraRegistroCorrompido(self):
        Sessao = self.client.session
        Sessao["NumerosCarrinhosVenda"] = "invalido"
        Sessao["CarrinhosVenda"] = {"7": {ObterChaveLote(self.Antigo.id): "1.000"}, "abc": {}}
        Sessao["NomesCarrinhosVenda"] = {"7": "Cliente legado"}
        Sessao.save()
        self.assertContains(self.client.get("/carrinho?carrinho=7"), "Cliente legado")
        self.assertEqual(self.client.post("/carrinho/abrir").url, "/carrinho?carrinho=8")
        Sessao = self.client.session
        Sessao["NumerosCarrinhosVenda"] = ["8", "2", "2", "abc", None, 5, "0", ""]
        Sessao.save()
        self.assertContains(self.client.get("/"), 'class="CartaoAtendimento"', count=2)


class TesteFiltrosHistoricoVenda(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.Usuario = ObterModeloUsuario().objects.create_user(username="filtros_vendas")
        cls.OutroUsuario = ObterModeloUsuario().objects.create_user(username="outras_vendas")
        cls.Dia = timezone.localdate().replace(day=10)
        cls.DiaAntigo = (cls.Dia.replace(day=1) - timedelta(days=1)).replace(day=10)
        cls.Vendas = {}
        cls.Registros = {}

        for Indice, (Pagamento, _) in enumerate(Venda.OpcoesFormaPagamento):
            DataVenda = timezone.make_aware(datetime.combine(cls.Dia, datetime.min.time()))

            if Pagamento == Venda.PIX:
                DataVenda += timedelta(hours=23, minutes=59, seconds=59, microseconds=999999)
            elif Pagamento == Venda.CONTA_CLIENTE:
                DataVenda += timedelta(days=1)

            VendaAtual = Venda.objects.create(
                Proprietario=cls.Usuario, NomeCliente=f"Cliente atual {Pagamento}",
                FormaPagamento=Pagamento, Total=Decimal("15.00"),
            )
            Venda.objects.filter(pk=VendaAtual.pk).update(CriadaEm=DataVenda)
            cls.Vendas[Pagamento] = VendaAtual
            cls.Registros[Pagamento] = RegistroVendaAntiga.objects.create(
                Proprietario=cls.Usuario, VendaOriginalId=90000 + Indice,
                NomeCliente=f"Cliente antigo {Pagamento}", FormaPagamento=Pagamento,
                Total=Decimal("12.00"),
                CriadaEm=timezone.make_aware(datetime.combine(cls.DiaAntigo, datetime.min.time())),
            )

        cls.VendaAnterior = Venda.objects.create(
            Proprietario=cls.Usuario, NomeCliente="Cliente do dia anterior",
            FormaPagamento=Venda.DINHEIRO, Total=Decimal("8.00"),
        )
        Venda.objects.filter(pk=cls.VendaAnterior.pk).update(
            CriadaEm=timezone.make_aware(datetime.combine(cls.Dia, datetime.min.time()))
            - timedelta(microseconds=1)
        )
        Venda.objects.create(
            Proprietario=cls.OutroUsuario, NomeCliente="Venda de outro proprietario",
            FormaPagamento=Venda.PIX, Total=Decimal("99.00"),
        )
        RegistroVendaAntiga.objects.create(
            Proprietario=cls.OutroUsuario, VendaOriginalId=99999,
            NomeCliente="Arquivo de outro proprietario", FormaPagamento=Venda.PIX,
            Total=Decimal("99.00"), CriadaEm=cls.Registros[Venda.PIX].CriadaEm,
        )
        FornecedorTeste = Fornecedor.objects.create(Nome="Fornecedor dos filtros")
        ProdutoTeste = Produto.objects.create(
            Nome="Produto dos filtros", Categoria="Alimentos", Fornecedor=FornecedorTeste,
            PrecoCusto=Decimal("1.11"), PrecoVenda=Decimal("7.50"),
            QuantidadeEstoque=Decimal("10.000"),
        )

        for _ in range(2):
            ItemVenda.objects.create(
                Venda=cls.Vendas[Venda.PIX], Produto=ProdutoTeste, NomeProduto="Arroz filtrado",
                UnidadeVenda="unidade", Quantidade=Decimal("1.000"),
                CustoUnitario=Decimal("1.11"), PrecoUnitario=Decimal("7.50"),
                Subtotal=Decimal("7.50"),
            )

        ItemRegistroVendaAntiga.objects.create(
            Registro=cls.Registros[Venda.PIX], NomeProduto="Arroz arquivado",
            UnidadeVenda="unidade", Quantidade=Decimal("1.000"),
            PrecoUnitario=Decimal("12.00"), Subtotal=Decimal("12.00"),
        )

    def setUp(self):
        self.client.force_login(self.Usuario)

    def Consultar(self, **Filtros):
        return self.client.get("/vendas/historico", Filtros)

    def test_sem_filtros_preserva_historico_e_isolamento_por_proprietario(self):
        Resposta = self.Consultar()
        self.assertContains(Resposta, 'class="LinhaHistoricoVenda"', count=7)
        self.assertNotContains(Resposta, "de outro proprietario")
        self.assertContains(Resposta, '<option value="conta_cliente">Conta</option>', html=True)
        self.assertContains(Resposta, 'href="/vendas/historico">Limpar filtros</a>')

    def test_periodo_inclui_dia_inteiro_no_fuso_local(self):
        Resposta = self.Consultar(data_inicial=self.Dia.isoformat(), data_final=self.Dia.isoformat())
        self.assertContains(Resposta, 'class="LinhaHistoricoVenda"', count=2)
        self.assertContains(Resposta, "Cliente atual dinheiro")
        self.assertContains(Resposta, "Cliente atual pix")
        self.assertNotContains(Resposta, "Cliente atual conta_cliente")
        self.assertNotContains(Resposta, "Cliente do dia anterior")
        self.assertNotContains(Resposta, "Cliente antigo")
        self.assertContains(Resposta, f'value="{self.Dia.isoformat()}"', count=2)

    def test_datas_podem_ser_filtradas_separadamente(self):
        RespostaInicial = self.Consultar(data_inicial=(self.Dia + timedelta(days=1)).isoformat())
        self.assertContains(RespostaInicial, 'class="LinhaHistoricoVenda"', count=1)
        self.assertContains(RespostaInicial, "Cliente atual conta_cliente")
        RespostaFinal = self.Consultar(data_final=self.DiaAntigo.isoformat())
        self.assertContains(RespostaFinal, 'class="LinhaHistoricoVenda"', count=3)
        self.assertNotContains(RespostaFinal, "Cliente atual")

    def test_pagamentos_filtram_vendas_atuais_e_arquivadas(self):
        for Pagamento, _ in Venda.OpcoesFormaPagamento:
            with self.subTest(Pagamento=Pagamento):
                Resposta = self.Consultar(pagamento=Pagamento)
                Quantidade = 3 if Pagamento == Venda.DINHEIRO else 2
                self.assertContains(Resposta, 'class="LinhaHistoricoVenda"', count=Quantidade)
                self.assertContains(Resposta, f"Cliente atual {Pagamento}")
                self.assertContains(Resposta, f"Cliente antigo {Pagamento}")
                self.assertContains(Resposta, f'<option value="{Pagamento}" selected>')

    def test_situacao_separa_vendas_atuais_e_arquivadas(self):
        Atuais = self.Consultar(situacao="atual")
        self.assertContains(Atuais, 'class="LinhaHistoricoVenda"', count=4)
        self.assertNotContains(Atuais, "Cliente antigo")
        Arquivadas = self.Consultar(situacao="arquivada")
        self.assertContains(Arquivadas, 'class="LinhaHistoricoVenda"', count=3)
        self.assertNotContains(Arquivadas, "Cliente atual")

    def test_combina_busca_periodo_pagamento_e_situacao_sem_duplicar_vendas(self):
        Resposta = self.Consultar(
            busca="Arroz", data_inicial=self.Dia.isoformat(), data_final=self.Dia.isoformat(),
            pagamento="pix", situacao="atual",
        )
        self.assertContains(Resposta, 'class="LinhaHistoricoVenda"', count=1)
        self.assertContains(Resposta, "Arroz filtrado", count=2)
        self.assertContains(Resposta, 'value="Arroz"')
        self.assertContains(Resposta, 'aria-expanded="false"')
        self.assertNotContains(Resposta, "Arroz arquivado")
        self.assertNotContains(Resposta, "1,11")

    def test_busca_numero_cliente_e_produto_das_vendas_antigas(self):
        for Busca in ("Arroz arquivado", "Cliente antigo pix", str(self.Registros[Venda.PIX].VendaOriginalId)):
            with self.subTest(Busca=Busca):
                Resposta = self.Consultar(busca=Busca, pagamento="pix", situacao="arquivada")
                self.assertContains(Resposta, 'class="LinhaHistoricoVenda"', count=1)
                self.assertContains(Resposta, "Arroz arquivado")

        RespostaAtual = self.Consultar(busca=str(self.Vendas[Venda.PIX].pk), situacao="atual")
        self.assertContains(RespostaAtual, 'class="LinhaHistoricoVenda"', count=1)
        self.assertContains(RespostaAtual, "Cliente atual pix")

    def test_sem_resultado_oferece_limpar_filtros(self):
        Resposta = self.Consultar(busca="cliente inexistente", pagamento="pix")
        self.assertContains(Resposta, "Nenhuma venda corresponde aos filtros selecionados.")
        self.assertNotContains(Resposta, 'class="LinhaHistoricoVenda"')

    def test_filtros_invalidos_mostram_erro_sem_listar_vendas(self):
        Casos = [
            ({"data_inicial": "nao-e-data"}, "Informe uma data inicial válida."),
            ({"data_final": "2026-02-30"}, "Informe uma data final válida."),
            ({"data_inicial": "2026-10-20", "data_final": "2026-10-01"}, "A data final deve ser igual ou posterior à data inicial."),
            ({"pagamento": "invalido"}, "Selecione uma forma de pagamento válida."),
            ({"situacao": "invalida"}, "Selecione uma situação válida."),
        ]

        for Filtros, Erro in Casos:
            with self.subTest(Filtros=Filtros):
                Resposta = self.Consultar(**Filtros)
                self.assertContains(Resposta, Erro)
                self.assertContains(Resposta, 'aria-invalid="true"')
                self.assertContains(Resposta, "Corrija os filtros para consultar as vendas.")
                self.assertNotContains(Resposta, 'class="LinhaHistoricoVenda"')

    def test_texto_de_busca_e_escapado(self):
        Resposta = self.Consultar(busca='<script>alert("teste")</script>')
        self.assertNotContains(Resposta, '<script>alert("teste")</script>')
        self.assertContains(Resposta, "&lt;script&gt;")

    def test_BuscaIncrementalPreservaFormularioFiltrosEDetalhes(self):
        Resposta = self.Consultar(busca="Arroz", pagamento="pix", situacao="atual")
        for Identificador in ("FormularioBuscaVendas", "FiltroVendaBusca", "ResultadosVendas", "ErroBuscaVendas"):
            self.assertContains(Resposta, f'id="{Identificador}"')
        self.assertContains(Resposta, 'Campo.addEventListener("input"')
        self.assertContains(Resposta, '"busca-incremental-atualizada"')
        self.assertContains(Resposta, 'document.getElementById("ResultadosVendas").addEventListener("click"')
        self.assertContains(Resposta, '<option value="pix" selected>')
        self.assertContains(Resposta, '<option value="atual" selected>')
        self.assertContains(Resposta, "Arroz filtrado")
        self.assertNotContains(Resposta, "Arroz arquivado")

    def test_BuscaIncrementalMantemAlvosDosErrosAoCorrigirDatas(self):
        Invalida = self.Consultar(data_inicial="2026-10-20", data_final="2026-10-01")
        self.assertContains(Invalida, 'id="FiltroVendaDataFinalErro">A data final')
        self.assertContains(Invalida, 'aria-describedby="FiltroVendaDataFinalErro"')
        Valida = self.Consultar(data_inicial=self.Dia.isoformat(), data_final=self.Dia.isoformat())
        self.assertContains(Valida, 'id="FiltroVendaDataFinalErro" hidden>')
        self.assertNotContains(Valida, 'aria-invalid="true"')


class TesteLeitorCodigoBarras(TestCase):
    def setUp(self):
        self.Usuario = ObterModeloUsuario().objects.create_user(username="leitor_codigo")
        self.client.force_login(self.Usuario)
        self.Fornecedor = Fornecedor.objects.create(Nome="Fornecedor do leitor")
        self.Arroz = Produto.objects.create(
            Nome="Arroz com codigo", CodigoBarras="0012345678905", Categoria="Alimentos",
            Fornecedor=self.Fornecedor, QuantidadeEstoque=Decimal("2.000"),
            PrecoCusto=Decimal("6.00"), PrecoVenda=Decimal("10.00"),
        )
        self.LoteAntigo = self.Arroz.LotesEstoque.get()
        self.LoteNovo = LoteEstoque.objects.create(
            Produto=self.Arroz, Fornecedor=self.Fornecedor,
            QuantidadeInicial=Decimal("3.000"), QuantidadeDisponivel=Decimal("3.000"),
            PrecoCusto=Decimal("7.00"), PrecoVenda=Decimal("12.00"),
        )
        self.Arroz.SincronizarResumoLotes()
        self.Batata = Produto.objects.create(
            Nome="Batata com codigo", CodigoBarras="0009876543210", Fornecedor=self.Fornecedor,
            UnidadeVenda=Produto.QUILOGRAMA, QuantidadeEstoque=None, EstoqueMinimo=None,
            PrecoCusto=Decimal("2.00"), PrecoVenda=Decimal("4.00"),
        )

    def test_LeiturasRepetidasSomamUnidadesNoCarrinhoSelecionadoSemBaixa(self):
        for Numero in ["1", "1", "2"]:
            Resposta = self.client.post("/carrinho/ler-codigo", {"carrinho": Numero, "codigo": self.Arroz.CodigoBarras})
            self.assertEqual(Resposta.status_code, 200)
        Carrinhos = self.client.session["CarrinhosVenda"]
        self.assertEqual(Carrinhos["1"], {ObterChaveLote(self.LoteAntigo.id): "2.000"})
        self.assertEqual(Carrinhos["2"], {ObterChaveLote(self.LoteAntigo.id): "1.000"})
        self.Arroz.refresh_from_db()
        self.assertEqual(self.Arroz.QuantidadeEstoque, Decimal("5.000"))
        self.assertFalse(Venda.objects.exists())

    def test_LeituraDistribuiLotesEConcluiVendaComValoresCorretos(self):
        Resposta = self.client.post("/carrinho/ler-codigo", {
            "carrinho": "3", "codigo": self.Arroz.CodigoBarras, "quantidade": "4",
        })
        self.assertEqual(Resposta.status_code, 200)
        self.assertEqual(self.client.session["CarrinhosVenda"]["3"], {
            ObterChaveLote(self.LoteAntigo.id): "2.000", ObterChaveLote(self.LoteNovo.id): "2.000",
        })
        self.client.post("/carrinho/concluir", {"carrinho": "3", "forma_pagamento": Venda.PIX})
        VendaConcluida = Venda.objects.get()
        self.assertEqual(VendaConcluida.Total, Decimal("44.00"))
        self.assertEqual(VendaConcluida.Lucro, Decimal("18.00"))
        self.Arroz.refresh_from_db()
        self.assertEqual(self.Arroz.QuantidadeEstoque, Decimal("1.000"))

    def test_PesoExigeQuantidadeAntesDeAdicionar(self):
        Resposta = self.client.post("/carrinho/ler-codigo", {"codigo": self.Batata.CodigoBarras})
        self.assertTrue(Resposta.json()["RequerQuantidade"])
        self.assertNotIn("CarrinhosVenda", self.client.session)
        Resposta = self.client.post("/carrinho/ler-codigo", {"codigo": self.Batata.CodigoBarras, "quantidade": "0,750"})
        self.assertEqual(Resposta.status_code, 200)
        self.client.post("/carrinho/concluir", {"forma_pagamento": Venda.PIX})
        self.assertEqual(Venda.objects.get().Total, Decimal("3.00"))
        self.Batata.refresh_from_db()
        self.assertIsNone(self.Batata.QuantidadeEstoque)
        self.assertTrue(self.Batata.Disponivel)

    def test_LeituraExigeCodigoExatoEPreservaZeros(self):
        for Codigo in ["12345678905", "001234", "codigo desconhecido"]:
            with self.subTest(Codigo=Codigo):
                Resposta = self.client.post("/carrinho/ler-codigo", {"codigo": Codigo})
                self.assertEqual(Resposta.status_code, 404)
        self.assertNotIn("CarrinhosVenda", self.client.session)
        Pesquisa = self.client.get("/carrinho/pesquisar", {"busca": self.Arroz.CodigoBarras})
        self.assertEqual([Item["Id"] for Item in Pesquisa.json()["Produtos"]], [self.Arroz.id])

    def test_LeituraSemEstoqueEProdutoInativoNaoAlteramCarrinho(self):
        self.Arroz.LotesEstoque.update(QuantidadeDisponivel=Decimal("0.000"))
        Resposta = self.client.post("/carrinho/ler-codigo", {"codigo": self.Arroz.CodigoBarras})
        self.assertEqual(Resposta.status_code, 400)
        self.Arroz.Ativo = False
        self.Arroz.save(update_fields=["Ativo"])
        Resposta = self.client.post("/carrinho/ler-codigo", {"codigo": self.Arroz.CodigoBarras})
        self.assertEqual(Resposta.status_code, 404)
        self.assertNotIn("CarrinhosVenda", self.client.session)

    def test_LeituraRejeitaQuantidadeInvalidaECarrinhoInexistente(self):
        for Quantidade in ["NaN", "Infinity", "0", "-1", "0.0001", "1000000000"]:
            with self.subTest(Quantidade=Quantidade):
                Resposta = self.client.post("/carrinho/ler-codigo", {"codigo": self.Batata.CodigoBarras, "quantidade": Quantidade})
                self.assertEqual(Resposta.status_code, 400)
        Resposta = self.client.post("/carrinho/ler-codigo", {"carrinho": "4", "codigo": self.Arroz.CodigoBarras})
        self.assertEqual(Resposta.status_code, 400)
        self.assertNotIn("CarrinhosVenda", self.client.session)

    def test_PesquisaUnificadaNaoAdicionaNomesNemCodigosParciais(self):
        for Termo in ["Arroz", "001234", "99999999", "Produto " * 12]:
            with self.subTest(Termo=Termo):
                Resposta = self.client.post("/carrinho/ler-codigo", {
                    "carrinho": "2", "codigo": Termo, "permitir_pesquisa": "1",
                })
                self.assertEqual(Resposta.status_code, 200)
                self.assertEqual(Resposta.json(), {"Pesquisar": True})
        self.assertNotIn("CarrinhosVenda", self.client.session)
        self.assertFalse(Venda.objects.exists())

    def test_PesquisaUnificadaAdicionaCodigoAlfanumericoExato(self):
        self.Arroz.CodigoBarras = "ARZ-001"
        self.Arroz.save(update_fields=["CodigoBarras"])
        Resposta = self.client.post("/carrinho/ler-codigo", {
            "carrinho": "2", "codigo": "ARZ-001", "permitir_pesquisa": "1",
        })
        self.assertEqual(Resposta.status_code, 200)
        self.assertFalse(Resposta.json()["RequerQuantidade"])
        self.assertEqual(self.client.session["CarrinhosVenda"]["2"], {
            ObterChaveLote(self.LoteAntigo.id): "1.000",
        })

    def test_PesquisaUnificadaMantemErrosDeProdutoInativoECarrinhoInvalido(self):
        self.Arroz.Ativo = False
        self.Arroz.save(update_fields=["Ativo"])
        Resposta = self.client.post("/carrinho/ler-codigo", {
            "codigo": self.Arroz.CodigoBarras, "permitir_pesquisa": "1",
        })
        self.assertEqual(Resposta.status_code, 404)
        Resposta = self.client.post("/carrinho/ler-codigo", {
            "carrinho": "4", "codigo": "Arroz", "permitir_pesquisa": "1",
        })
        self.assertEqual(Resposta.status_code, 400)
        self.assertNotIn("CarrinhosVenda", self.client.session)

    def test_PaginasUsamBarraDePesquisaSemCampoSeparadoDeCodigo(self):
        Carrinho = self.client.get("/carrinho?carrinho=2&busca=Arroz")
        self.assertContains(Carrinho, 'id="BuscaProdutoCarrinho"')
        self.assertContains(Carrinho, 'data-leitor-codigo="2"')
        self.assertContains(Carrinho, 'value="Arroz"')
        self.assertNotContains(Carrinho, 'id="CodigoCarrinho-')
        Principal = self.client.get("/")
        for Numero in ["1", "2", "3"]:
            self.assertContains(Principal, f'id="BuscaCarrinho-{Numero}"')
            self.assertContains(Principal, f'data-leitor-codigo="{Numero}"')
        self.assertNotContains(Principal, 'id="CodigoCarrinho-')

    def test_LeituraProtegeMetodoCsrfEAutenticacao(self):
        self.assertEqual(self.client.get("/carrinho/ler-codigo").status_code, 405)
        ClienteCsrf = Client(enforce_csrf_checks=True)
        ClienteCsrf.force_login(self.Usuario)
        self.assertEqual(ClienteCsrf.post("/carrinho/ler-codigo", {"codigo": self.Arroz.CodigoBarras}).status_code, 403)
        self.client.logout()
        self.assertEqual(self.client.post("/carrinho/ler-codigo", {"codigo": self.Arroz.CodigoBarras}).status_code, 302)
        self.assertEqual(self.client.get("/estoque/ler-codigo", {"codigo": self.Arroz.CodigoBarras}).status_code, 302)


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
                "nome_cliente": "  maria   da Silva  ",
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

    def test_NomeDoCarrinhoRecebeInicialMaiusculaSemAlterarRestante(self):
        for NomeInformado, NomeEsperado in (
            ("  luiz  ", "Luiz"),
            ("álvaro da Silva", "Álvaro da Silva"),
            ("joão d'Ávila", "João d'Ávila"),
            ("ANA", "ANA"),
        ):
            with self.subTest(Nome=NomeInformado):
                self.client.post("/carrinho/nome", {"carrinho": "1", "nome_cliente": NomeInformado})
                self.assertEqual(self.client.session["NomesCarrinhosVenda"]["1"], NomeEsperado)
                self.assertContains(self.client.get("/carrinho"), NomeEsperado.replace("'", "&#x27;"))
        self.client.post("/carrinho/nome", {"carrinho": "1", "nome_cliente": "   "})
        self.assertNotIn("1", self.client.session["NomesCarrinhosVenda"])

    def test_PesquisaDoCarrinhoNaoMostraTextoIntrodutorio(self):
        for Busca in ("", "Arroz", "produto inexistente"):
            with self.subTest(Busca=Busca):
                Pagina = self.client.get("/carrinho", {"busca": Busca})
                self.assertNotContains(Pagina, "Pesquisar produtos")
                self.assertNotContains(Pagina, "Use o produto, a categoria, a marca ou o fornecedor na pesquisa.")
        self.assertContains(self.client.get("/carrinho", {"busca": "produto inexistente"}), "Nenhum produto disponível")

    def test_InicialMaiusculaReutilizaContinhaAnteriorSemDuplicar(self):
        ContaAnterior = ContaCliente.objects.create(Proprietario=self.Usuario, NomeCliente="luiz da Silva", Ativa=False)
        self.client.post("/carrinho/nome", {"carrinho": "1", "nome_cliente": "luiz da Silva"})
        self.AdicionarProduto("1", self.Arroz, "1")
        self.client.post("/carrinho/concluir", {"carrinho": "1", "forma_pagamento": Venda.CONTA_CLIENTE})
        VendaConcluida = Venda.objects.get()
        self.assertEqual(VendaConcluida.NomeCliente, "Luiz da Silva")
        self.assertEqual(VendaConcluida.ContaCliente, ContaAnterior)
        self.assertEqual(ContaCliente.objects.filter(Proprietario=self.Usuario).count(), 1)
        self.assertTrue(LancamentoContaCliente.objects.filter(Conta=ContaAnterior, Venda=VendaConcluida).exists())
        ContaAnterior.refresh_from_db()
        self.assertTrue(ContaAnterior.Ativa)

    def test_ContinhaComNomeExatoTemPreferenciaSemJuntarContasAnteriores(self):
        ContaCliente.objects.create(Proprietario=self.Usuario, NomeCliente="luiz")
        ContaExata = ContaCliente.objects.create(Proprietario=self.Usuario, NomeCliente="Luiz")
        self.client.post("/carrinho/nome", {"carrinho": "1", "nome_cliente": "luiz"})
        self.AdicionarProduto("1", self.Arroz, "1")
        self.client.post("/carrinho/concluir", {"carrinho": "1", "forma_pagamento": Venda.CONTA_CLIENTE})
        self.assertEqual(Venda.objects.get().ContaCliente, ContaExata)
        self.assertEqual(ContaCliente.objects.filter(Proprietario=self.Usuario).count(), 2)

    def test_ContinhasNaoMostramBotaoAbrirAtendimento(self):
        PaginaVazia = self.client.get("/continhas")
        self.assertContains(PaginaVazia, "Nenhuma continha encontrada")
        self.assertNotContains(PaginaVazia, "Abrir atendimento")

        ContaCliente.objects.create(Proprietario=self.Usuario, NomeCliente="Cliente teste")
        PaginaComConta = self.client.get("/continhas")
        self.assertContains(PaginaComConta, "Cliente teste")
        self.assertNotContains(PaginaComConta, "Abrir atendimento")

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
