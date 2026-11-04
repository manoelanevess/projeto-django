FROM python:3.13.18-slim-bookworm AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app
RUN python -m venv /opt/venv \
    && groupadd --gid 10001 estoque \
    && useradd --uid 10001 --gid estoque --create-home estoque

# Dependências antes do código: alterações em telas preservam esta camada.
COPY requirements.txt ./
RUN pip install --no-cache-dir --requirement requirements.txt

FROM base AS dev
COPY --chown=estoque:estoque manage.py ./
COPY --chown=estoque:estoque src ./src
COPY --chown=estoque:estoque Docker/Iniciar.py ./Docker/Iniciar.py
USER estoque
EXPOSE 8000
ENTRYPOINT ["python", "Docker/Iniciar.py"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

FROM dev AS testes
USER root
COPY Docker/RequisitosTestes.txt ./Docker/RequisitosTestes.txt
RUN pip install --no-cache-dir --requirement Docker/RequisitosTestes.txt
COPY .coveragerc ./
COPY --chown=estoque:estoque Testes ./Testes
USER estoque

FROM base AS dependencias-prod
COPY Docker/RequisitosProducao.txt ./Docker/RequisitosProducao.txt
RUN pip install --no-cache-dir --requirement Docker/RequisitosProducao.txt

FROM dependencias-prod AS build
COPY manage.py ./
COPY src ./src
RUN python manage.py collectstatic --noinput \
    && find /app/src -type f -name 'test*.py' -delete

# A aplicação Django precisa de Python e do código em produção (não é uma SPA).
FROM python:3.13.18-slim-bookworm AS prod
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    PATH="/opt/venv/bin:$PATH"
WORKDIR /app
RUN groupadd --gid 10001 estoque \
    && useradd --uid 10001 --gid estoque --create-home estoque
COPY --from=build /opt/venv /opt/venv
COPY --from=build --chown=estoque:estoque /app/manage.py ./
COPY --from=build --chown=estoque:estoque /app/src ./src
COPY --chown=estoque:estoque Docker/Iniciar.py ./Docker/Iniciar.py
USER estoque
EXPOSE 8000
ENTRYPOINT ["python", "Docker/Iniciar.py"]
CMD ["gunicorn", "--chdir", "/app/src", "--bind", "0.0.0.0:8000", "--workers", "2", "--threads", "2", "--timeout", "60", "--access-logfile", "-", "--error-logfile", "-", "configuracao.wsgi:application"]

# Mesmo contexto de build: o proxy recebe somente os estáticos coletados.
FROM nginx:1.30.6-alpine AS web-prod
COPY Docker/Nginx.conf /etc/nginx/nginx.conf
COPY --from=build /app/staticfiles /usr/share/nginx/html/static
USER nginx
EXPOSE 8080
ENTRYPOINT ["nginx"]
CMD ["-g", "daemon off;"]
