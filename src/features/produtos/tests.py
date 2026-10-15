"""Testes da manutenção de produtos na área de estoque."""
from datetime import timedelta
from decimal import Decimal
import json
from unittest.mock import Mock, patch as Substituir
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode

from django.contrib.auth import get_user_model as ObterModeloUsuario
from django.core.cache import cache as Cache
from django.db import IntegrityError, transaction
from django.test import Client, SimpleTestCase, TestCase, override_settings as ConfigurarTeste
from django.utils import timezone

from features.fornecedor.models import Fornecedor

from .ApiProduto import ObterLotesDisponiveisProduto
from .ApiCatalogoProduto import ConsultarCatalogoProduto, LimiteRespostaCatalogo
from .ApiPesquisaWebProduto import ExtrairSugestaoPesquisa, PesquisarProdutoNaWeb, ValidarUrlFonte
from .FormularioProduto import FormularioEdicaoProduto, FormularioProduto
from .LogicaCatalogoProduto import ClassificarCategoriaCatalogo, ExtrairDadosCatalogo
from .LogicaCodigoBarras import EhCodigoGtin
from .models import LoteEstoque, Produto


@ConfigurarTeste(OPENAI_API_KEY="chave-de-teste", PESQUISA_PRODUTO_IA_ATIVA=True, PESQUISA_PRODUTO_IA_MODELO="modelo-teste")
class TestePesquisaWebProduto(SimpleTestCase):
    def setUp(self):
        Cache.clear()
        self.addCleanup(Cache.clear)
        self.Codigo = "7894650016091"
        self.Url = "https://loja.example/produto-pato"
        self.Sugestao = {
            "Encontrado": True, "Codigo": self.Codigo, "Nome": "Pato Limpeza Profunda 750ml",
            "Marca": "PATO", "Categoria": "Limpeza", "FonteUrl": self.Url,
            "Evidencia": f"Pato 750ml. Codigo de barras: {self.Codigo}",
        }

    def CriarResposta(self, Sugestao=None):
        return {"status": "completed", "output": [
            {"type": "web_search_call", "status": "completed", "action": {
                "type": "search", "sources": [{"type": "url", "url": self.Url}],
            }},
            {"type": "message", "content": [{"type": "output_text", "text": json.dumps(Sugestao or self.Sugestao)}]},
        ]}

    def CriarRespostaHttp(self):
        Resposta = Mock()
        Resposta.__enter__ = Mock(return_value=Resposta)
        Resposta.__exit__ = Mock(return_value=False)
        Resposta.read.return_value = json.dumps(self.CriarResposta()).encode()
        return Resposta

    def test_PesquisaExigeFonteConsultadaECodigoExatoESomenteSugereCamposPermitidos(self):
        Dados = ExtrairSugestaoPesquisa(self.CriarResposta(), self.Codigo)
        self.assertEqual(Dados["Dados"], {"Nome": "Pato Limpeza Profunda 750ml", "Marca": "pato", "Categoria": "Limpeza"})
        self.assertEqual(Dados["Fonte"]["Url"], self.Url)
        self.assertTrue(Dados["Fonte"]["PesquisaWeb"])

    def test_RejeitaDivergenciaFonteInventadaENomeAusente(self):
        for Alteracoes in (
            {"Codigo": "3017620422003"}, {"FonteUrl": "https://outra.example/produto"},
            {"Evidencia": "Sem codigo"}, {"Evidencia": f"0{self.Codigo}0"},
            {"Nome": ""}, {"Nome": "A" * 121}, {"Categoria": "Inventada"},
        ):
            with self.subTest(Alteracoes=Alteracoes):
                with self.assertRaises(ValueError):
                    ExtrairSugestaoPesquisa(self.CriarResposta({**self.Sugestao, **Alteracoes}), self.Codigo)
        SemPesquisa = self.CriarResposta()
        SemPesquisa["output"].pop(0)
        with self.assertRaises(ValueError):
            ExtrairSugestaoPesquisa(SemPesquisa, self.Codigo)

    def test_FontesInsegurasSaoRecusadasESaidaNaoViraHtml(self):
        for Url in ("javascript:alert(1)", "http://loja.example/item", "https://127.0.0.1/item", "https://localhost/item", "https://host.local/item", "https://user:senha@loja.example/item", "https://loja.example:8080/item", "https://loja.example/\nitem"):
            with self.subTest(Url=Url):
                self.assertEqual(ValidarUrlFonte(Url), "")
        Dados = ExtrairSugestaoPesquisa(self.CriarResposta({**self.Sugestao, "Nome": "<b>Pato</b>"}), self.Codigo)
        self.assertEqual(Dados["Dados"]["Nome"], "Pato")

    def test_AusenciaERecusaNaoInventamProduto(self):
        self.assertEqual(ExtrairSugestaoPesquisa(self.CriarResposta({**self.Sugestao, "Encontrado": False}), self.Codigo), {"Situacao": "nao_encontrado", "Dados": {}})
        for Resposta in ({"status": "incomplete"}, {"status": "completed", "output": []}, None):
            with self.subTest(Resposta=Resposta), self.assertRaises(ValueError):
                ExtrairSugestaoPesquisa(Resposta, self.Codigo)

    def test_RequisicaoUsaPesquisaObrigatoriaSemEnviarDadosDaLojaEReutilizaCache(self):
        with Substituir("features.produtos.ApiPesquisaWebProduto.AbrirUrl", return_value=self.CriarRespostaHttp()) as Abrir:
            Resultado = PesquisarProdutoNaWeb(self.Codigo, 77)
            self.assertEqual(Resultado["Situacao"], "encontrado")
            self.assertEqual(PesquisarProdutoNaWeb(self.Codigo, 88), Resultado)
        Abrir.assert_called_once()
        Requisicao = Abrir.call_args.args[0]
        self.assertEqual(Requisicao.full_url, "https://api.openai.com/v1/responses")
        Dados = json.loads(Requisicao.data)
        self.assertFalse(Dados["store"])
        self.assertEqual(Dados["tool_choice"], "required")
        self.assertEqual(Dados["tools"][0]["type"], "web_search")
        self.assertLessEqual(Dados["max_tool_calls"], 3)
        self.assertNotIn("UsuarioId", Requisicao.data.decode())
        self.assertNotIn("chave-de-teste", str(Resultado))

    def test_DesativadaSemChaveOuCodigoInvalidoNaoChamaApi(self):
        with Substituir("features.produtos.ApiPesquisaWebProduto.AbrirUrl") as Abrir:
            with ConfigurarTeste(PESQUISA_PRODUTO_IA_ATIVA=False):
                self.assertEqual(PesquisarProdutoNaWeb(self.Codigo, 1)["Situacao"], "nao_configurada")
            with ConfigurarTeste(OPENAI_API_KEY=""):
                self.assertEqual(PesquisarProdutoNaWeb(self.Codigo, 1)["Situacao"], "nao_configurada")
            for Codigo in ("ABC-001", "7894650016092"):
                self.assertEqual(PesquisarProdutoNaWeb(Codigo, 1)["Situacao"], "codigo_nao_consultavel")
        Abrir.assert_not_called()

    def test_LimitaFrequenciaEConsumoPorUsuario(self):
        Prefixo = "PesquisaProdutoWeb:v1:modelo-teste:"
        with Substituir("features.produtos.ApiPesquisaWebProduto.AbrirUrl") as Abrir:
            Cache.set(f"{Prefixo}Intervalo", True)
            self.assertEqual(PesquisarProdutoNaWeb(self.Codigo, 1)["Situacao"], "limite")
            Cache.delete(f"{Prefixo}Intervalo")
            Cache.set(f"{Prefixo}Usuario:1", 30)
            self.assertEqual(PesquisarProdutoNaWeb(self.Codigo, 1)["Situacao"], "limite")
        Abrir.assert_not_called()

    def test_ErrosDeRedeERespostasInvalidasMantemCadastroManual(self):
        for Erro in (URLError("offline"), TimeoutError(), HTTPError("url", 429, "limite", {}, None), ValueError("json")):
            Cache.clear()
            with self.subTest(Erro=Erro), Substituir("features.produtos.ApiPesquisaWebProduto.AbrirUrl", side_effect=Erro) as Abrir:
                self.assertEqual(PesquisarProdutoNaWeb(self.Codigo, 1), {"Situacao": "indisponivel", "Dados": {}})
                PesquisarProdutoNaWeb(self.Codigo, 1)
                Abrir.assert_called_once()


