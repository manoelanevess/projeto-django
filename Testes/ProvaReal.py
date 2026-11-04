"""Demonstra verde/vermelho/verde em cópia descartável, sem alterar o host."""
import hashlib
from pathlib import Path
import subprocess
import sys


def Executar():
    if not Path("/.dockerenv").exists():
        raise SystemExit("Execute somente no contêiner descartável de testes.")

    Caminho = Path("/app/src/features/vendas/LogicaCarrinho.py")
    Original = Caminho.read_bytes()
    HashOriginal = hashlib.sha256(Original).hexdigest()
    Trecho = b"if ValorRecebido < TotalDinheiro:"
    if Original.count(Trecho) != 1:
        raise SystemExit("A validação mudou; revise a prova real antes de executá-la.")

    Comando = [sys.executable, "manage.py", "test", "--noinput",
               "features.vendas.test_pagamento_misto.TestePagamentoMisto.test_DinheiroInsuficienteMantemCarrinhoEEstoque"]
    Pasta = Path("/relatorios")
    Pasta.mkdir(parents=True, exist_ok=True)

    def Rodar(Nome):
        Resultado = subprocess.run(Comando, capture_output=True, text=True)
        (Pasta / f"ProvaReal-{Nome}.log").write_text(
            Resultado.stdout + Resultado.stderr, encoding="utf-8"
        )
        print(f"{Nome}: codigo de saida {Resultado.returncode}", flush=True)
        return Resultado

    if Rodar("Antes").returncode != 0:
        raise SystemExit("O teste original falhou; não foi aplicada mutação.")
    try:
        Caminho.write_bytes(Original.replace(Trecho, b"if False:  # Mutacao temporaria da prova real"))
        ResultadoMutado = Rodar("Mutacao")
    finally:
        Caminho.write_bytes(Original)

    if hashlib.sha256(Caminho.read_bytes()).hexdigest() != HashOriginal:
        raise SystemExit("A restauração do arquivo falhou.")
    if ResultadoMutado.returncode != 1 or "AssertionError" not in ResultadoMutado.stderr:
        raise SystemExit("A mutação não produziu a falha de asserção esperada. Confira o relatório.")
    if Rodar("Restaurado").returncode != 0:
        raise SystemExit("O teste não voltou a passar após restaurar o código.")
    print("Prova real aprovada: verde, vermelho, verde; codigo restaurado com hash identico.")


if __name__ == "__main__":
    Executar()
