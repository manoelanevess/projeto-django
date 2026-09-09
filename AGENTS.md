# AGENTS.md

## Projeto

Sistema de controle de estoque para a matéria de Frameworks Web.

Framework: Django 6.1.1.
Banco de dados: PostgreSQL configurado por `.env`.
Roteamento: MPA com `path()` no arquivo `src/configuracao/urls.py`.

## Estrutura obrigatória

- `src/configuracao/` guarda configurações globais, rotas principais, ASGI e WSGI.
- `src/features/<nome-da-feature>/` guarda API, lógica e componentes da feature.
- `src/componentes/` guarda apenas código usado por duas ou mais features.
- `ROTAS.md` guarda o mapa de navegação e os esboços de telas.
- A rota deve ser uma casca fina: registrar URL em `urls.py` e importar o componente da feature.

## Regras de código

- Usar português nos nomes do domínio do projeto.
- Usar PascalCase para arquivos, funções e variáveis criados pelo projeto.
- Manter nomes exigidos pelo Django no padrão do framework, como `manage.py`, `settings.py`, `urls.py`, `asgi.py` e `wsgi.py`.
- Manter variáveis de ambiente em maiúsculas, como `POSTGRES_DB`.
- Separar acesso a dados, lógica e componente quando a feature crescer.
- Filtros, busca, paginação e ordenação devem ficar na query string.
- Links de navegação devem ser `<a href="...">` no HTML final.
- Criar estado vazio e rota 404 quando houver tela de listagem ou rota nova.

## Restrições

- Não usar SQLite neste projeto.
- Não instalar biblioteca nova sem perguntar antes.
- Não criar componentes compartilhados se eles forem usados por apenas uma feature.
- Não importar uma feature dentro de outra sem motivo claro; dashboard e relatórios podem consumir funções públicas de outras features para montar indicadores.
- Não commitar `.env`, `.venv/`, bancos locais ou arquivos de cache.

## Comandos

```powershell
python -m pip install -r requirements.txt
python manage.py check
python manage.py runserver
python manage.py migrate
```

## Contexto de roteamento

Django usa roteamento baseado em configuração. As rotas ficam em `src/configuracao/urls.py`; cada rota deve chamar um componente dentro da feature correspondente.
