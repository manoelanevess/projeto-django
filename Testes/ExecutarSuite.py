"""Executa Django e denuncia qualquer tentativa de rede Python nos testes."""
import json
from pathlib import Path
import runpy
import socket
from unittest.mock import patch


Tentativas = []


def BloquearConexaoPython(Socket, Endereco):
    Tentativas.append(str(Endereco))
    raise AssertionError("Um teste tentou abrir uma conexão de rede Python real.")


# PostgreSQL usa libpq nativa; nenhum teste HTTP pode chamar serviços externos.
try:
    with patch.object(socket.socket, "connect", BloquearConexaoPython), \
            patch.object(socket.socket, "connect_ex", BloquearConexaoPython):
        runpy.run_path("manage.py", run_name="__main__")
finally:
    Path("/relatorios/Rede.json").write_text(
        json.dumps({"tentativas_rede_python": Tentativas}, indent=2), encoding="utf-8"
    )

if Tentativas:
    raise SystemExit("Foram detectadas tentativas de conexão real. Confira Rede.json.")
