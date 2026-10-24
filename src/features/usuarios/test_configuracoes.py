"""Persistência do comércio, upload da foto e isolamento entre usuários."""
from struct import pack as Empacotar
from zlib import compress as Comprimir, crc32 as CalcularCrc

from django.contrib.auth import get_user_model as ObterModeloUsuario
from django.core.files.uploadedfile import SimpleUploadedFile as ArquivoEnviado
from django.test import Client, TestCase

from features.fornecedor.models import Fornecedor
from features.produtos.models import Produto

from .FormularioConfiguracao import LimiteFotoPerfil
from .models import ConfiguracaoComercio, PerfilUsuario


def CriarPngTeste(Cor=(7, 132, 202)):
    def Bloco(Tipo, Conteudo):
        return Empacotar(">I", len(Conteudo)) + Tipo + Conteudo + Empacotar(">I", CalcularCrc(Tipo + Conteudo))
    return (b"\x89PNG\r\n\x1a\n" + Bloco(b"IHDR", Empacotar(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
            + Bloco(b"IDAT", Comprimir(b"\x00" + bytes(Cor))) + Bloco(b"IEND", b""))


class TesteConfiguracoes(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.Usuario = ObterModeloUsuario().objects.create_user(username="dono_configuracoes")
        cls.OutroUsuario = ObterModeloUsuario().objects.create_user(username="outro_configuracoes")
        cls.Fornecedor = Fornecedor.objects.create(Nome="Distribuidora Configurações")
        cls.Produto = Produto.objects.create(Nome="Produto Configurações", Categoria="Alimentos",
                                            Fornecedor=cls.Fornecedor, PrecoVenda="5")

    def setUp(self):
        self.client.force_login(self.Usuario)

    def SalvarFoto(self, Cor=(7, 132, 202), NomeComercio="mercado da família"):
        return self.client.post("/configuracoes", {
            "NomeComercio": NomeComercio,
            "FotoPerfil": ArquivoEnviado("foto.png", CriarPngTeste(Cor), content_type="image/png"),
        })

    def test_ProprietarioAbreConfiguracoesELeituraNaoCriaRegistros(self):
        self.assertContains(self.client.get("/"), 'class="AcessoProprietario" href="/configuracoes"')
        Resposta = self.client.get("/configuracoes")
        self.assertContains(Resposta, 'name="NomeComercio" value="Controle de Estoque"')
        self.assertContains(Resposta, 'enctype="multipart/form-data"')
        self.assertContains(Resposta, 'name="FotoPerfil"')
        self.assertFalse(ConfiguracaoComercio.objects.exists())
        self.assertFalse(PerfilUsuario.objects.exists())

    def test_NomePersisteEPersonalizaTodasAsPaginasInclusiveLoginE404(self):
        self.assertRedirects(self.client.post("/configuracoes", {"NomeComercio": "  mercado   da família  "}), "/configuracoes")
        self.assertEqual(ConfiguracaoComercio.objects.get().NomeComercio, "Mercado Da Família")
        Rotas = ("/", "/estoque", "/estoque/novo", "/estoque/categorias/nova", "/dashboard", "/fornecedores",
                 "/fornecedores/novo", f"/fornecedores/{self.Fornecedor.pk}/editar",
                 f"/estoque/{self.Produto.pk}/editar", "/carrinho", "/continhas", "/vendas/historico", "/configuracoes")
        for Rota in Rotas:
            with self.subTest(Rota=Rota):
                Resposta = self.client.get(Rota)
                self.assertContains(Resposta, '<div class="MarcaTopo">Mercado Da Família</div>')
                self.assertContains(Resposta, "· Mercado Da Família</title>")
        self.assertContains(self.client.get("/pagina-ausente"), "Mercado Da Família", status_code=404)
        self.client.logout()
        self.assertContains(self.client.get("/login"), "<h1>Mercado Da Família</h1>")

    def test_FotoEnviadaApareceNoTopoEPodeSerLidaSomentePeloUsuario(self):
        self.assertRedirects(self.SalvarFoto(), "/configuracoes")
        Perfil = PerfilUsuario.objects.get(Usuario=self.Usuario)
        self.assertEqual(bytes(Perfil.FotoConteudo), CriarPngTeste())
        self.assertContains(self.client.get("/estoque"), f'/configuracoes/foto-perfil?v={Perfil.FotoVersao}')
        Resposta = self.client.get("/configuracoes/foto-perfil")
        self.assertEqual(Resposta.content, CriarPngTeste())
        self.assertEqual(Resposta["Content-Type"], "image/png")
        self.assertEqual(Resposta["Cache-Control"], "private, no-store")
        self.assertEqual(Resposta["X-Content-Type-Options"], "nosniff")
        self.client.force_login(self.OutroUsuario)
        self.assertEqual(self.client.get("/configuracoes/foto-perfil").status_code, 404)
        self.assertNotContains(self.client.get("/configuracoes"), f'?v={Perfil.FotoVersao}')
        self.assertContains(self.client.get("/configuracoes"), "Mercado Da Família")

    def test_TrocarFotoAtualizaVersaoESalvarSomenteNomePreservaFoto(self):
        self.SalvarFoto()
        VersaoAnterior = PerfilUsuario.objects.get().FotoVersao
        self.assertRedirects(self.SalvarFoto(Cor=(220, 45, 30)), "/configuracoes")
        Perfil = PerfilUsuario.objects.get()
        self.assertNotEqual(Perfil.FotoVersao, VersaoAnterior)
        self.assertEqual(bytes(Perfil.FotoConteudo), CriarPngTeste((220, 45, 30)))
        self.assertRedirects(self.client.post("/configuracoes", {"NomeComercio": "mercearia nova"}), "/configuracoes")
        Perfil.refresh_from_db()
        self.assertEqual(bytes(Perfil.FotoConteudo), CriarPngTeste((220, 45, 30)))
        self.assertEqual(ConfiguracaoComercio.objects.get().NomeComercio, "Mercearia Nova")

    def test_ArquivosIncorretosOuMuitoGrandesNaoAlteramNomeNemFoto(self):
        self.SalvarFoto()
        for Nome, Conteudo in (("foto.png", b"<html><script>alert(1)</script></html>"),
                               ("foto.svg", b'<svg xmlns="http://www.w3.org/2000/svg"></svg>'),
                               ("foto.png", CriarPngTeste() + b"x" * LimiteFotoPerfil)):
            with self.subTest(Nome=Nome, Tamanho=len(Conteudo)):
                Resposta = self.client.post("/configuracoes", {
                    "NomeComercio": "Nome Incorreto", "FotoPerfil": ArquivoEnviado(Nome, Conteudo, content_type="image/png"),
                })
                self.assertContains(Resposta, 'role="alert"')
                self.assertEqual(ConfiguracaoComercio.objects.get().NomeComercio, "Mercado Da Família")
                self.assertEqual(bytes(PerfilUsuario.objects.get().FotoConteudo), CriarPngTeste())

    def test_NomeInvalidoNaoGravaFotoENemCriaConfiguracao(self):
        for Nome in ("   ", "x" * 121):
            with self.subTest(Nome=Nome):
                self.assertContains(self.SalvarFoto(NomeComercio=Nome), 'role="alert"')
        self.assertFalse(ConfiguracaoComercio.objects.exists())
        self.assertFalse(PerfilUsuario.objects.exists())

    def test_NomeComHtmlEEscapadoNoCabecalhoETitulo(self):
        self.client.post("/configuracoes", {"NomeComercio": "mercado <script>alert(1)</script>"})
        Resposta = self.client.get("/configuracoes")
        self.assertContains(Resposta, "Mercado &lt;Script&gt;Alert(1)&lt;/Script&gt;")
        self.assertNotContains(Resposta, "<Script>Alert(1)</Script>")

    def test_RotasExigemLoginECsrfEMetodosCorretos(self):
        for Rota in ("/configuracoes", "/configuracoes/foto-perfil"):
            self.assertEqual(Client().get(Rota).status_code, 302)
        Cliente = Client(enforce_csrf_checks=True)
        Cliente.force_login(self.Usuario)
        self.assertEqual(Cliente.post("/configuracoes", {"NomeComercio": "Teste"}).status_code, 403)
        self.assertEqual(self.client.delete("/configuracoes").status_code, 405)
        self.assertEqual(self.client.post("/configuracoes/foto-perfil").status_code, 405)
        self.assertEqual(self.client.get("/configuracoes/foto-perfil").status_code, 404)
