# Controle de Estoque com Django

Projeto de controle de estoque utilizando Django para a matéria de Frameworks Web.

## Principais funcionalidades

- Login do proprietário, sem cadastro público
- Cadastro de produtos
- Identificação por código de barras com catálogo local, APIs de produtos e pesquisa opcional na web; preenchimento somente de nome e marca
- Listagem com filtros
- Controle de estoque
- Cadastro e filtragem de fornecedores
- Carrinhos independentes para atendimentos simultâneos, com três iniciais e abertura de mais carrinhos pelo botão `+`, sem limite fixo
- Pagamento em dinheiro com troco ou PIX
- Baixa automática de estoque ao concluir uma venda

## Arquitetura

As convenções e regras do projeto estão no [Guia de Desenvolvimento](GuiaDesenvolvimento.md).

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
    pagina_principal/
    produtos/
    usuarios/
    vendas/
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

Crie a conta do proprietário:

```powershell
python manage.py createsuperuser
```

## Rodando com Docker

Adaptação da aula **Docker — Padronização de Ambiente e Preparação para Deploy** para Django: este projeto é uma MPA, com HTML gerado no servidor. Não existe frontend Node separado nem build de SPA. O mesmo `Dockerfile` possui os estágios `dev`, `build`, `prod` (Django com Gunicorn) e `web-prod` (Nginx com os arquivos estáticos do Django). O PostgreSQL roda em seu próprio serviço.

Pré-requisito: Docker Engine com Compose v2 ou superior. No Windows, abra o Docker Desktop com contêineres Linux/WSL 2. A primeira construção precisa de internet para baixar imagens e dependências; não é necessário instalar Python ou PostgreSQL no computador.

### 1. Preparar as variáveis

Na raiz do repositório, no PowerShell:

```powershell
docker --version
docker compose version
powershell -ExecutionPolicy Bypass -File .\Docker\PrepararAmbiente.ps1
```

O script cria `.env.docker` a partir de `.env.docker.example`, com chave Django, senha do banco e senha aleatória para o administrador, sem imprimir os segredos. Se o arquivo já existir, não o substitui. O `.env` usado fora do Docker permanece separado. Proteja esse arquivo e consulte nele a senha inicial do administrador.

Em Linux/macOS, copie `.env.docker.example` para `.env.docker` e preencha `DJANGO_SECRET_KEY`, `POSTGRES_PASSWORD` e `DJANGO_SUPERUSER_PASSWORD` com segredos aleatórios antes de continuar. Ajuste também `DJANGO_SUPERUSER_USERNAME` e `DJANGO_SUPERUSER_EMAIL` se desejar. As credenciais de APIs são opcionais. Nunca versione `.env.docker` nem o envie com o trabalho. Não altere a senha depois de inicializar o volume sem também alterar a senha no PostgreSQL.

### 2. Desenvolvimento com recarga automática

```powershell
docker compose up --build -d --wait
docker compose exec app python manage.py createsuperuser
```