@ConfigurarTeste(OPENAI_API_KEY="chave-de-teste", PESQUISA_PRODUTO_IA_ATIVA=True)
class TesteRotaPesquisaWebProduto(TestCase):
    def setUp(self):
        self.Usuario = ObterModeloUsuario().objects.create_user(username="pesquisa_web")
        self.client.force_login(self.Usuario)
        self.Codigo = "7894650016091"
        self.Rota = "/estoque/pesquisar-codigo-web"

    def test_ProtegidaPorLoginPostECsrf(self):
        self.assertEqual(self.client.get(self.Rota).status_code, 405)
        self.assertEqual(Client().post(self.Rota).status_code, 302)
        ClienteCsrf = Client(enforce_csrf_checks=True)
        ClienteCsrf.force_login(self.Usuario)
        self.assertEqual(ClienteCsrf.post(self.Rota, {"codigo": self.Codigo}).status_code, 403)

    def test_PostSugereSemSalvarProdutoOuLote(self):
        with Substituir("features.produtos.ComponenteCatalogoProduto.PesquisarProdutoNaWeb", return_value={
            "Situacao": "encontrado", "Dados": {"Nome": "Pato", "Marca": "pato", "Categoria": "Limpeza"},
            "Fonte": {"Nome": "Loja", "Url": "https://loja.example/item", "PesquisaWeb": True},
        }) as Pesquisa:
            Resposta = self.client.post(self.Rota, {"codigo": self.Codigo})
        self.assertEqual(Resposta.json()["Dados"]["Marca"], "pato")
        self.assertIn("Confira", Resposta.json()["Mensagem"])
        self.assertIn("no-store", Resposta.headers["Cache-Control"])
        Pesquisa.assert_called_once_with(self.Codigo, self.Usuario.pk)
        self.assertFalse(Produto.objects.exists())
        self.assertFalse(LoteEstoque.objects.exists())

    def test_ProdutoJaCadastradoOuInativoNaoGeraPesquisaPaga(self):
        FornecedorTeste = Fornecedor.objects.create(Nome="Fornecedor web")
        ProdutoLocal = Produto.objects.create(Nome="Pato local", CodigoBarras=self.Codigo, Fornecedor=FornecedorTeste, PrecoVenda=Decimal("1.00"))
        with Substituir("features.produtos.ComponenteCatalogoProduto.PesquisarProdutoNaWeb") as Pesquisa:
            self.assertEqual(self.client.post(self.Rota, {"codigo": self.Codigo}).json()["Situacao"], "cadastrado")
            ProdutoLocal.Ativo = False
            ProdutoLocal.save(update_fields=["Ativo"])
            self.assertEqual(self.client.post(self.Rota, {"codigo": self.Codigo}).json()["Situacao"], "inativo")
        Pesquisa.assert_not_called()

    def test_CatalogoNaoAcionaIaNoGetESinalizaAlternativaApenasQuandoConfigurada(self):
        with Substituir("features.produtos.ComponenteCatalogoProduto.ConsultarCatalogoProduto", return_value={"Situacao": "nao_encontrado", "Dados": {}}), Substituir("features.produtos.ComponenteCatalogoProduto.PesquisarProdutoNaWeb") as Pesquisa:
            self.assertTrue(self.client.get("/estoque/consultar-codigo", {"codigo": self.Codigo}).json()["PesquisaWebDisponivel"])
            with ConfigurarTeste(OPENAI_API_KEY=""):
                self.assertFalse(self.client.get("/estoque/consultar-codigo", {"codigo": self.Codigo}).json()["PesquisaWebDisponivel"])
        Pesquisa.assert_not_called()


class TesteClassificacaoCatalogo(SimpleTestCase):
    def test_AlimentosPereciveisENaoPereciveisUsamMesmaCategoria(self):
        for Nome in ("Leite fresco", "Arroz", "Maçã", "Miojo", "Biscoito", "Carne congelada"):
            with self.subTest(Nome=Nome):
                self.assertEqual(ExtrairDadosCatalogo({
                    "product_name_pt": Nome, "product_type": "food",
                    "categories_tags_pt": ["Categoria especifica do alimento"],
                })["Categoria"], "Alimentos")

    def test_AlimentoSemCategoriaNoCatalogoRecebeAlimentos(self):
        self.assertEqual(ExtrairDadosCatalogo({
            "product_name": "Macarrão Instantâneo", "brands": "NISSIN",
        }, TipoCatalogo="food"), {
            "Nome": "Macarrão Instantâneo", "Marca": "nissin", "Categoria": "Alimentos",
        })

    def test_MedicamentosEHigieneUsamFarmacia(self):
        Casos = [
            {"product_type": "beauty", "product_name": "Shampoo de leite de coco"},
            {"product_type": "product", "categories_tags": ["en:medicines"]},
            {"categories_tags_pt": ["FARMÁCIA", "Medicamentos"]},
            {"product_name_pt": "Creme dental"},
            {"categories_tags": ["en:personal-care", "en:oral-care"]},
        ]
        for ProdutoCatalogo in Casos:
            with self.subTest(ProdutoCatalogo=ProdutoCatalogo):
                self.assertEqual(ClassificarCategoriaCatalogo(ProdutoCatalogo), "Farmácia")

    def test_FerramentasEFerragensUsamFerragem(self):
        Casos = [
            {"categories_tags": ["en:hardware", "en:fasteners"]},
            {"categories_tags": ["en:power-tools"]},
            {"categories_tags_pt": ["Ferramentas elétricas"]},
            {"product_type": "product", "product_name_pt": "Parafuso sextavado"},
            {"product_name": "Alicate universal"},
        ]
        for ProdutoCatalogo in Casos:
            with self.subTest(ProdutoCatalogo=ProdutoCatalogo):
                self.assertEqual(ClassificarCategoriaCatalogo(ProdutoCatalogo), "Ferragem")

    def test_NaoClassificaProdutosGenericosOuCategoriasAmbiguasComoAlimentos(self):
        Casos = [
            {}, {"product_type": "product", "product_name": "Caderno universitário"},
            {"categories_tags": ["en:tools", "en:medicines"]},
            {"brands": "Farmácia Exemplo", "product_name": "Produto desconhecido"},
            {"categories_tags": [None, {}, 123], "categories_tags_pt": "Ferragem"},
        ]
        for ProdutoCatalogo in Casos:
            with self.subTest(ProdutoCatalogo=ProdutoCatalogo):
                self.assertEqual(ClassificarCategoriaCatalogo(ProdutoCatalogo), "")

    def test_TipoAlimenticioNaoViraFarmaciaPorPalavraNoNome(self):
        self.assertEqual(ClassificarCategoriaCatalogo({
            "product_type": "food", "product_name": "Chá da Farmácia Exemplo",
        }), "Alimentos")

    def test_MarcasSugeridasEmMinusculasSemMudarNomeDoProduto(self):
        for Marca in ("NISSIN", "L'ORÉAL", "3M, BOSCH", "Nestlé"):
            with self.subTest(Marca=Marca):
                Dados = ExtrairDadosCatalogo({"product_name": "Nome Original", "brands": Marca})
                self.assertEqual(Dados["Marca"], Marca.lower())
                self.assertEqual(Dados["Nome"], "Nome Original")
        self.assertNotIn("Marca", ExtrairDadosCatalogo({"brands": "İ" * 80}))

    def test_ProdutosDeLimpezaNaoSaoAlimentosNemHigienePessoal(self):
        for ProdutoCatalogo in (
            {"categories_tags": ["en:household-cleaners"]},
            {"categories_tags_pt": ["Produtos de limpeza", "Detergentes"]},
            {"product_name_pt": "Desinfetante sanitario"},
            {"product_type": "beauty", "categories_tags": ["en:toilet-cleaners"]},
        ):
            with self.subTest(ProdutoCatalogo=ProdutoCatalogo):
                self.assertEqual(ClassificarCategoriaCatalogo(ProdutoCatalogo), "Limpeza")


