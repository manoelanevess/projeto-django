# Controle de Estoque com Django

Projeto de controle de estoque utilizando Django para a matéria de Frameworks Web.

## Principais funcionalidades

- Login do proprietário, sem cadastro público
- Cadastro de produtos
- Listagem com filtros
- Controle de estoque
- Cadastro e filtragem de fornecedores
- Três carrinhos de compras para atendimentos simultâneos
- Pagamento em dinheiro com troco ou PIX
- Baixa automática de estoque ao concluir uma venda

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

Data: 02/10/2026

Contexto: o sistema será usado em um comércio específico e somente o proprietário terá acesso.

Decisão: usar a autenticação nativa do Django com uma conta criada pelo terminal, sem tela de cadastro, cargos ou níveis de permissão. As telas do sistema exigem login e, após a autenticação, o proprietário tem acesso completo.

Consequências: o fluxo de acesso permanece simples; visitantes não acessam dados digitando uma URL diretamente; novas contas, se necessárias no futuro, devem ser criadas de forma administrativa.

Alternativa descartada: cadastro público de usuários e controle de permissões por cargo, pois não fazem parte da necessidade atual do comércio.

## Decisão 09 — Página Principal orientada ao atendimento

Data: 02/10/2026

Contexto: o proprietário precisa acessar rapidamente as tarefas usadas no balcão, principalmente a pesquisa de produtos e os atendimentos em andamento.

Decisão: substituir a Dashboard pela Página Principal, colocando a pesquisa para venda e o acesso aos carrinhos antes dos indicadores administrativos. Esta decisão substitui a Decisão 05 quanto ao conteúdo da tela inicial, mas preserva o layout administrativo compartilhado.

Consequências: a rota `/` passa a apoiar diretamente o atendimento; indicadores de estoque e atalhos continuam disponíveis abaixo das ações principais.

Alternativa descartada: manter os indicadores como conteúdo principal e exigir que o proprietário navegue para outra tela antes de pesquisar produtos.

## Decisão 10 — Três carrinhos e baixa transacional do estoque

Data: 02/10/2026

Contexto: o comércio pode atender até três clientes ao mesmo tempo, com produtos vendidos por unidade ou por peso e pagamento em dinheiro ou PIX.

Decisão: manter três carrinhos independentes na sessão. A conclusão cria uma venda e seus itens no PostgreSQL e reduz o estoque quantitativo dentro de uma única transação; produtos por unidade aceitam apenas números inteiros e produtos por quilograma aceitam até três casas decimais.

Consequências: cancelar um carrinho não altera o estoque nem os outros atendimentos; dinheiro exige valor recebido e calcula troco; PIX conclui sem esse campo; falta de estoque impede toda a operação, sem baixa parcial.

Alternativa descartada: usar um único carrinho ou reduzir o estoque ao adicionar produtos, pois isso impediria atendimentos simultâneos e reservaria mercadoria antes da conclusão da compra.

## Decisão 11 — Carrinhos expansíveis na Página Principal

Data: 02/10/2026

Contexto: o proprietário precisa consultar o estoque durante o atendimento e, em alguns momentos, acompanhar até três clientes sem sair da Página Principal.

Decisão: manter os cards de atendimentos em andamento como acionadores de painéis expansíveis. Até três painéis podem permanecer abertos lado a lado; cada um possui pesquisa por nome, categoria, marca ou fornecedor, seleção de quantidade ou peso, total e pagamento. A consulta de estoque da Página Principal é somente leitura, enquanto inclusão, edição e exclusão pertencem à área Estoque e à feature Produtos.

Consequências: os carrinhos não escondem a página, pois são inseridos abaixo dos cards e deslocam o estoque para baixo; no celular, os painéis usam rolagem horizontal; o proprietário consegue comparar marcas e estoques antes de adicionar um item.

Alternativa descartada: manter apenas uma aba de carrinho por vez ou abrir painéis sobrepostos ao conteúdo, pois essas opções dificultam acompanhar atendimentos simultâneos.

## Decisão 12 — Experiência desktop como prioridade

Data: 02/10/2026

Contexto: o sistema será usado majoritariamente no computador do comércio, durante o atendimento no balcão.

Decisão: projetar e validar primeiro a experiência desktop, incluindo os três carrinhos lado a lado. Manter apenas uma adaptação responsiva básica para evitar quebra de conteúdo em telas menores.

Consequências: decisões de densidade, largura de tabelas e disposição simultânea dos carrinhos priorizam monitor e teclado; refinamentos específicos de experiência mobile não fazem parte do escopo atual.

Alternativa descartada: abordagem mobile-first, pois não corresponde ao principal ambiente de uso do sistema.

## Decisão 13 — Identificação opcional do cliente no carrinho

Data: 02/10/2026

Contexto: clientes conhecidos podem ser identificados durante o atendimento, mas a maioria das vendas não exige cadastro prévio do comprador.

Decisão: permitir um nome opcional em cada carrinho. O nome permanece temporariamente na sessão, é copiado para a venda concluída e volta para `Carrinho 1`, `Carrinho 2` ou `Carrinho 3` quando o atendimento é concluído ou cancelado.

Consequências: o histórico do Dashboard mostra quem realizou a compra quando o proprietário informou um nome; vendas sem identificação aparecem como `Não identificado`; os três carrinhos continuam independentes e reutilizáveis.

Alternativa descartada: criar um cadastro obrigatório de clientes, pois aumentaria o tempo de atendimento e não é necessário para registrar vendas ocasionais.

## Decisão 14 — Estoque unificado e Dashboard separado

Data: 02/10/2026

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
