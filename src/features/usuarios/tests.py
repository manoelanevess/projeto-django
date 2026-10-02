"""Testes do fluxo de autenticação do proprietário."""
from django.contrib.auth import get_user_model as ObterModeloUsuario
from django.test import Client, TestCase


class TesteAutenticacao(TestCase):
    def setUp(self):
        self.NomeUsuario = "proprietario_teste"
        self.Senha = "SenhaTeste123!"
        self.Usuario = ObterModeloUsuario().objects.create_user(
            username=self.NomeUsuario,
            password=self.Senha,
        )
        self.Cliente = Client(enforce_csrf_checks=True)

    def ObterTokenCsrf(self):
        Resposta = self.Cliente.get("/login")

        self.assertEqual(Resposta.status_code, 200)
        return Resposta.cookies["csrftoken"].value

    def test_RotasProtegidasRedirecionamParaLogin(self):
        for Rota in ["/", "/produtos", "/estoque", "/dashboard", "/fornecedores"]:
            with self.subTest(Rota=Rota):
                Resposta = self.Cliente.get(Rota)

                self.assertEqual(Resposta.status_code, 302)
                self.assertEqual(Resposta.url, f"/login?next={Rota}")

    def test_LoginInvalidoExibeMensagem(self):
        TokenCsrf = self.ObterTokenCsrf()
        Resposta = self.Cliente.post(
            "/login",
            {
                "usuario": self.NomeUsuario,
                "senha": "senha-incorreta",
                "csrfmiddlewaretoken": TokenCsrf,
            },
        )

        self.assertEqual(Resposta.status_code, 200)
        self.assertContains(Resposta, "Usuário ou senha inválidos")

    def test_LoginValidoLiberaAcessoEAoSairBloqueiaNovamente(self):
        TokenCsrf = self.ObterTokenCsrf()
        RespostaLogin = self.Cliente.post(
            "/login",
            {
                "usuario": self.NomeUsuario,
                "senha": self.Senha,
                "csrfmiddlewaretoken": TokenCsrf,
            },
        )

        self.assertRedirects(
            RespostaLogin,
            "/",
            fetch_redirect_response=False,
        )
        self.assertEqual(self.Cliente.get("/").status_code, 200)

        RespostaLogout = self.Cliente.get("/logout")

        self.assertRedirects(
            RespostaLogout,
            "/login",
            fetch_redirect_response=False,
        )
        self.assertEqual(self.Cliente.get("/").status_code, 302)
