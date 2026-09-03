# Controle de Estoque com Django

Projeto de controle de estoque utilizando Django para a matéria de Frameworks Web.

## Principais funcionalidades

- Cadastro e login de usuários
- Cadastro de produtos
- Listagem com filtros
- Controle de estoque
- Cadastro e filtragem de fornecedores

## Arquitetura

O projeto será organizado por feature em `src/features/<nome-da-feature>`.
O prefixo `@` será usado como alias para a pasta `src` nos arquivos JavaScript/TypeScript e nas ferramentas que leem o `jsconfig.json`.
No Python, como `@` não é um prefixo válido de importação, o `manage.py` adiciona `src` ao path e os imports usam o pacote `features`.

Estrutura inicial:

```text
src/
  componentes/
  configuracao/
  features/
    estoque/
    fornecedor/
    produtos/
    usuarios/
```

## Configuração do ambiente

Crie e ative um ambiente virtual:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Instale as dependências:

```powershell
python -m pip install -r requirements.txt
```

Verifique a instalação do Django:

```powershell
python -m django --version
```

Rode a aplicação:

```powershell
python manage.py runserver
```

## Decisão 01 — Organização por feature

Data: 02/09/2026

Contexto: projeto com funcionalidades de usuários, produtos, estoque e fornecedores.

Decisão: agrupar o código em `src/features/<nome-da-feature>`.

Consequências: cada feature fica isolada; `src/componentes` guarda apenas o que for usado por duas ou mais features.

Alternativa descartada: agrupamento por tipo, como uma pasta global para APIs, outra para lógicas e outra para componentes.

## Decisão 02 — Alias de caminho com @

Data: 02/09/2026

Contexto: o projeto precisa de um padrão curto para referenciar arquivos dentro de `src`.

Decisão: usar o prefixo `@` como alias para `src` nas ferramentas compatíveis, começando pelo `jsconfig.json`.

Consequências: caminhos de frontend podem usar `@/features/...`; no Python, os imports continuam usando `features...` por limitação da linguagem.

Alternativa descartada: usar caminhos relativos longos, como `../../../features/produtos`.

## Decisão 03 — Nomenclatura em português e PascalCase

Data: 02/09/2026

Contexto: o projeto será desenvolvido em português e precisa manter um padrão de leitura consistente.

Decisão: usar nomes em português e PascalCase em arquivos, funções e variáveis criados pelo projeto, exceto quando o Django exigir nomes próprios do framework.

Consequências: o código fica alinhado ao vocabulário do trabalho; arquivos obrigatórios como `manage.py`, `settings.py`, `urls.py`, `asgi.py` e `wsgi.py` mantêm o padrão esperado pelo Django.

Alternativa descartada: misturar inglês com português ou alternar entre snake_case, camelCase e PascalCase sem regra.
