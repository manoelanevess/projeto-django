"""Aplica as migrações antes de iniciar o servidor do contêiner."""
import os
import subprocess
import sys


def Iniciar():
    for NomeVariavel in ("DJANGO_SECRET_KEY", "POSTGRES_PASSWORD"):
        if not os.environ.get(NomeVariavel, "").strip():
            raise SystemExit(f"Preencha {NomeVariavel} em .env.docker antes de iniciar.")

    if len(sys.argv) < 2:
        raise SystemExit("Informe o comando do servidor.")

    if os.environ.get("APLICAR_MIGRACOES", "1") == "1":
        subprocess.run(
            [sys.executable, "manage.py", "migrate", "--noinput"],
            check=True,
        )

    os.execvp(sys.argv[1], sys.argv[1:])


if __name__ == "__main__":
    Iniciar()
