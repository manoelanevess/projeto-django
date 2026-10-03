"""Testes do cadastro e da manutenção de fornecedores."""
from django.contrib.auth import get_user_model as ObterModeloUsuario
from django.test import TestCase

from .models import Fornecedor


class TesteManutencaoFornecedores(TestCase):
    def setUp(self):
        self.Usuario = ObterModeloUsuario().objects.create_user(
            username="proprietario_fornecedores",
            password="SenhaTeste123!",
        )
        self.client.force_login(self.Usuario)

    def test_CadastraFornecedor(self):
        Resposta = self.client.post(
            "/fornecedores/novo",
            {
                "Nome": "Distribuidora Alemão",
                "Telefone": "(51) 99999-0000",
                "Email": "VENDAS@ALEMAO.TEST",
                "Cidade": "Porto Alegre",
            },
        )

        self.assertRedirects(Resposta, "/fornecedores")
        FornecedorCriado = Fornecedor.objects.get(Nome="Distribuidora Alemão")
        self.assertEqual(FornecedorCriado.Email, "vendas@alemao.test")
        self.assertTrue(FornecedorCriado.Ativo)

    def test_ListaPermitePesquisarEEditarFornecedor(self):
        FornecedorCriado = Fornecedor.objects.create(
            Nome="Papelaria Central",
            Cidade="Canoas",
        )

        RespostaBusca = self.client.get("/fornecedores", {"busca": "Canoas"})
        self.assertContains(RespostaBusca, "Papelaria Central")
        self.assertContains(RespostaBusca, "+ Adicionar fornecedor")

        RespostaEdicao = self.client.post(
            f"/fornecedores/{FornecedorCriado.id}/editar",
            {
                "Nome": "Papelaria Central RS",
                "Telefone": "",
                "Email": "",
                "Cidade": "Canoas",
            },
        )

        self.assertRedirects(RespostaEdicao, "/fornecedores")
        FornecedorCriado.refresh_from_db()
        self.assertEqual(FornecedorCriado.Nome, "Papelaria Central RS")

    def test_InativaFornecedorSemApagarCadastro(self):
        FornecedorCriado = Fornecedor.objects.create(Nome="Fornecedor Antigo")

        Resposta = self.client.post(
            f"/fornecedores/{FornecedorCriado.id}/excluir"
        )

        self.assertRedirects(Resposta, "/fornecedores")
        FornecedorCriado.refresh_from_db()
        self.assertFalse(FornecedorCriado.Ativo)
        self.assertNotContains(self.client.get("/fornecedores"), "Fornecedor Antigo")
