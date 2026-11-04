"""Prontidão sem autenticação e sem exposição de erros do banco."""
from unittest.mock import patch

from django.db import OperationalError
from django.test import SimpleTestCase


class TesteSaude(SimpleTestCase):
    @patch("configuracao.ComponenteSaude.connection")
    def test_SaudeConsultaBancoSemExigirLogin(self, Conexao):
        Resposta = self.client.get("/health")

        self.assertEqual(Resposta.status_code, 200)
        self.assertEqual(Resposta.json(), {"status": "ok"})
        self.assertEqual(Resposta["Cache-Control"], "no-store")
        Conexao.cursor.return_value.__enter__.return_value.execute.assert_called_once_with("SELECT 1")

    @patch("configuracao.ComponenteSaude.connection")
    def test_FalhaBancoRetorna503SemRevelarCredenciais(self, Conexao):
        Conexao.cursor.side_effect = OperationalError("senha ou host confidencial")

        Resposta = self.client.get("/health")

        self.assertEqual(Resposta.status_code, 503)
        self.assertEqual(Resposta.json(), {"status": "indisponivel"})
        self.assertNotContains(Resposta, "confidencial", status_code=503)

    def test_SaudeNaoAceitaPost(self):
        self.assertEqual(self.client.post("/health").status_code, 405)
