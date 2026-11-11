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

    if os.environ.get("DJANGO_CRIAR_SUPERUSUARIO_AUTOMATICO", "0") == "1":
        CriarSuperusuario()

    if os.environ.get("DJANGO_CARREGAR_DADOS_DEMO", "0") == "1":
        subprocess.run(
            [sys.executable, "manage.py", "carregar_dados_demo"],
            check=True,
        )

    os.execvp(sys.argv[1], sys.argv[1:])


def CriarSuperusuario():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "configuracao.settings")
    import django

    django.setup()

    from django.contrib.auth import get_user_model

    ModeloUsuario = get_user_model()
    CampoUsuario = ModeloUsuario.USERNAME_FIELD
    Prefixo = "DJANGO_SUPERUSER_"
    DadosUsuario = {}

    for Campo in (CampoUsuario, *ModeloUsuario.REQUIRED_FIELDS):
        Variavel = Prefixo + Campo.upper()
        Valor = os.environ.get(Variavel, "").strip()
        if not Valor:
            raise SystemExit(
                f"Preencha {Variavel} em .env.docker para criar o administrador."
            )
        DadosUsuario[Campo] = Valor

    Senha = os.environ.get(Prefixo + "PASSWORD", "")
    if not Senha:
        raise SystemExit(
            "Preencha DJANGO_SUPERUSER_PASSWORD em .env.docker para criar o administrador."
        )

    UsuarioExistente = ModeloUsuario._default_manager.filter(
        **{CampoUsuario: DadosUsuario[CampoUsuario]}
    ).first()
    if UsuarioExistente:
        if not UsuarioExistente.is_staff or not UsuarioExistente.is_superuser:
            raise SystemExit(
                "O usuário administrador configurado já existe, mas não possui permissões de superusuário."
            )
        print("Administrador já existe; nenhuma alteração foi feita.")
        return

    ModeloUsuario._default_manager.create_superuser(
        password=Senha,
        **DadosUsuario,
    )
    print("Administrador criado com sucesso.")


if __name__ == "__main__":
    Iniciar()
