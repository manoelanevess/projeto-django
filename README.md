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

Crie o arquivo `.env` a partir do exemplo e ajuste os dados do PostgreSQL:

```powershell
Copy-Item .env.example .env
```

Banco esperado para desenvolvimento:

```sql
CREATE DATABASE controle_estoque;
```

Verifique a instalação do Django:

```powershell
python -m django --version
```

Rode a aplicação:

```powershell
python manage.py runserver
```

Depois que o PostgreSQL estiver instalado, rodando e configurado no `.env`, rode as migrations:

```powershell
python manage.py migrate
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

Decisão: usar nomes em português e PascalCase em arquivos, funções e variáveis criados pelo projeto, exceto quando o Django exigir nomes próprios do framework ou quando variáveis de ambiente seguirem convenção em maiúsculas.

Consequências: o código fica alinhado ao vocabulário do trabalho; arquivos obrigatórios como `manage.py`, `settings.py`, `urls.py`, `asgi.py` e `wsgi.py` mantêm o padrão esperado pelo Django, e variáveis como `POSTGRES_DB` mantêm o padrão comum de ambiente.

Alternativa descartada: misturar inglês com português ou alternar entre snake_case, camelCase e PascalCase sem regra.

## Decisão 04 — Banco de dados PostgreSQL

Data: 02/09/2026

Contexto: o projeto tende a crescer além de um exemplo pequeno de disciplina e precisa de um banco de dados mais próximo de um ambiente real.

Decisão: usar PostgreSQL como banco de dados principal, configurado por variáveis de ambiente no arquivo `.env`.

Consequências: o projeto ganha um banco mais robusto; será necessário ter PostgreSQL instalado e um banco criado antes de rodar migrations.

Alternativa descartada: SQLite, por ser mais indicado para projetos pequenos, protótipos e configuração inicial simples.

## Decisão 05 — Interface inicial em formato de dashboard

Data: 09/09/2026

Contexto: a aplicação precisa ter aparência de sistema administrativo de estoque, com leitura rápida dos dados principais.

Decisão: a tela inicial seguirá uma referência visual de dashboard, com menu lateral, barra superior, cards de indicadores e atalhos para as features.

Consequências: o primeiro acesso já comunica o objetivo do sistema; novas telas devem manter o mesmo padrão visual para parecerem parte do mesmo produto.

Alternativa descartada: página inicial simples apenas com tabela de produtos, por não demonstrar bem a experiência final esperada.

## Decisão 06 — Mapa de rotas versionado

Data: 09/09/2026

Contexto: a aula de roteamento reforçou que a URL deve representar o estado da aplicação e que filtros pertencem à query string.

Decisão: manter o mapa de navegação em `ROTAS.md`, com rota, tela, parâmetro, proteção, query string e status de implementação.

Consequências: novas telas passam a ter URL planejada antes do código; filtros como busca e estoque ficam compartilháveis por link.

Alternativa descartada: criar rotas conforme a necessidade sem documentação prévia.

## Decisão 07 — Layout compartilhado e rota 404

Data: 09/09/2026

Contexto: menu e topo não devem ser copiados em cada tela, e toda aplicação precisa responder bem quando a URL não existe.

Decisão: criar um layout base em `src/componentes/LayoutBase.py` e uma página 404 compartilhada em `src/componentes/ComponenteErro.py`.

Consequências: dashboard, produtos, estoque, fornecedores e login usam a mesma navegação; URLs inexistentes exibem uma tela de retorno para o dashboard.

Alternativa descartada: repetir HTML e CSS de menu/topo dentro de cada feature.
