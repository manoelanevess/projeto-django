#!/usr/bin/env python
"""Comando principal do Django para tarefas administrativas."""
import os
import sys
from pathlib import Path


def main():
    BaseProjeto = Path(__file__).resolve().parent
    PastaSrc = BaseProjeto / "src"
    sys.path.insert(0, str(PastaSrc))

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "configuracao.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