class TesteApiCatalogoProduto(SimpleTestCase):
    def test_PatoTemReferenciaComplementarSemConsultaExterna(self):
        with Substituir("features.produtos.ApiCatalogoProduto.AbrirUrl") as Abrir:
            for Codigo in ("7894650016091", "07894650016091"):
                Resultado = ConsultarCatalogoProduto(Codigo)
                self.assertEqual(Resultado["Situacao"], "encontrado")
                self.assertEqual(Resultado["Dados"]["Marca"], "pato")
                self.assertEqual(Resultado["Dados"]["Categoria"], "Limpeza")
                self.assertIn("750ml", Resultado["Dados"]["Nome"])
                self.assertTrue(Resultado["Fonte"]["Complementar"])
            Abrir.assert_not_called()

    def setUp(self):
        Cache.clear()
        self.Codigo = "3017620422003"
        self.ProdutoCatalogo = {
            "code": self.Codigo, "product_name_pt": "Creme de avela",
            "product_name": "Hazelnut cream", "brands": "MARCA EXEMPLO", "product_type": "food",
            "categories_tags_pt": ["Alimentos", "Doces para barrar", "en:unknown"],
            "expiration_date": "2028-01-01", "price": 99, "quantity": "400 g",
        }

    def tearDown(self):
        Cache.clear()

    def CriarResposta(self, ProdutoCatalogo=None):
        Resposta = Mock()
        Resposta.__enter__ = Mock(return_value=Resposta)
        Resposta.__exit__ = Mock(return_value=False)
        Resposta.geturl.return_value = f"https://world.openfoodfacts.org/api/v3.6/product/{self.Codigo}"
        Resposta.read.return_value = json.dumps({
            "status": "success", "product": ProdutoCatalogo or self.ProdutoCatalogo,
        }).encode()
        return Resposta

    def test_ValidaGtinSemPerderZerosNemConfundirTextoComCodigo(self):
        for Codigo in ("96385074", "036000291452", self.Codigo, "03017620422003"):
            with self.subTest(Codigo=Codigo):
                self.assertTrue(EhCodigoGtin(Codigo))
        for Codigo in (None, "", "Arroz", "ABC-001", "001234", "3017620422004", "0000000000000", "٣" * 13):
            with self.subTest(Codigo=Codigo):
                self.assertFalse(EhCodigoGtin(Codigo))

    def test_ConsultaPedeApenasDadosDeCadastroEUsaCache(self):
        Resposta = self.CriarResposta()
        with Substituir("features.produtos.ApiCatalogoProduto.AbrirUrl", return_value=Resposta) as Abrir:
            Resultado = ConsultarCatalogoProduto(self.Codigo)
            self.assertEqual(Resultado, {
                "Situacao": "encontrado", "Dados": {
                    "Nome": "Creme de avela", "Marca": "marca exemplo", "Categoria": "Alimentos",
                },
                "Fonte": {"Nome": "Open Food Facts", "Url": f"https://world.openfoodfacts.org/product/{self.Codigo}"},
            })
            self.assertEqual(ConsultarCatalogoProduto(self.Codigo), Resultado)
        Abrir.assert_called_once()
        Requisicao = Abrir.call_args.args[0]
        self.assertTrue(Requisicao.full_url.startswith("https://world.openfoodfacts.org/api/v3.6/product/3017620422003?"))
        self.assertIn("categories_tags_pt", Requisicao.full_url)
        self.assertIn("product_type=all", Requisicao.full_url)
        self.assertNotIn("expiration", Requisicao.full_url)
        self.assertIn("ControleEstoque/", Requisicao.get_header("User-agent"))
        self.assertEqual(Abrir.call_args.kwargs["timeout"], 4)
        Resposta.read.assert_called_once_with(LimiteRespostaCatalogo + 1)

    def test_NaoConsultaCodigosInternosTextosOuUrls(self):
        with Substituir("features.produtos.ApiCatalogoProduto.AbrirUrl") as Abrir:
            for Codigo in ("ABC-001", "3017620422004", "https://example.com", "123", ""):
                self.assertEqual(ConsultarCatalogoProduto(Codigo)["Situacao"], "codigo_nao_consultavel")
        Abrir.assert_not_called()

    def test_LimitaConsultasNovasSemImpedirCache(self):
        with Substituir("features.produtos.ApiCatalogoProduto.AbrirUrl", return_value=self.CriarResposta()) as Abrir:
            ConsultarCatalogoProduto(self.Codigo)
            self.assertEqual(ConsultarCatalogoProduto("036000291452")["Situacao"], "indisponivel")
            self.assertEqual(ConsultarCatalogoProduto(self.Codigo)["Situacao"], "encontrado")
        Abrir.assert_called_once()

    def test_ProdutoNaoEncontradoEhArmazenadoNoCache(self):
        with Substituir("features.produtos.ApiCatalogoProduto.AbrirUrl", side_effect=HTTPError("url", 404, "Not found", {}, None)) as Abrir:
            self.assertEqual(ConsultarCatalogoProduto(self.Codigo), {"Situacao": "nao_encontrado", "Dados": {}})
            self.assertEqual(ConsultarCatalogoProduto(self.Codigo)["Situacao"], "nao_encontrado")
        Abrir.assert_called_once()

    def test_FalhasDeRedeELimitesNaoImpedemCadastro(self):
        for Erro in (URLError("offline"), TimeoutError(), HTTPError("url", 429, "Limit", {}, None), HTTPError("url", 503, "Unavailable", {}, None)):
            with self.subTest(Erro=Erro):
                Cache.clear()
                with Substituir("features.produtos.ApiCatalogoProduto.AbrirUrl", side_effect=Erro) as Abrir:
                    self.assertEqual(ConsultarCatalogoProduto(self.Codigo), {"Situacao": "indisponivel", "Dados": {}})
                    ConsultarCatalogoProduto(self.Codigo)
                Abrir.assert_called_once()

    def test_RespostasInvalidasOuGrandesSaoIgnoradas(self):
        Conteudos = [b"not json", b"null", b"[]", b"{}", b"x" * (LimiteRespostaCatalogo + 1)]
        for ProdutoCatalogo in ({"code": "036000291452"}, {"code": None}):
            Conteudos.append(json.dumps({"status": "success", "product": ProdutoCatalogo}).encode())
        for Conteudo in Conteudos:
            with self.subTest(Conteudo=Conteudo[:100]):
                Cache.clear()
                Resposta = self.CriarResposta()
                Resposta.read.return_value = Conteudo
                with Substituir("features.produtos.ApiCatalogoProduto.AbrirUrl", return_value=Resposta):
                    self.assertEqual(ConsultarCatalogoProduto(self.Codigo)["Situacao"], "indisponivel")

    def test_DadosParciaisNaoInventamCamposENaoTrazemValidade(self):
        self.assertEqual(ExtrairDadosCatalogo({"brands": "Marca sem nome"}), {"Marca": "marca sem nome"})
        self.assertEqual(ExtrairDadosCatalogo({"expiration_date": "2028-01-01", "categories_tags_pt": ["en:unknown"]}), {})
        self.assertEqual(ExtrairDadosCatalogo({"product_name_pt": [], "product_name": "Original", "brands": {}, "categories_tags_pt": "Alimentos"}), {"Nome": "Original"})

    def test_LimpaMarcacoesEEvitaSugestoesMaioresQueOsCampos(self):
        self.assertEqual(ExtrairDadosCatalogo({
            "product_name_pt": "<b> Arroz </b> \n integral", "brands": "B" * 81,
            "categories_tags_pt": ["Alimentos", "C" * 81],
        }), {"Nome": "Arroz integral", "Categoria": "Alimentos"})
        self.assertEqual(ExtrairDadosCatalogo({"product_name": "N" * 121, "brands": "x\x00y"}), {})

    def test_CatalogoSemCategoriaEspecificaAindaClassificaAlimentos(self):
        Resposta = self.CriarResposta({"code": self.Codigo, "product_name": "Miojo", "brands": "NISSIN"})
        with Substituir("features.produtos.ApiCatalogoProduto.AbrirUrl", return_value=Resposta):
            self.assertEqual(ConsultarCatalogoProduto(self.Codigo)["Dados"], {
                "Nome": "Miojo", "Marca": "nissin", "Categoria": "Alimentos",
            })

    def test_RedirecionamentoParaCatalogoDeHigieneUsaFarmaciaEFonteCorreta(self):
        Resposta = self.CriarResposta({
            "code": self.Codigo, "product_name": "Shampoo", "brands": "MARCA DE HIGIENE",
        })
        Resposta.geturl.return_value = f"https://br.openbeautyfacts.org/api/v3.6/product/{self.Codigo}"
        with Substituir("features.produtos.ApiCatalogoProduto.AbrirUrl", return_value=Resposta):
            Resultado = ConsultarCatalogoProduto(self.Codigo)
        self.assertEqual(Resultado["Dados"], {"Nome": "Shampoo", "Marca": "marca de higiene", "Categoria": "Farmácia"})
        self.assertEqual(Resultado["Fonte"], {
            "Nome": "Open Beauty Facts", "Url": f"https://world.openbeautyfacts.org/product/{self.Codigo}",
        })

    def test_CatalogoDeProdutosClassificaFerragemSemTratarTudoComoAlimento(self):
        for Nome, Categorias, CategoriaEsperada in (
            ("Parafuso", ["en:fasteners"], "Ferragem"),
            ("Medicamento", ["en:medicines"], "Farmácia"),
            ("Caderno", ["en:stationery"], None),
        ):
            with self.subTest(Nome=Nome):
                Cache.clear()
                Resposta = self.CriarResposta({
                    "code": self.Codigo, "product_name": Nome, "brands": "MARCA",
                    "categories_tags": Categorias,
                })
                Resposta.geturl.return_value = f"https://br.openproductsfacts.org/api/v3.6/product/{self.Codigo}"
                with Substituir("features.produtos.ApiCatalogoProduto.AbrirUrl", return_value=Resposta):
                    Resultado = ConsultarCatalogoProduto(self.Codigo)
                self.assertEqual(Resultado["Dados"].get("Categoria"), CategoriaEsperada)
                self.assertEqual(Resultado["Fonte"]["Nome"], "Open Products Facts")

    def test_NaoUsaCacheAntigoComCategoriasEspecificasEMarcaMaiuscula(self):
        Cache.set(f"CatalogoProduto:v1:{self.Codigo}", {
            "Situacao": "encontrado", "Dados": {"Marca": "MARCA", "Categoria": "Doces"},
        })
        with Substituir("features.produtos.ApiCatalogoProduto.AbrirUrl", return_value=self.CriarResposta()) as Abrir:
            Resultado = ConsultarCatalogoProduto(self.Codigo)
        Abrir.assert_called_once()
        self.assertEqual(Resultado["Dados"]["Marca"], "marca exemplo")
        self.assertEqual(Resultado["Dados"]["Categoria"], "Alimentos")

    def test_FontesDesconhecidasOuSemHttpsSaoIgnoradas(self):
        for Url in ("http://world.openfoodfacts.org/api", "https://openfoodfacts.org.example.com/api"):
            with self.subTest(Url=Url):
                Cache.clear()
                Resposta = self.CriarResposta()
                Resposta.geturl.return_value = Url
                with Substituir("features.produtos.ApiCatalogoProduto.AbrirUrl", return_value=Resposta):
                    self.assertEqual(ConsultarCatalogoProduto(self.Codigo)["Situacao"], "indisponivel")


