"""Compressão HTTP precisa preservar login, CSRF e conteúdo das páginas."""
import gzip

from django.contrib.auth import get_user_model as ObterModeloUsuario
from django.test import Client, TestCase


class TesteCompressaoHttp(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.Usuario = ObterModeloUsuario().objects.create_user(
            username="teste_compressao", password="SenhaTeste123!"
        )

    def test_LoginComprimidoPreservaCsrfESessao(self):
        Cliente = Client(enforce_csrf_checks=True)
        Resposta = Cliente.get("/login", HTTP_ACCEPT_ENCODING="gzip")
        self.assertEqual(Resposta.status_code, 200)
        self.assertEqual(Resposta["Content-Encoding"], "gzip")
        Html = gzip.decompress(Resposta.content).decode("utf-8")
        self.assertIn('name="csrfmiddlewaretoken"', Html)
        self.assertIn("Acesso do proprietário", Html)
        self.assertLess(len(Resposta.content), len(Html.encode("utf-8")))
        self.assertIn("Accept-Encoding", Resposta["Vary"])
        self.assertIn("Cookie", Resposta["Vary"])

        Login = Cliente.post("/login", {
            "usuario": "teste_compressao", "senha": "SenhaTeste123!",
            "csrfmiddlewaretoken": Resposta.cookies["csrftoken"].value,
        })
        self.assertEqual(Login.status_code, 302)
        self.assertEqual(Login.url, "/")
        Pagina = Cliente.get("/", HTTP_ACCEPT_ENCODING="gzip")
        self.assertEqual(Pagina.status_code, 200)
        self.assertEqual(Pagina["Content-Encoding"], "gzip")
        self.assertIn("Carrinho", gzip.decompress(Pagina.content).decode("utf-8"))

    def test_NaoComprimeQuandoClienteNaoAceitaGzip(self):
        Resposta = self.client.get("/login", HTTP_ACCEPT_ENCODING="identity")
        self.assertNotIn("Content-Encoding", Resposta)
        self.assertContains(Resposta, "Acesso do proprietário")
