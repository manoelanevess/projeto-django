"""Configuração WSGI do projeto."""
import os
import sys
from pathlib import Path

from django.core.wsgi import get_wsgi_application


BaseProjeto = Path(__file__).resolve().parents[2]
PastaSrc = BaseProjeto / "src"
sys.path.insert(0, str(PastaSrc))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "configuracao.settings")

application = get_wsgi_application()
