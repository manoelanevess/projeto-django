"""Verificação de prontidão da aplicação e da conexão com PostgreSQL."""
from django.db import DatabaseError, connection
from django.http import JsonResponse
from django.views.decorators.http import require_GET


@require_GET
def ComponenteSaude(Request):
    try:
        with connection.cursor() as Cursor:
            Cursor.execute("SELECT 1")
            Cursor.fetchone()
    except DatabaseError:
        Resposta = JsonResponse({"status": "indisponivel"}, status=503)
    else:
        Resposta = JsonResponse({"status": "ok"})

    Resposta["Cache-Control"] = "no-store"
    return Resposta