Abra [http://localhost:8000](http://localhost:8000). Crie o proprietário somente na primeira utilização desse banco. As migrations são aplicadas automaticamente antes de iniciar o servidor; a aplicação aguarda o banco ficar saudável. O código em `src` fica montado no contêiner e o `runserver` detecta alterações por polling, inclusive no Windows. Ao salvar um componente Python, atualize a página no navegador para ver a mudança. Ao alterar `requirements.txt`, reconstrua com `docker compose up --build -d --wait`.

No primeiro início com um banco vazio, os ambientes Docker carregam fornecedores, categorias e produtos fictícios para demonstração. O carregamento é feito pelo comando `carregar_dados_demo`. Se já houver qualquer categoria, fornecedor ou produto, o comando não insere dados. Para produção real, desative a variável de carga de demonstração conforme a orientação abaixo.

Comandos de rotina:

```powershell
docker compose logs -f app
docker compose exec app sh
docker compose exec app python manage.py check
docker compose exec app python manage.py test configuracao features --noinput
docker compose down
docker compose up -d --wait
```

O banco começa vazio e fica no volume `estoque-dev_dados-postgres`. O PostgreSQL não publica uma porta no computador, evitando conflito com instalações existentes. Os dados atuais do comércio não são importados automaticamente.

### 3. Produção local em localhost:8080

```powershell
docker compose -f compose.prod.yaml up --build -d --wait
```

Na primeira inicialização, o contêiner aplica as migrations, cria o superusuário definido em `.env.docker` e carrega dados fictícios de demonstração se o banco ainda não tiver nenhuma categoria, fornecedor ou produto. Em reinicializações, não duplica nem altera esses cadastros. **Não use essa opção em um banco vazio destinado a dados reais**; para um deploy real, remova `DJANGO_CARREGAR_DADOS_DEMO: "1"` de `compose.prod.yaml` antes de subir. Abra [http://localhost:8080](http://localhost:8080) e entre com as credenciais configuradas. Esse ambiente usa outro volume, `estoque-prod_dados-postgres`; portanto, o proprietário e os cadastros de desenvolvimento não aparecem aqui. É possível manter ambos os ambientes rodando, pois usam nomes e portas diferentes.

A imagem da aplicação executa Gunicorn como usuário sem privilégios. O Nginx também roda sem root, entrega `/static/` e encaminha as demais URLs para o Django, preservando acesso direto e F5 nas rotas internas. Não há volumes de código em produção. `GET /health` responde `200` quando a aplicação consegue consultar o PostgreSQL e `503` em caso de falha, sem expor credenciais; o Nginx só inicia depois de a aplicação ficar saudável. Todos os serviços de produção usam `restart: unless-stopped`.

```powershell
Invoke-RestMethod http://localhost:8080/health
docker compose -f compose.prod.yaml ps
docker compose -f compose.prod.yaml logs -f app web
docker compose -f compose.prod.yaml down
docker compose -f compose.prod.yaml up -d --wait
```

Este Compose simula produção **local** em HTTP, com `DEBUG=0` e acesso limitado a `127.0.0.1`. Para um deploy público, configure domínio e HTTPS no proxy, `DJANGO_ALLOWED_HOSTS` e `DJANGO_CSRF_TRUSTED_ORIGINS`, e ative cookies seguros, redirecionamento HTTPS e HSTS. Os valores HTTP do Compose local precisam ser ajustados nesse deploy.

### 4. Persistência, backup e dados existentes

`down` remove os contêineres, mas preserva o volume do PostgreSQL. **Não utilize `down -v` para parar o sistema: essa opção apaga o banco desse ambiente.** Volumes não substituem backups. Exemplo de backup da produção, sem passar dados binários por redirecionamento do PowerShell:

```powershell
New-Item -ItemType Directory -Path .\backups -Force
$NomeBackup = 'Estoque-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '.backup'
docker compose -f compose.prod.yaml exec banco sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --format=custom --no-owner --no-acl --file=/tmp/estoque.backup'
if ($LASTEXITCODE -ne 0) { throw 'O backup falhou.' }
docker compose -f compose.prod.yaml cp banco:/tmp/estoque.backup (Join-Path '.\backups' $NomeBackup)
if ($LASTEXITCODE -ne 0) { throw 'A copia do backup falhou.' }
```

Para levar os dados já cadastrados no PostgreSQL fora do Docker, faça um `pg_dump` desse banco e restaure em um **volume novo, antes de iniciar a aplicação**. Não restaure sobre os cadastros de outro ambiente. Exemplo para um backup no formato custom, substituindo o caminho do arquivo:

```powershell
docker compose -f compose.prod.yaml up -d --wait banco
docker compose -f compose.prod.yaml cp 'C:\TransferenciaEstoque\BancoComercio.backup' banco:/tmp/importacao.backup
if ($LASTEXITCODE -ne 0) { throw 'A copia do backup falhou.' }
docker compose -f compose.prod.yaml exec banco sh -c 'pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --no-owner --no-acl --exit-on-error --single-transaction /tmp/importacao.backup'
if ($LASTEXITCODE -ne 0) { throw 'A restauracao falhou. Nao inicie a aplicacao.' }
docker compose -f compose.prod.yaml up --build -d --wait
```

O backup leva os usuários e suas senhas de login, produtos, fornecedores, vendas e fotos salvas no banco. Não é necessário criar outro proprietário após importar os dados. Teste o login e confira os registros restaurados antes de usar o sistema no comércio. Nenhuma restauração ou migração de dados reais faz parte da criação dos arquivos Docker.

### 5. Conferência para a aula

Os resultados dos testes, a auditoria dos sete itens dos slides e os tamanhos das imagens estão em [Docker/Auditoria.md](Docker/Auditoria.md).

1. Suba desenvolvimento, faça um cadastro e altere um componente: o servidor recarrega ao salvar.
2. Execute `down` e `up` e confirme que o cadastro continua lá.
3. Suba produção, faça login, cadastre algo e abra uma rota interna diretamente, como `/estoque`, atualizando com F5.
4. Confira `GET /health`, os serviços saudáveis e os usuários das imagens:

```powershell
docker compose config --quiet
docker compose -f compose.prod.yaml config --quiet
docker image inspect controle-estoque-app:prod --format '{{.Config.User}}'
docker image inspect controle-estoque-web:prod --format '{{.Config.User}}'
docker images --filter 'reference=controle-estoque-*'
git status --short
```

As imagens usam versões explícitas de Python, Nginx e PostgreSQL, sem `latest`. `requirements.txt` é copiado antes do código para aproveitar o cache. `.dockerignore` exclui ambientes virtuais, `.env*`, Git, caches e backups. A imagem final Django conserva o código necessário à execução, mas não os testes; somente os estáticos coletados vão para o Nginx. Dependências de produção do contêiner ficam em `Docker/RequisitosProducao.txt`.

Se a porta 8000 estiver ocupada, no PowerShell defina `$env:PORTA_DESENVOLVIMENTO = '8001'` antes de subir desenvolvimento e acesse `http://localhost:8001`. Mantenha essa variável ao executar novamente `up` nesse ambiente. Para produção, altere somente a porta do computador no Compose (à esquerda dos dois-pontos), mantendo o endereço `127.0.0.1`. Em falhas de inicialização, comece por `docker compose logs app banco` ou pelo equivalente com `-f compose.prod.yaml`. Não use `docker system prune` nem remova volumes para resolver um erro sem antes preservar os dados.

## Testes e performance

O plano, os comandos e os resultados da aula de testes estão em [TESTES.md](TESTES.md). As medições Lighthouse, o diagnóstico e o antes/depois da compressão estão em [PERFORMANCE.md](PERFORMANCE.md). O ambiente `compose.testes.yaml` usa PostgreSQL separado e a imagem `testes`, com coverage.py, sem instalar ferramentas na imagem de produção.

```powershell
docker compose -f compose.testes.yaml run --build --rm app
docker compose -f compose.testes.yaml run --rm app python Testes/ProvaReal.py
```

## Identificação de Produtos

O cadastro consulta primeiro os produtos e as identificações salvas no PostgreSQL. Depois tenta os catálogos especializados e, se necessário e configurado, pesquisa a web com IA. Somente nome e marca são sugeridos; categoria, validade e dados do estoque são informados pelo vendedor. O cadastro só é concluído ao confirmar o formulário.

Open Food Facts funciona sem chave. Para ampliar a cobertura de produtos variados, configure `COSMOS_API_TOKEN` e `COSMOS_API_USER_AGENT` fornecidos pelo [Cosmos](https://api.cosmos.bluesoft.com.br/api). Ajuste `COSMOS_LIMITE_DIARIO` ao plano contratado (padrão conservador: 25). Confira as licenças aplicáveis aos dados antes de ativar a integração.

A pesquisa com IA requer `OPENAI_API_KEY` e `PESQUISA_PRODUTO_IA_ATIVA=1`. Ela é opcional, desativada por padrão e tem cobrança própria. Configure limites de gastos no provedor antes de ativá-la. As credenciais ficam somente no `.env`, nunca no navegador ou Git. Reinicie o servidor após configurá-las.

As sugestões ficam no catálogo local por 24 horas; dados confirmados no cadastro ou na edição têm prioridade e continuam disponíveis. Nenhuma fonte garante encontrar todos os códigos. Sem resultado confiável ou sem conexão, o cadastro manual permanece disponível. Consulte [ROTAS.md](ROTAS.md) para limites e detalhes das integrações.

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

Status: substituída pela Decisão 09.

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

Consequências: Página Principal, produtos, estoque, fornecedores e login usam a mesma navegação; URLs inexistentes exibem uma tela de retorno para a Página Principal.

Alternativa descartada: repetir HTML e CSS de menu/topo dentro de cada feature.

## Decisão 08 — Autenticação sem cadastro público

Data: 11/10/2026

Contexto: o sistema será usado em um comércio específico e somente o proprietário terá acesso.

Decisão: usar a autenticação nativa do Django com uma conta criada pelo terminal, sem tela de cadastro, cargos ou níveis de permissão. As telas do sistema exigem login e, após a autenticação, o proprietário tem acesso completo.

Consequências: o fluxo de acesso permanece simples; visitantes não acessam dados digitando uma URL diretamente; novas contas, se necessárias no futuro, devem ser criadas de forma administrativa.

Alternativa descartada: cadastro público de usuários e controle de permissões por cargo, pois não fazem parte da necessidade atual do comércio.

## Decisão 09 — Página Principal orientada ao atendimento

Data: 11/10/2026

Contexto: o proprietário precisa acessar rapidamente as tarefas usadas no balcão, principalmente a pesquisa de produtos e os atendimentos em andamento.

Decisão: substituir a Dashboard pela Página Principal, colocando a pesquisa para venda e o acesso aos carrinhos antes dos indicadores administrativos. Esta decisão substitui a Decisão 05 quanto ao conteúdo da tela inicial, mas preserva o layout administrativo compartilhado.

Consequências: a rota `/` passa a apoiar diretamente o atendimento; indicadores de estoque e atalhos continuam disponíveis abaixo das ações principais.

Alternativa descartada: manter os indicadores como conteúdo principal e exigir que o proprietário navegue para outra tela antes de pesquisar produtos.

## Decisão 10 — Carrinhos independentes e baixa transacional do estoque

Data: 11/10/2026

Contexto: o comércio precisa atender vários clientes ao mesmo tempo, com produtos vendidos por unidade ou por peso e pagamento em dinheiro ou PIX.

Decisão: iniciar cada sessão com três carrinhos independentes e permitir abrir outros pelo botão `+`, sem limite fixo, tanto na Página Principal quanto em Carrinhos. A conclusão cria uma venda e seus itens no PostgreSQL e reduz o estoque quantitativo dentro de uma única transação; produtos por unidade aceitam apenas números inteiros e produtos por quilograma aceitam até três casas decimais.

Consequências: cancelar um carrinho não altera o estoque nem os outros atendimentos; dinheiro exige valor recebido e calcula troco; PIX conclui sem esse campo; falta de estoque impede toda a operação, sem baixa parcial. Cada carrinho também pode ser fechado individualmente, com confirmação quando houver itens ou cliente identificado. Se todos forem fechados, o botão `+` permite abrir um novo atendimento.

Alternativa descartada: usar um único carrinho ou reduzir o estoque ao adicionar produtos, pois isso impediria atendimentos simultâneos e reservaria mercadoria antes da conclusão da compra.

## Decisão 11 — Carrinhos sempre abertos na Página Principal

Data: 02/10/2026

Contexto: o proprietário precisa consultar o estoque durante o atendimento e acompanhar vários clientes sem sair da Página Principal.

Decisão: manter os cards dos atendimentos alinhados acima dos respectivos painéis, sempre abertos. Todos os carrinhos da sessão ficam lado a lado, com rolagem horizontal compartilhada quando necessário; cada um possui pesquisa por nome, categoria, marca ou fornecedor, seleção de quantidade ou peso, total e pagamento. O botão `+` abre mais carrinhos sem limite fixo. A consulta de estoque da Página Principal é somente leitura, enquanto inclusão, edição e exclusão pertencem à área Estoque e à feature Produtos.

Consequências: os painéis permanecem abaixo dos cards, sem esconder o restante da página; a rolagem mantém os cards alinhados aos painéis, inclusive em telas menores; o proprietário consegue comparar marcas e estoques antes de adicionar um item. Fechar um carrinho remove apenas aquele atendimento, preservando os demais.

Alternativa descartada: manter apenas uma aba de carrinho por vez ou abrir painéis sobrepostos ao conteúdo, pois essas opções dificultam acompanhar atendimentos simultâneos.

## Decisão 12 — Experiência desktop como prioridade

Data: 17/10/2026

Contexto: o sistema será usado majoritariamente no computador do comércio, durante o atendimento no balcão.

Decisão: projetar e validar primeiro a experiência desktop, com os carrinhos abertos lado a lado e rolagem horizontal quando ultrapassarem a largura disponível. Manter apenas uma adaptação responsiva básica para evitar quebra de conteúdo em telas menores.

Consequências: decisões de densidade, largura de tabelas e disposição simultânea dos carrinhos priorizam monitor e teclado; refinamentos específicos de experiência mobile não fazem parte do escopo atual.

Alternativa descartada: abordagem mobile-first, pois não corresponde ao principal ambiente de uso do sistema.

## Decisão 13 — Identificação opcional do cliente no carrinho

Data: 17/10/2026

Contexto: clientes conhecidos podem ser identificados durante o atendimento, mas a maioria das vendas não exige cadastro prévio do comprador.

Decisão: permitir um nome opcional em cada carrinho. O nome permanece temporariamente na sessão, é copiado para a venda concluída e a identificação volta para `Carrinho <número>` quando o atendimento é concluído ou cancelado, inclusive nos carrinhos abertos pelo botão `+`.

Consequências: o histórico do Dashboard mostra quem realizou a compra quando o proprietário informou um nome; vendas sem identificação aparecem como `Não identificado`; todos os carrinhos continuam independentes e reutilizáveis.

Alternativa descartada: criar um cadastro obrigatório de clientes, pois aumentaria o tempo de atendimento e não é necessário para registrar vendas ocasionais.

## Decisão 14 — Estoque unificado e Dashboard separado

Data: 18/10/2026

Contexto: o comércio trabalha com alimentos, rações, papelaria, ferramentas e itens vendidos por unidade, metro, peso ou preço fixo. A listagem de Produtos e o controle de Estoque representavam a mesma rotina de manutenção, enquanto os indicadores e o histórico de vendas possuíam função gerencial distinta.

Decisão: transformar a antiga área Produtos em Estoque, concentrando cadastro, edição, exclusão lógica, busca por nome, marca ou fornecedor e filtro por categoria. Preservar a antiga tela de indicadores e vendas recentes como Dashboard. Produtos vendidos por quilograma usam apenas disponibilidade e não sofrem baixa numérica; unidades, metros e itens de preço fixo mantêm quantidade e estoque mínimo.

Consequências: `/estoque` passa a ser a manutenção completa dos produtos; `/dashboard` apresenta indicadores e histórico; `/produtos` redireciona para `/estoque`; vendas por peso permanecem registradas no histórico sem depender de uma quantidade estimada em estoque.

Alternativa descartada: manter Produtos e Estoque como cadastros separados ou inventar uma quantidade para produtos a granel, pois isso duplicaria responsabilidades e produziria saldos imprecisos.

## Decisão 15 — Fornecedores cadastrados e vinculados aos produtos

Data: 02/10/2026

Contexto: pesquisar o fornecedor como texto livre permite variações de escrita e não garante que o produto esteja associado a um fornecedor conhecido pelo comércio.

Decisão: manter fornecedores em cadastro próprio, com nome, telefone, e-mail, cidade e situação. Todo produto deve escolher um fornecedor cadastrado; a área Estoque oferece um filtro específico por fornecedor, além da busca textual. Fornecedores removidos são apenas inativados para preservar produtos e registros históricos.

Consequências: o cadastro de produtos usa uma lista consistente de fornecedores; renomear um fornecedor atualiza sua identificação em todos os produtos relacionados; fornecedores inativos não aparecem em novos cadastros, mas os vínculos existentes continuam válidos.

Alternativa descartada: continuar armazenando o nome do fornecedor diretamente no produto, pois isso geraria duplicidades e dificultaria filtros confiáveis.

## Decisão 16 — Pesquisa incremental no carrinho

Data: 02/10/2026

Contexto: durante o atendimento, o proprietário precisa localizar rapidamente um produto entre marcas e fornecedores diferentes sem interromper a digitação para enviar o formulário.

Decisão: pesquisar produtos disponíveis a cada trecho digitado no carrinho, com um pequeno intervalo para evitar requisições desnecessárias. A consulta considera nome, categoria, marca e fornecedor; a query string continua registrando a busca e o botão Pesquisar permanece como alternativa sem JavaScript.

Consequências: resultados como `A`, `Ar` e `Arroz` aparecem progressivamente, requisições antigas são canceladas quando a busca muda e as mesmas regras de disponibilidade do estoque são reutilizadas.

Alternativa descartada: exigir o envio manual do formulário para cada pesquisa, pois isso torna o atendimento mais lento.

## Decisão 17 — Custo, lucro e consolidação mensal das vendas

Data: 02/10/2026

Contexto: a Dashboard precisa mostrar o valor investido no estoque, os lucros do dia, mês e ano e os produtos abaixo do estoque mínimo sem manter indefinidamente todos os detalhes de vendas antigas.

Decisão: cadastrar preço de custo e preço de venda em cada produto. As tabelas administrativas de produtos exibem os dois valores, enquanto o carrinho e o histórico de vendas mostram somente o preço cobrado. Ao concluir uma venda, copiar o custo vigente para o item e registrar o lucro calculado. Na primeira abertura da Dashboard após a mudança de mês, consolidar vendas de meses anteriores em totais mensais não exibidos e remover seus detalhes; esses resumos continuam compondo o lucro anual.

Consequências: alterar o custo de um produto não modifica o lucro de vendas antigas; produtos com quantidade controlada compõem o valor do estoque pelo custo; produtos vendidos por peso ficam fora dessa soma por não possuírem quantidade cadastrada; o histórico visual mantém somente as vendas do mês atual.

Alternativa descartada: tratar faturamento como lucro ou recalcular vendas antigas pelo custo atual, pois ambas as opções produziriam indicadores financeiros incorretos.

## Decisão 18 — Virada diária dos indicadores às 07:00

Data: 02/10/2026

Contexto: o comércio funciona das 08:00 às 20:00 e o lucro diário precisa estar zerado antes do início do atendimento, sem dividir vendas de um mesmo turno por causa da meia-noite.

Decisão: considerar o dia comercial no intervalo entre 07:00 de um dia e 06:59 do dia seguinte para calcular o lucro e o total vendido de hoje.

Consequências: vendas realizadas antes das 07:00 ainda pertencem ao dia comercial anterior; a partir das 07:00 os indicadores diários iniciam um novo período, enquanto os totais mensal e anual continuam seguindo o calendário.

Alternativa descartada: reiniciar os indicadores à meia-noite, pois essa virada não representa a rotina de funcionamento do comércio.

## Decisão 19 — Separar faturamento de lucro dos produtos

Data: 02/10/2026

Contexto: a soma das vendas precisa ficar visível nos períodos diário, mensal e anual, mas chamar esse valor de lucro esconderia o custo dos produtos vendidos.

Decisão: apresentar os cards principais como faturamento de hoje, do mês e do ano. Manter um resumo financeiro separado com entradas das vendas, custo dos produtos vendidos e lucro dos produtos para os mesmos períodos.

Consequências: cada venda aumenta imediatamente o faturamento; o lucro dos produtos só aumenta quando o preço de venda supera o custo registrado no momento da venda; valores mensais consolidados continuam permitindo calcular o custo pela diferença entre faturamento e lucro. Aluguel, energia e outras despesas gerais ficam fora desse cálculo.

Alternativa descartada: usar o termo lucro para toda entrada de venda, pois isso mistura faturamento com resultado financeiro e pode levar a decisões incorretas.

## Decisão 20 — Detalhes expansíveis nas vendas recentes

Data: 02/10/2026

Contexto: o proprietário precisa conferir rapidamente quais produtos e quantidades formaram uma venda sem sair da Dashboard durante o atendimento.

Decisão: tornar cada linha de venda recente expansível no próprio histórico. O detalhe mostra produto, quantidade, preço unitário cobrado e subtotal, mantendo preços de custo fora dessa visualização.

Consequências: até cinco vendas recentes carregam seus itens em uma consulta otimizada e permanecem fechadas até o clique; o controle também funciona por teclado no botão de expansão.

Alternativa descartada: abrir uma página separada para cada venda, pois isso interromperia a consulta rápida e adicionaria navegação desnecessária.

## Decisão 22 — Entradas de estoque organizadas por lote

Data: 05/10/2026

Contexto: novas unidades de um produto podem chegar com custo, preço de venda e fornecedor diferentes enquanto ainda existe saldo da entrada anterior. Substituir os preços no cadastro perderia a composição real do estoque e distorceria o lucro das vendas.

Decisão: manter o produto como identidade de nome, marca, categoria e forma de venda, e registrar cada entrada em `LoteEstoque`. Cada lote preserva fornecedor, quantidade recebida, saldo disponível, preço de custo, preço de venda, disponibilidade e data de entrada. O carrinho exige a escolha do lote e a conclusão da venda reduz somente o saldo escolhido dentro da transação.

Consequências: um produto pode aparecer no carrinho com mais de uma opção de preço; o item vendido guarda o lote e copia seus preços para preservar o histórico; o valor do estoque considera o custo de cada lote; produtos por peso mantêm encerramento manual por não possuírem quantidade exata; os campos de preço e quantidade de `Produto` permanecem como resumo para compatibilidade das telas e filtros existentes.

Alternativa descartada: duplicar o produto ou sobrescrever custo, venda e quantidade a cada nova compra, pois ambas as opções perderiam a origem do saldo e tornariam incorretos o lucro e a baixa de estoque.
