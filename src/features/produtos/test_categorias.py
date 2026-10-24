"""Categorias persistem sem produtos e só opções cadastradas podem ser escolhidas."""
from decimal import Decimal
from importlib import import_module as ImportarModulo
from urllib.parse import parse_qs as LerParametros, urlsplit as SepararUrl

from django.apps import apps as Apps
from django.contrib.auth import get_user_model as ObterModeloUsuario
from django.db import connection as Conexao
from django.test import Client, TestCase

from features.fornecedor.models import Fornecedor

from .ApiProduto import BuscarCategoriasProdutos
from .FormularioProduto import FormularioEdicaoProduto, FormularioProduto
from .models import CategoriaProduto, Produto


class TesteCategoriasProduto(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.Usuario = ObterModeloUsuario().objects.create_user(username="categorias_produtos")
        cls.Fornecedor = Fornecedor.objects.create(Nome="Distribuidora Central")
        cls.Produto = Produto.objects.create(
            Nome="Arroz Branco", Categoria="Alimentos", Fornecedor=cls.Fornecedor,
            QuantidadeEstoque=Decimal("10"), EstoqueMinimo=Decimal("1"), PrecoVenda=Decimal("7"),
        )

    def setUp(self):
        self.client.force_login(self.Usuario)

    def DadosProduto(self, **Dados):
        return {
            "Nome": "Suco De Uva", "Categoria": "Bebidas Sem Álcool", "Fornecedor": self.Fornecedor.pk,
            "UnidadeVenda": Produto.UNIDADE, "PrecoCusto": "2", "PrecoVenda": "5",
            "QuantidadeEstoque": "10", "EstoqueMinimo": "1", **Dados,
        }

    def test_MaisNoFiltroAbreCadastroComAlternativaSemJavascript(self):
        Resposta = self.client.get("/estoque", {"busca": "arroz", "categoria": "Alimentos"})
        self.assertContains(Resposta, 'aria-label="Adicionar categoria"')
        self.assertContains(Resposta, 'href="/estoque/categorias/nova?busca=arroz&amp;categoria=Alimentos"')
        self.assertContains(Resposta, '<dialog class="DialogoNovaCategoria"')
        self.assertContains(self.client.get("/estoque/categorias/nova"), 'name="Nome"')

    def test_CategoriaNovaPersisteSemProdutoEVoltaAosFiltros(self):
        Filtros = {"busca": "arroz", "inicio": "1", "categoria": "Alimentos",
                   "fornecedor": str(self.Fornecedor.pk), "estoque": "disponivel"}
        Resposta = self.client.post("/estoque/categorias/nova", {
            "Nome": "  bebidas   sem álcool ", **{f"retorno_{Campo}": Valor for Campo, Valor in Filtros.items()},
        })
        self.assertEqual(Resposta.status_code, 302)
        self.assertEqual(LerParametros(SepararUrl(Resposta.url).query), {Campo: [Valor] for Campo, Valor in Filtros.items()})
        self.assertTrue(CategoriaProduto.objects.filter(Nome="Bebidas Sem Álcool").exists())
        self.assertIn("Bebidas Sem Álcool", BuscarCategoriasProdutos())
        self.assertEqual(Produto.objects.count(), 1)
        self.Produto.refresh_from_db()
        self.assertEqual(self.Produto.QuantidadeEstoque, Decimal("10"))
        self.assertContains(self.client.get("/estoque"), '<option value="Bebidas Sem Álcool">')

    def test_NaoAceitaCategoriaVaziaLongaOuDuplicada(self):
        CategoriaProduto.objects.create(Nome="Bebidas Sem Álcool")
        for Nome in ("  ", "x" * 81, "BEBIDAS SEM ÁLCOOL", "alimentos"):
            with self.subTest(Nome=Nome):
                self.assertContains(self.client.post("/estoque/categorias/nova", {"Nome": Nome}), 'role="alert"')
        self.assertEqual(CategoriaProduto.objects.count(), 1)

    def test_CadastroEEdicaoUsamListaOrdenadaComCategoriasExistentes(self):
        CategoriaProduto.objects.create(Nome="Bebidas Sem Álcool")
        CategoriaProduto.objects.create(Nome="Alimentos")
        for Formulario in (FormularioProduto(), FormularioEdicaoProduto(instance=self.Produto)):
            with self.subTest(Formulario=type(Formulario).__name__):
                self.assertEqual(Formulario.fields["Categoria"].widget.input_type, "select")
                self.assertEqual(list(Formulario.fields["Categoria"].choices), [
                    ("", "Selecione uma categoria"), ("Alimentos", "Alimentos"), ("Bebidas Sem Álcool", "Bebidas Sem Álcool"),
                ])
        self.assertContains(self.client.get(f"/estoque/{self.Produto.pk}/editar"), '<option value="Alimentos" selected>')

    def test_EscolhaCadastradaSalvaNoProdutoEFiltraEstoque(self):
        CategoriaProduto.objects.create(Nome="Bebidas Sem Álcool")
        Resposta = self.client.post("/estoque/novo", self.DadosProduto(Categoria="bebidas sem álcool"))
        self.assertRedirects(Resposta, "/estoque")
        ProdutoSalvo = Produto.objects.get(Nome="Suco De Uva")
        self.assertEqual(ProdutoSalvo.Categoria, "Bebidas Sem Álcool")
        Filtrado = self.client.get("/estoque", {"categoria": ProdutoSalvo.Categoria})
        self.assertContains(Filtrado, "Suco De Uva")
        self.assertNotContains(Filtrado, "Arroz Branco")
        self.assertRedirects(self.client.post(f"/estoque/{self.Produto.pk}/editar", {
            "Nome": self.Produto.Nome, "Categoria": ProdutoSalvo.Categoria, "EstoqueMinimo": "1",
        }), f"/estoque/{self.Produto.pk}/editar")
        self.Produto.refresh_from_db()
        self.assertEqual(self.Produto.Categoria, ProdutoSalvo.Categoria)

    def test_PostNaoPermiteInventarCategoriaNoCadastroOuEdicao(self):
        self.assertContains(self.client.post("/estoque/novo", self.DadosProduto()), "Selecione uma categoria cadastrada.")
        self.assertContains(self.client.post(f"/estoque/{self.Produto.pk}/editar", {
            "Nome": self.Produto.Nome, "Categoria": "Categoria Inexistente", "EstoqueMinimo": "1",
        }), "Selecione uma categoria cadastrada.")
        self.Produto.refresh_from_db()
        self.assertEqual(self.Produto.Categoria, "Alimentos")
        self.assertEqual(Produto.objects.count(), 1)

    def test_ErroEmOutroCampoMantemCategoriaSelecionada(self):
        CategoriaProduto.objects.create(Nome="Bebidas Sem Álcool")
        Resposta = self.client.post("/estoque/novo", self.DadosProduto(Nome="", Categoria="bebidas sem álcool"))
        self.assertContains(Resposta, '<option value="Bebidas Sem Álcool" selected>')
        self.assertEqual(Produto.objects.count(), 1)

    def test_MigracaoImportaCategoriasAntigasInclusiveDeProdutosInativosSemDuplicar(self):
        Produto.objects.filter(pk=self.Produto.pk).update(Categoria="  alimentos  secos ", Ativo=False)
        Produto.objects.create(Nome="Feijão", Categoria="Alimentos Secos", Fornecedor=self.Fornecedor, PrecoVenda=Decimal("5"))
        Migracao = ImportarModulo("features.produtos.migrations.0010_categoriaproduto")
        with Conexao.schema_editor() as Editor:
            Migracao.ImportarCategoriasExistentes(Apps, Editor)
            Migracao.ImportarCategoriasExistentes(Apps, Editor)
        self.assertEqual(list(CategoriaProduto.objects.values_list("Nome", flat=True)), ["Alimentos Secos"])

    def test_CadastroExigeLoginECsrfENaoAceitaOutrosMetodos(self):
        self.assertEqual(Client().post("/estoque/categorias/nova", {"Nome": "Teste"}).status_code, 302)
        Cliente = Client(enforce_csrf_checks=True)
        Cliente.force_login(self.Usuario)
        self.assertEqual(Cliente.post("/estoque/categorias/nova", {"Nome": "Teste"}).status_code, 403)
        self.assertEqual(self.client.delete("/estoque/categorias/nova").status_code, 405)
        self.assertFalse(CategoriaProduto.objects.exists())