class TesteCadastroComCatalogo(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.Usuario = ObterModeloUsuario().objects.create_user(username="catalogo_produtos")
        cls.Fornecedor = Fornecedor.objects.create(Nome="Fornecedor do catalogo")
        cls.Codigo = "3017620422003"

    def setUp(self):
        self.client.force_login(self.Usuario)
        self.Substituicao = Substituir("features.produtos.ComponenteCatalogoProduto.ConsultarCatalogoProduto", return_value={
            "Situacao": "encontrado", "Dados": {"Nome": "Creme de avela", "Marca": "marca exemplo", "Categoria": "Alimentos"},
        })
        self.Consultar = self.Substituicao.start()
        self.addCleanup(self.Substituicao.stop)

    def test_ConsultaProtegidaESomenteGet(self):
        self.assertEqual(self.client.post("/estoque/consultar-codigo").status_code, 405)
        self.client.logout()
        self.assertRedirects(self.client.get("/estoque/consultar-codigo", {"codigo": self.Codigo}),
            f"/login?next=/estoque/consultar-codigo%3Fcodigo%3D{self.Codigo}", fetch_redirect_response=False)
        self.Consultar.assert_not_called()

    def test_ConsultaSugereDadosSemSalvarProdutoOuLote(self):
        Resposta = self.client.get("/estoque/consultar-codigo", {"codigo": f" {self.Codigo} "})
        self.assertEqual(Resposta.json()["Dados"], {"Nome": "Creme de avela", "Marca": "marca exemplo", "Categoria": "Alimentos"})
        self.Consultar.assert_called_once_with(self.Codigo)
        self.assertEqual(Produto.objects.count(), 0)
        self.assertEqual(LoteEstoque.objects.count(), 0)
        self.assertIn("no-store", Resposta.headers["Cache-Control"])

    def test_CodigosInvalidosNaoChegamAoCatalogo(self):
        for Codigo in ("", "a" * 65, "ABC\x00DEF"):
            with self.subTest(Codigo=Codigo):
                self.assertEqual(self.client.get("/estoque/consultar-codigo", {"codigo": Codigo}).status_code, 400)
        self.Consultar.assert_not_called()

    def test_ProdutoLocalAbreNovaEntradaSemChamarCatalogo(self):
        ProdutoLocal = Produto.objects.create(Nome="Produto local", CodigoBarras="ABC-001", Fornecedor=self.Fornecedor, PrecoVenda=Decimal("1.00"))
        Resposta = self.client.get("/estoque/consultar-codigo", {"codigo": "ABC-001"})
        self.assertEqual(Resposta.json(), {"Situacao": "cadastrado", "Destino": f"/estoque/{ProdutoLocal.pk}/editar?entrada=1#NovaEntradaEstoque"})
        self.Consultar.assert_not_called()
        self.assertEqual(ProdutoLocal.LotesEstoque.count(), 1)

    def test_ProdutoInativoNaoRecebeSugestoesNemNovaEntrada(self):
        Produto.objects.create(Nome="Produto inativo", CodigoBarras=self.Codigo, Fornecedor=self.Fornecedor, Ativo=False, PrecoVenda=Decimal("1.00"))
        Resposta = self.client.get("/estoque/consultar-codigo", {"codigo": self.Codigo})
        self.assertEqual(Resposta.json()["Situacao"], "inativo")
        self.assertNotIn("Destino", Resposta.json())
        self.Consultar.assert_not_called()

    def test_EstoqueAbreCadastroParaGtinNovoSemAlterarBuscaNormal(self):
        Resposta = self.client.get("/estoque/ler-codigo", {"codigo": self.Codigo, "permitir_pesquisa": "1"})
        self.assertRedirects(Resposta, f"/estoque/novo?codigo={self.Codigo}")
        Pagina = self.client.get(Resposta.url)
        self.assertContains(Pagina, f'name="CodigoBarras" value="{self.Codigo}"')
        self.assertContains(Pagina, "if (true) ConsultarCodigo();")
        self.Consultar.assert_not_called()

    def test_FormularioSemCodigoNaoConsultaEEdicaoMantemFluxoAnterior(self):
        self.assertContains(self.client.get("/estoque/novo"), "if (false) ConsultarCodigo();")
        ProdutoLocal = Produto.objects.create(Nome="Produto para editar", Fornecedor=self.Fornecedor, PrecoVenda=Decimal("1.00"))
        PaginaEdicao = self.client.get(f"/estoque/{ProdutoLocal.pk}/editar")
        self.assertNotContains(PaginaEdicao, 'id="ConsultaCatalogoProduto"')
        self.Consultar.assert_not_called()

    def test_CadastroVazioRecebeLeitorNoCampoCodigoDeBarras(self):
        Formulario = FormularioProduto()
        self.assertTrue(Formulario.fields["CodigoBarras"].widget.attrs.get("autofocus"))
        self.assertNotIn("autofocus", Formulario.fields["Nome"].widget.attrs)
        self.assertContains(self.client.get("/estoque/novo"), "autofocus", count=1)

    def test_CodigoRecebidoNaUrlMantemFocoNoNomeParaRevisao(self):
        Formulario = FormularioProduto(initial={"CodigoBarras": self.Codigo})
        self.assertTrue(Formulario.fields["Nome"].widget.attrs.get("autofocus"))
        self.assertNotIn("autofocus", Formulario.fields["CodigoBarras"].widget.attrs)

    def test_ErrosDeCadastroEEdicaoNaoMudamFocoParaLeitor(self):
        for Formulario in (FormularioProduto({"Nome": "Nome manual"}), FormularioEdicaoProduto()):
            with self.subTest(Formulario=Formulario.__class__.__name__):
                self.assertTrue(Formulario.fields["Nome"].widget.attrs.get("autofocus"))
                self.assertNotIn("autofocus", Formulario.fields["CodigoBarras"].widget.attrs)

    def test_FalhasEProdutoAusenteRetornamEstadoManual(self):
        for Situacao in ("nao_encontrado", "indisponivel", "codigo_nao_consultavel"):
            with self.subTest(Situacao=Situacao):
                self.Consultar.return_value = {"Situacao": Situacao, "Dados": {}}
                Resposta = self.client.get("/estoque/consultar-codigo", {"codigo": self.Codigo})
                self.assertEqual(Resposta.status_code, 200)
                self.assertEqual(Resposta.json()["Situacao"], Situacao)
                self.assertTrue(Resposta.json()["Mensagem"])
        self.assertFalse(Produto.objects.exists())

    def test_PostInvalidoPreservaValoresManuaisSemConsultaAutomatica(self):
        Resposta = self.client.post(f"/estoque/novo?codigo={self.Codigo}", {
            "Nome": "Nome corrigido", "Marca": "Marca corrigida", "Categoria": "Categoria corrigida",
            "CodigoBarras": self.Codigo, "DataValidade": "2028-12-31",
        })
        for Valor in ("Nome corrigido", "Marca corrigida", "Categoria corrigida", "2028-12-31"):
            self.assertContains(Resposta, f'value="{Valor}"')
        self.assertContains(Resposta, "if (false) ConsultarCodigo();")
        self.Consultar.assert_not_called()
        self.assertFalse(Produto.objects.exists())

    def test_CadastroConfirmadoUsaDadosManuaisEValidadeDoVendedor(self):
        Resposta = self.client.post("/estoque/novo", {
            "Nome": "Nome confirmado", "Marca": "Marca confirmada", "Categoria": "Categoria confirmada",
            "CodigoBarras": self.Codigo, "Fornecedor": self.Fornecedor.pk,
            "DataValidade": "2028-12-31", "UnidadeVenda": Produto.UNIDADE,
            "PrecoCusto": "4.00", "PrecoVenda": "7.00", "QuantidadeEstoque": "5", "EstoqueMinimo": "1",
        })
        self.assertRedirects(Resposta, "/estoque")
        ProdutoCriado = Produto.objects.get(CodigoBarras=self.Codigo)
        self.assertEqual(ProdutoCriado.Nome, "Nome confirmado")
        self.assertEqual(ProdutoCriado.Marca, "Marca confirmada")
        self.assertEqual(ProdutoCriado.Categoria, "Categoria confirmada")
        self.assertEqual(ProdutoCriado.LotesEstoque.get().DataValidade.isoformat(), "2028-12-31")
        self.Consultar.assert_not_called()


class TesteValidadeLote(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.Usuario = ObterModeloUsuario().objects.create_user(username="validade_lotes")
        cls.Fornecedor = Fornecedor.objects.create(Nome="Fornecedor de validade")
        cls.Validade = timezone.localdate() + timedelta(days=90)
        cls.Produto = Produto.objects.create(
            Nome="Arroz com validade", Categoria="Alimentos", Fornecedor=cls.Fornecedor,
            PrecoCusto=Decimal("5.00"), PrecoVenda=Decimal("8.00"),
            QuantidadeEstoque=Decimal("10.000"), EstoqueMinimo=Decimal("2.000"),
        )

    def setUp(self):
        self.client.force_login(self.Usuario)

    def DadosCadastro(self, **Valores):
        return {
            "Nome": "Novo produto com validade", "Categoria": "Alimentos",
            "Fornecedor": self.Fornecedor.pk, "UnidadeVenda": Produto.UNIDADE,
            "PrecoCusto": "4.00", "PrecoVenda": "7.00",
            "QuantidadeEstoque": "5", "EstoqueMinimo": "1",
            **Valores,
        }

    def DadosEntrada(self, **Valores):
        return {
            "acao": "adicionar_lote", "Lote-Fornecedor": self.Fornecedor.pk,
            "Lote-PrecoCusto": "6.00", "Lote-PrecoVenda": "9.00",
            "Lote-QuantidadeEntrada": "6", **Valores,
        }

    def test_CadastroInicialGravaValidadeNoPrimeiroLote(self):
        Resposta = self.client.post("/estoque/novo", self.DadosCadastro(
            DataValidade=self.Validade.isoformat(), CodigoBarras="0099999999999",
        ))
        self.assertRedirects(Resposta, "/estoque")
        ProdutoCriado = Produto.objects.get(Nome="Novo produto com validade")
        Lote = ProdutoCriado.LotesEstoque.get()
        self.assertEqual(Lote.DataValidade, self.Validade)
        self.assertEqual(Lote.Numero, 1)
        self.assertEqual(ProdutoCriado.CodigoBarras, "0099999999999")
        self.assertEqual(Lote.QuantidadeDisponivel, Decimal("5.000"))

    def test_ValidadeOpcionalPreservaLotesSemDataInformada(self):
        self.assertIsNone(self.Produto.LotesEstoque.get().DataValidade)
        Resposta = self.client.post("/estoque/novo", self.DadosCadastro())
        self.assertRedirects(Resposta, "/estoque")
        ProdutoCriado = Produto.objects.get(Nome="Novo produto com validade")
        self.assertIsNone(ProdutoCriado.LotesEstoque.get().DataValidade)
        RespostaEntrada = self.client.post(
            f"/estoque/{self.Produto.pk}/editar", self.DadosEntrada()
        )
        self.assertRedirects(RespostaEntrada, f"/estoque/{self.Produto.pk}/editar")
        self.assertIsNone(self.Produto.LotesEstoque.get(Numero=2).DataValidade)

    def test_CadastroRejeitaDataInvalidaSemCriarProdutoOuLote(self):
        Resposta = self.client.post("/estoque/novo", self.DadosCadastro(DataValidade="2026-02-30"))
        self.assertContains(Resposta, "Informe uma data de validade válida.")
        self.assertEqual(Produto.objects.count(), 1)
        self.assertEqual(LoteEstoque.objects.count(), 1)

    def test_NovaEntradaPreservaValidadeDoLoteAnteriorEOrdemDeSaida(self):
        LoteAnterior = self.Produto.LotesEstoque.get()
        LoteAnterior.DataValidade = self.Validade
        LoteAnterior.save(update_fields=["DataValidade"])
        ValidadeNova = self.Validade - timedelta(days=30)
        Resposta = self.client.post(f"/estoque/{self.Produto.pk}/editar", self.DadosEntrada(
            **{"Lote-DataValidade": ValidadeNova.isoformat()},
        ))
        self.assertRedirects(Resposta, f"/estoque/{self.Produto.pk}/editar")
        NovoLote = self.Produto.LotesEstoque.get(Numero=2)
        LoteAnterior.refresh_from_db()
        self.Produto.refresh_from_db()
        self.assertEqual(LoteAnterior.DataValidade, self.Validade)
        self.assertEqual(NovoLote.DataValidade, ValidadeNova)
        self.assertEqual(LoteAnterior.PrecoCusto, Decimal("5.00"))
        self.assertEqual(LoteAnterior.QuantidadeDisponivel, Decimal("10.000"))
        self.assertEqual(NovoLote.QuantidadeDisponivel, Decimal("6.000"))
        self.assertEqual(self.Produto.QuantidadeEstoque, Decimal("16.000"))
        self.assertEqual(
            [Lote.pk for Lote in ObterLotesDisponiveisProduto(self.Produto)],
            [LoteAnterior.pk, NovoLote.pk],
        )

    def test_NovaEntradaComValidadeInvalidaNaoAlteraLotesOuResumo(self):
        Resposta = self.client.post(f"/estoque/{self.Produto.pk}/editar", self.DadosEntrada(
            **{"Lote-DataValidade": "invalida"},
        ))
        self.assertContains(Resposta, "Informe uma data de validade válida.")
        self.assertEqual(self.Produto.LotesEstoque.count(), 1)
        self.Produto.refresh_from_db()
        self.assertEqual(self.Produto.QuantidadeEstoque, Decimal("10.000"))
        self.assertEqual(self.Produto.PrecoVenda, Decimal("8.00"))

    def test_ValidadeTambemFuncionaEmLotesPorQuilograma(self):
        Resposta = self.client.post("/estoque/novo", self.DadosCadastro(
            Nome="Tomate com validade", UnidadeVenda=Produto.QUILOGRAMA,
            DataValidade=self.Validade.isoformat(), Disponivel="on",
        ))
        self.assertRedirects(Resposta, "/estoque")
        Tomate = Produto.objects.get(Nome="Tomate com validade")
        LoteInicial = Tomate.LotesEstoque.get()
        self.assertEqual(LoteInicial.DataValidade, self.Validade)
        self.assertIsNone(LoteInicial.QuantidadeDisponivel)
        RespostaEntrada = self.client.post(f"/estoque/{Tomate.pk}/editar", self.DadosEntrada(
            **{"Lote-DataValidade": self.Validade.isoformat(), "Lote-Disponivel": "on"},
        ))
        self.assertRedirects(RespostaEntrada, f"/estoque/{Tomate.pk}/editar")
        NovoLote = Tomate.LotesEstoque.get(Numero=2)
        self.assertEqual(NovoLote.DataValidade, self.Validade)
        self.assertIsNone(NovoLote.QuantidadeDisponivel)
        Tomate.refresh_from_db()
        self.assertIsNone(Tomate.QuantidadeEstoque)
        self.assertTrue(Tomate.Disponivel)

    def test_CorrigeELimpaValidadeSemAlterarEntradaSaldoOuPrecos(self):
        Lote = self.Produto.LotesEstoque.get()
        DadosOriginais = (Lote.CriadoEm, Lote.QuantidadeDisponivel, Lote.PrecoCusto, Lote.PrecoVenda)
        Rota = f"/estoque/{self.Produto.pk}/lotes/{Lote.pk}/validade"
        Resposta = self.client.post(Rota, {"DataValidade": self.Validade.isoformat()})
        self.assertRedirects(Resposta, f"/estoque/{self.Produto.pk}/editar")
        Lote.refresh_from_db()
        self.assertEqual(Lote.DataValidade, self.Validade)
        self.assertEqual(
            (Lote.CriadoEm, Lote.QuantidadeDisponivel, Lote.PrecoCusto, Lote.PrecoVenda),
            DadosOriginais,
        )
        RespostaLimpar = self.client.post(Rota, {"DataValidade": ""})
        self.assertRedirects(RespostaLimpar, f"/estoque/{self.Produto.pk}/editar")
        Lote.refresh_from_db()
        self.assertIsNone(Lote.DataValidade)
        self.Produto.refresh_from_db()
        self.assertEqual(self.Produto.QuantidadeEstoque, Decimal("10.000"))

    def test_CorrecaoInvalidaPreservaValidadeAnterior(self):
        Lote = self.Produto.LotesEstoque.get()
        Lote.DataValidade = self.Validade
        Lote.save(update_fields=["DataValidade"])
        Rota = f"/estoque/{self.Produto.pk}/lotes/{Lote.pk}/validade"
        for Valor in ("nao-e-data", "2026-02-30"):
            with self.subTest(Valor=Valor):
                Resposta = self.client.post(Rota, {"DataValidade": Valor}, follow=True)
                self.assertContains(Resposta, "Informe uma data de validade válida.")
                Lote.refresh_from_db()
                self.assertEqual(Lote.DataValidade, self.Validade)

    def test_ValidadeHistoricaPodeSerRegistradaSemEncerrarLoteAutomaticamente(self):
        Lote = self.Produto.LotesEstoque.get()
        DataAntiga = timezone.localdate() - timedelta(days=1)
        Resposta = self.client.post(
            f"/estoque/{self.Produto.pk}/lotes/{Lote.pk}/validade",
            {"DataValidade": DataAntiga.isoformat()},
        )
        self.assertRedirects(Resposta, f"/estoque/{self.Produto.pk}/editar")
        Lote.refresh_from_db()
        self.assertEqual(Lote.DataValidade, DataAntiga)
        self.assertTrue(Lote.EstaDisponivelParaVenda())

    def test_ValidadeExigePostLoginELoteDoProdutoCorreto(self):
        Lote = self.Produto.LotesEstoque.get()
        Rota = f"/estoque/{self.Produto.pk}/lotes/{Lote.pk}/validade"
        self.assertEqual(self.client.get(Rota).status_code, 405)
        OutroProduto = Produto.objects.create(
            Nome="Outro produto com validade", Categoria="Alimentos", Fornecedor=self.Fornecedor,
            PrecoCusto=Decimal("1.00"), PrecoVenda=Decimal("2.00"),
        )
        Resposta = self.client.post(
            f"/estoque/{OutroProduto.pk}/lotes/{Lote.pk}/validade",
            {"DataValidade": self.Validade.isoformat()},
        )
        self.assertEqual(Resposta.status_code, 404)
        Lote.refresh_from_db()
        self.assertIsNone(Lote.DataValidade)
        self.client.logout()
        self.assertEqual(self.client.post(Rota, {"DataValidade": self.Validade.isoformat()}).status_code, 302)

    def test_FormulariosETabelaMostramValidadeDoLote(self):
        Lote = self.Produto.LotesEstoque.get()
        Lote.DataValidade = self.Validade
        Lote.save(update_fields=["DataValidade"])
        Cadastro = self.client.get("/estoque/novo")
        Edicao = self.client.get(f"/estoque/{self.Produto.pk}/editar")
        self.assertContains(Cadastro, 'name="DataValidade"')
        self.assertContains(Edicao, 'name="Lote-DataValidade"')
        self.assertContains(Edicao, "<th>Data de validade</th>", html=True)
        self.assertContains(Edicao, f'value="{self.Validade.isoformat()}"')
        self.assertContains(Edicao, f'aria-label="Salvar validade do lote #{Lote.Numero}"')


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

    def test_BuscaProdutoIgnoraAcentos(self):
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

        Resposta = self.client.get("/estoque", {"busca": "feijao"})

        self.assertContains(Resposta, "Feijão Carioca")

    def test_CadastroColocaPrimeiraLetraDoProdutoEmMaiuscula(self):
        Resposta = self.client.post(
            "/estoque/novo",
            {
                "Nome": "caderno universitário",
                "Categoria": "Papelaria",
                "Marca": "Académie",
                "Fornecedor": self.Distribuidora.id,
                "UnidadeVenda": Produto.UNIDADE,
                "PrecoCusto": "12.00",
                "PrecoVenda": "18.00",
                "QuantidadeEstoque": "5",
                "EstoqueMinimo": "1",
            },
        )

        self.assertRedirects(Resposta, "/estoque")
        self.assertTrue(Produto.objects.filter(Nome="Caderno universitário").exists())

    def test_CadastroNovoAbreFormularioAutenticadoSemAlterarEstoque(self):
        Resposta = self.client.get("/estoque/novo")
        for Campo in ("Nome", "CodigoBarras", "Marca", "Categoria", "Fornecedor", "DataValidade", "PrecoCusto", "PrecoVenda", "UnidadeVenda", "QuantidadeEstoque", "EstoqueMinimo", "Disponivel"):
            with self.subTest(Campo=Campo):
                self.assertContains(Resposta, f'id="id_{Campo}"')
        self.assertContains(Resposta, 'class="PainelFormulario CadastroProdutoCompacto"')
        self.assertContains(Resposta, '"PrecoVenda Fornecedor EstoqueMinimo"')
        self.assertContains(Resposta, 'Formulario.addEventListener("keydown"')
        self.assertContains(Resposta, "ObterCamposVisiveis")
        self.assertContains(Resposta, "Campo.reportValidity()")
        self.assertEqual(Produto.objects.count(), 1)
        self.assertEqual(self.Arroz.LotesEstoque.count(), 1)

    def test_BuscaIncrementalSomenteInicioDoNomeIgnoraAcentosEMaiusculas(self):
        Produto.objects.create(Nome="Água mineral", Fornecedor=self.Distribuidora, PrecoVenda=Decimal("3.00"))
        Produto.objects.create(Nome="Pacote Água", Fornecedor=self.Distribuidora, PrecoVenda=Decimal("4.00"))
        Produto.objects.create(Nome="Outro produto", Marca="Água", Categoria="Água", Fornecedor=self.Distribuidora, PrecoVenda=Decimal("5.00"))
        Produto.objects.create(Nome="Água inativa", Ativo=False, Fornecedor=self.Distribuidora, PrecoVenda=Decimal("3.00"))

        Resposta = self.client.get("/estoque", {"busca": "  AGU  ", "inicio": "1"})
        self.assertContains(Resposta, "Água mineral")
        self.assertNotContains(Resposta, "Pacote Água")
        self.assertNotContains(Resposta, "Outro produto")
        self.assertNotContains(Resposta, "Água inativa")
        self.assertNotContains(Resposta, "Arroz Branco")
        self.assertEqual(Produto.objects.count(), 5)

    def test_BuscaIncrementalCombinaFiltrosEPesquisaCodigoSemBaixarEstoque(self):
        self.Arroz.CodigoBarras = "0012345678905"
        self.Arroz.save(update_fields=["CodigoBarras"])
        Filtros = {"inicio": "1", "categoria": "Mercearia", "fornecedor": self.Distribuidora.id, "estoque": "disponivel"}
        for Busca in ("arr", "00123"):
            with self.subTest(Busca=Busca):
                Resposta = self.client.get("/estoque", {**Filtros, "busca": Busca})
                self.assertContains(Resposta, "Arroz Branco")
                self.assertContains(Resposta, '<option value="disponivel" selected>')
        for Filtro, Valor in (("categoria", "Alimentos"), ("fornecedor", self.Hortifruti.id), ("estoque", "indisponivel")):
            with self.subTest(Filtro=Filtro):
                Vazio = self.client.get("/estoque", {**Filtros, Filtro: Valor, "busca": "arr"})
                self.assertContains(Vazio, "Nenhum produto encontrado")
                self.assertNotContains(Vazio, "Arroz Branco")
        self.Arroz.refresh_from_db()
        self.assertEqual(self.Arroz.QuantidadeEstoque, Decimal("12.000"))
        self.assertEqual(self.Arroz.LotesEstoque.count(), 1)

    def test_BuscaIncrementalLimpaPesquisaEPreservaInicioNoEnterDeTexto(self):
        Todos = self.client.get("/estoque", {"busca": "", "inicio": "1"})
        self.assertContains(Todos, "Arroz Branco")
        self.assertContains(Todos, 'id="ResultadosEstoque"')
        self.assertContains(Todos, 'name="inicio" value="1"')
        self.assertContains(Todos, 'Campo.addEventListener("input"')
        Filtros = {"busca": "Arroz", "categoria": "Mercearia", "fornecedor": str(self.Distribuidora.id), "estoque": "disponivel", "inicio": "1"}
        Resposta = self.client.get("/estoque/ler-codigo", {"codigo": "Arroz", "permitir_pesquisa": "1", **{Nome: Valor for Nome, Valor in Filtros.items() if Nome != "busca"}})
        self.assertRedirects(Resposta, f"/estoque?{urlencode(Filtros)}")

    def test_CadastroPreservaZerosDoCodigoEPermiteProdutosSemCodigo(self):
        Resposta = self.client.post("/estoque/novo", {
            "Nome": "Feijao com codigo", "CodigoBarras": "0012345678905",
            "Categoria": "Alimentos", "Fornecedor": self.Distribuidora.id,
            "UnidadeVenda": Produto.UNIDADE, "PrecoCusto": "4.00", "PrecoVenda": "7.00",
            "QuantidadeEstoque": "5", "EstoqueMinimo": "1",
        })
        self.assertRedirects(Resposta, "/estoque")
        self.assertEqual(Produto.objects.get(Nome="Feijao com codigo").CodigoBarras, "0012345678905")
        self.assertIsNone(self.Arroz.CodigoBarras)

    def test_CodigoDuplicadoERejeitadoNoFormularioENoBanco(self):
        self.Arroz.CodigoBarras = "0012345678905"
        self.Arroz.save(update_fields=["CodigoBarras"])
        Resposta = self.client.post("/estoque/novo", {
            "Nome": "Outro produto", "CodigoBarras": "0012345678905",
            "Categoria": "Alimentos", "Fornecedor": self.Distribuidora.id,
            "UnidadeVenda": Produto.UNIDADE, "PrecoCusto": "4.00", "PrecoVenda": "7.00",
            "QuantidadeEstoque": "5", "EstoqueMinimo": "1",
        })
        self.assertContains(Resposta, "Este código de barras já está cadastrado em outro produto.")
        self.assertFalse(Produto.objects.filter(Nome="Outro produto").exists())
        with self.assertRaises(IntegrityError), transaction.atomic():
            Produto.objects.create(
                Nome="Codigo repetido", CodigoBarras=self.Arroz.CodigoBarras,
                Fornecedor=self.Distribuidora, PrecoVenda=Decimal("1.00"),
            )

    def test_LeituraEstoqueAbreNovaEntradaSemAlterarSaldo(self):
        self.Arroz.CodigoBarras = "0012345678905"
        self.Arroz.save(update_fields=["CodigoBarras"])
        Resposta = self.client.get("/estoque/ler-codigo", {"codigo": "0012345678905"})
        self.assertRedirects(Resposta, f"/estoque/{self.Arroz.id}/editar?entrada=1#NovaEntradaEstoque")
        self.Arroz.refresh_from_db()
        self.assertEqual(self.Arroz.QuantidadeEstoque, Decimal("12.000"))
        self.assertEqual(self.Arroz.LotesEstoque.count(), 1)
        Busca = self.client.get("/estoque", {"busca": "0012345678905"})
        self.assertContains(Busca, "Arroz Branco")

    def test_EstoqueTemUmUnicoCampoParaPesquisaELeitor(self):
        Resposta = self.client.get("/estoque")
        self.assertContains(Resposta, 'name="busca"', count=1)
        self.assertContains(Resposta, 'id="BuscaProdutoEstoque"')
        self.assertContains(Resposta, "Produto ou código de barras")
        self.assertNotContains(Resposta, 'id="CodigoEntradaEstoque"')
        self.assertNotContains(Resposta, 'class="LeitorEstoque"')

    def test_BuscaUnificadaAbreCodigoExatoNumericoEAlfanumerico(self):
        for Codigo in ("0012345678905", "ABC-001"):
            with self.subTest(Codigo=Codigo):
                self.Arroz.CodigoBarras = Codigo
                self.Arroz.save(update_fields=["CodigoBarras"])
                Resposta = self.client.get("/estoque/ler-codigo", {
                    "codigo": Codigo, "permitir_pesquisa": "1",
                    "categoria": "Categoria diferente", "estoque": "indisponivel",
                })
                self.assertRedirects(
                    Resposta, f"/estoque/{self.Arroz.id}/editar?entrada=1#NovaEntradaEstoque"
                )
                self.Arroz.refresh_from_db()
                self.assertEqual(self.Arroz.QuantidadeEstoque, Decimal("12.000"))
                self.assertEqual(self.Arroz.LotesEstoque.count(), 1)

    def test_BuscaUnificadaPesquisaTextoEPreservaTodosOsFiltros(self):
        Filtros = {
            "busca": "Distribuidora Central", "categoria": "Mercearia",
            "fornecedor": str(self.Distribuidora.id), "estoque": "disponivel",
        }
        Resposta = self.client.get("/estoque/ler-codigo", {
            "codigo": "  Distribuidora Central  ", "permitir_pesquisa": "1",
            **{Chave: Valor for Chave, Valor in Filtros.items() if Chave != "busca"},
        })
        self.assertRedirects(Resposta, f"/estoque?{urlencode(Filtros)}")
        Pagina = self.client.get(Resposta.url)
        self.assertContains(Pagina, "Arroz Branco")
        self.assertContains(Pagina, 'value="Distribuidora Central"')
        self.assertContains(Pagina, '<option value="disponivel" selected>')

    def test_BuscaUnificadaTrataCodigoParcialDesconhecidoETextoLongoComoPesquisa(self):
        self.Arroz.CodigoBarras = "0012345678905"
        self.Arroz.save(update_fields=["CodigoBarras"])

        for Busca in ("001234", "0009876543210", "Produto " * 12, ""):
            with self.subTest(Busca=Busca):
                Resposta = self.client.get("/estoque/ler-codigo", {
                    "codigo": Busca, "permitir_pesquisa": "1",
                })
                self.assertRedirects(Resposta, f"/estoque?{urlencode({'busca': Busca.strip()})}")
                self.assertEqual(Produto.objects.count(), 1)

    def test_BuscaUnificadaNaoAbreProdutoInativo(self):
        self.Arroz.CodigoBarras = "0012345678905"
        self.Arroz.Ativo = False
        self.Arroz.save(update_fields=["CodigoBarras", "Ativo"])
        Resposta = self.client.get("/estoque/ler-codigo", {
            "codigo": self.Arroz.CodigoBarras, "permitir_pesquisa": "1",
        }, follow=True)
        self.assertContains(Resposta, "Este código pertence a um produto inativo.")
        self.assertEqual(Produto.objects.count(), 1)

    def test_BuscaUnificadaRejeitaCaractereNuloSemErroNoBanco(self):
        Resposta = self.client.get("/estoque/ler-codigo", {
            "codigo": "ABC\x00DEF", "permitir_pesquisa": "1",
        }, follow=True)
        self.assertContains(Resposta, "Informe um código de barras válido com até 64 caracteres.")

    def test_LeituraCodigoNovoPreencheCadastroSemCriarProduto(self):
        Resposta = self.client.get("/estoque/ler-codigo", {"codigo": "0009876543210"}, follow=True)
        self.assertContains(Resposta, 'name="CodigoBarras" value="0009876543210"')
        self.assertEqual(Produto.objects.count(), 1)

    def test_EdicaoPermiteVincularELimparCodigo(self):
        Dados = {"Nome": self.Arroz.Nome, "Categoria": "Alimentos", "EstoqueMinimo": "3", "CodigoBarras": "0012345678905"}
        self.client.post(f"/estoque/{self.Arroz.id}/editar", Dados)
        self.Arroz.refresh_from_db()
        self.assertEqual(self.Arroz.CodigoBarras, "0012345678905")
        Dados["CodigoBarras"] = ""
        self.client.post(f"/estoque/{self.Arroz.id}/editar", Dados)
        self.Arroz.refresh_from_db()
        self.assertIsNone(self.Arroz.CodigoBarras)

    def test_CodigoDeProdutoInativoNaoAbreCadastroDuplicado(self):
        self.Arroz.CodigoBarras = "0012345678905"
        self.Arroz.Ativo = False
        self.Arroz.save(update_fields=["CodigoBarras", "Ativo"])
        Resposta = self.client.get("/estoque/ler-codigo", {"codigo": self.Arroz.CodigoBarras}, follow=True)
        self.assertContains(Resposta, "Este código pertence a um produto inativo.")
        self.assertEqual(Produto.objects.count(), 1)

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

        Produto.objects.create(
            Nome="Feijão Preto",
            Categoria="Mercearia",
            Marca="Sabor da Terra",
            Fornecedor=self.Distribuidora,
            UnidadeVenda=Produto.UNIDADE,
            QuantidadeEstoque=Decimal("4.000"),
            EstoqueMinimo=Decimal("1.000"),
            PrecoCusto=Decimal("4.00"),
            PrecoVenda=Decimal("7.00"),
        )

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

        NovoLote = self.Arroz.LotesEstoque.exclude(pk=LoteAnterior.pk).get()
        self.assertEqual(NovoLote.QuantidadeDisponivel, Decimal("6.000"))
        self.assertEqual(NovoLote.PrecoCusto, Decimal("5.75"))
        self.assertEqual(NovoLote.PrecoVenda, Decimal("9.25"))
        self.assertGreater(NovoLote.id, 2)
        self.assertEqual(LoteAnterior.ObterNumeroNoProduto(), 1)
        self.assertEqual(NovoLote.ObterNumeroNoProduto(), 2)
        self.Arroz.refresh_from_db()
        self.assertEqual(self.Arroz.QuantidadeEstoque, Decimal("18.000"))
        PaginaEdicao = self.client.get(Resposta.url)
        self.assertContains(PaginaEdicao, "Entradas de estoque")
        self.assertContains(PaginaEdicao, "<strong>#2</strong>", html=True)

    def test_ExclusaoLogicaPreservaProdutoEEscondeDaLista(self):
        Resposta = self.client.post(f"/estoque/{self.Arroz.id}/excluir")

        self.assertRedirects(Resposta, "/estoque")
        self.Arroz.refresh_from_db()
        self.assertFalse(self.Arroz.Ativo)
        self.assertFalse(self.Arroz.Disponivel)
        self.assertNotContains(self.client.get("/estoque"), "Arroz Branco")

    def test_CorrigeDataDeEntradaDoLote(self):
        Lote = self.Arroz.LotesEstoque.get()

        Resposta = self.client.post(
            f"/estoque/{self.Arroz.id}/lotes/{Lote.id}/data",
            {"DataEntrada": "2026-09-28"},
        )

        self.assertRedirects(Resposta, f"/estoque/{self.Arroz.id}/editar")
        Lote.refresh_from_db()
        self.assertEqual(timezone.localtime(Lote.CriadoEm).date().isoformat(), "2026-09-28")
        self.assertContains(self.client.get(Resposta.url), 'value="2026-09-28"')

    def test_ExcluiLoteSemVendaSemRenumerarLotesPosteriores(self):
        LoteDois = LoteEstoque.objects.create(
            Produto=self.Arroz,
            Fornecedor=self.Distribuidora,
            QuantidadeInicial=Decimal("2.000"),
            QuantidadeDisponivel=Decimal("2.000"),
            PrecoCusto=Decimal("5.50"),
            PrecoVenda=Decimal("9.00"),
        )
        LoteTres = LoteEstoque.objects.create(
            Produto=self.Arroz,
            Fornecedor=self.Distribuidora,
            QuantidadeInicial=Decimal("3.000"),
            QuantidadeDisponivel=Decimal("3.000"),
            PrecoCusto=Decimal("6.00"),
            PrecoVenda=Decimal("10.00"),
        )
        self.Arroz.SincronizarResumoLotes()

        Resposta = self.client.post(
            f"/estoque/{self.Arroz.id}/lotes/{LoteDois.id}/excluir",
            follow=True,
        )

        self.assertFalse(LoteEstoque.objects.filter(pk=LoteDois.pk).exists())
        LoteTres.refresh_from_db()
        self.Arroz.refresh_from_db()
        self.assertEqual(LoteTres.Numero, 3)
        self.assertEqual(self.Arroz.QuantidadeEstoque, Decimal("15.000"))
        self.assertContains(Resposta, "Lote #2 excluído")
        self.assertContains(Resposta, "<strong>#3</strong>", html=True)

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
