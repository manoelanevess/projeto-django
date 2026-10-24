# Mapa de rotas

As URLs usam substantivos no plural, letras minúsculas e hífen quando necessário. Filtros e buscas ficam na query string.

| rota | tela | parâmetro | protegida | query string | status |
| --- | --- | --- | --- | --- | --- |
| `/` | Página Principal | não | sim | `busca`, `inicio`, `carrinho`, `busca_carrinho`, `carrinhos_abertos` | implementada |
| `/login` | Login | não | não | não | implementada |
| `/logout` | Encerramento da sessão | não | sim | não | implementada |
| `/configuracoes` | Nome do comércio e foto de perfil (GET e POST) | não | sim | não | implementada |
| `/configuracoes/foto-perfil` | Foto do usuário autenticado | não | sim | `v` identifica a versão da foto | implementada |
| `/carrinho` | Carrinho de compras | não | sim | `carrinho`, `busca` | implementada |
| `/carrinho/abrir` | Abrir mais um atendimento | não | sim | não, ação POST | implementada |
| `/carrinho/fechar` | Fechar um atendimento | não | sim | não, ação POST | implementada |
| `/carrinho/pesquisar` | Pesquisa incremental de produtos no carrinho | não | sim | `busca` | implementada |
| `/carrinho/ler-codigo` | Adicionar produto pelo código de barras | não | sim | não, ação POST | implementada |
| `/carrinho/adicionar` | Adicionar item | não | sim | não, ação POST | implementada |
| `/carrinho/remover` | Remover item | não | sim | não, ação POST | implementada |
| `/carrinho/cancelar` | Cancelar atendimento | não | sim | não, ação POST | implementada |
| `/carrinho/concluir` | Concluir venda | não | sim | não, ação POST | implementada |
| `/carrinho/nome` | Identificar cliente do carrinho | não | sim | não, ação POST | implementada |
| `/vendas/historico` | Histórico de vendas atuais e antigas | não | sim | `busca`, `data_inicial`, `data_final`, `pagamento`, `situacao` | implementada |
| `/continhas` | Continhas dos clientes | não | sim | `busca` | implementada |
| `/continhas/pagamento` | Registrar pagamento de continha | não | sim | não, ação POST | implementada |
| `/continhas/<id>/excluir` | Remover continha quitada da lista | `id` | sim | não, ação POST | implementada |
| `/produtos` | Redirecionamento para Estoque | não | sim | não | implementada |
| `/estoque` | Produtos e controle de estoque | não | sim | `busca`, `inicio`, `categoria`, `fornecedor`, `estoque` | implementada |
| `/estoque/novo` | Cadastro de produto | não | sim | `codigo` | implementada |
| `/estoque/categorias/nova` | Cadastro de categoria (GET e POST) | não | sim | filtros do estoque para retorno | implementada |
| `/estoque/ler-codigo` | Localizar produto para nova entrada ou cadastro | não | sim | `codigo`, `permitir_pesquisa`, `inicio`, `categoria`, `fornecedor`, `estoque` | implementada |
| `/estoque/consultar-codigo` | Identificação local e sugestões de nome e marca (JSON) | não | sim | `codigo` | implementada |
| `/estoque/complementar-codigo` | Complemento por catálogo geral EAN (JSON) | não | sim | não, ação POST | implementada |
| `/estoque/pesquisar-codigo-web` | Sugestões por pesquisa na internet com IA (JSON) | não | sim | não, ação POST | implementada |
| `/estoque/<id>/editar` | Edição de produto | `id` | sim | não | implementada |
| `/estoque/<id>/lotes/<lote_id>/validade` | Atualização da validade de um lote | `id`, `lote_id` | sim | não, ação POST | implementada |
| `/estoque/<id>/excluir` | Exclusão lógica de produto | `id` | sim | não, ação POST | implementada |
| `/dashboard` | Indicadores e vendas recentes | não | sim | não | implementada |
| `/fornecedores` | Lista de fornecedores | não | sim | `busca`, `inicio` | implementada |
| `/fornecedores/novo` | Cadastro de fornecedor | não | sim | não | implementada |
| `/fornecedores/<id>/editar` | Edição de fornecedor | `id` | sim | não | implementada |
| `/fornecedores/<id>/excluir` | Inativação de fornecedor | `id` | sim | não, ação POST | implementada |
| `*` | Página 404 | caminho inválido | sim | não | implementada |

O sistema não possui cadastro público. A conta do proprietário é criada pelo terminal e, após o login, tem acesso completo a todas as funcionalidades.

O botão `+` ao lado do filtro de categorias em Estoque abre o cadastro de uma categoria. As opções são persistidas em `CategoriaProduto`, inclusive antes de terem produtos. A migração `produtos.0010_categoriaproduto` aproveita as categorias existentes. Os formulários de cadastro e edição de produtos usam uma lista obrigatória de categorias cadastradas, com validação no servidor. Nomes seguem a regra de iniciais maiúsculas e não podem ser duplicados. Ao adicionar uma categoria, os filtros do estoque são preservados. Sem JavaScript, o mesmo link abre o formulário em uma página própria.

O menu lateral segue a ordem: Principal, Carrinhos, Estoque, Dashboard, Fornecedores, Continhas e Vendas.

As ações de fechar carrinho ocupado, cancelar atendimento, remover produto, inativar fornecedor, encerrar/excluir lote e remover continha usam um diálogo de confirmação no visual do sistema. O aviso explica a consequência e oferece uma ação explícita; o foco começa no botão de voltar. Esc, o botão × e clicar fora cancelam, preservando os dados e devolvendo o foco. A confirmação mantém o formulário original, seus campos e o botão acionado, com apenas um envio. Carrinhos vazios e sem cliente fecham diretamente. Mensagens de sucesso e erro usam cartões com ícones, cores suaves e fechamento manual das mensagens de operação; erros não somem automaticamente.

O link Proprietário no cabeçalho abre Configurações. O nome do comércio é compartilhado pelo sistema e substitui a identificação padrão no cabeçalho, no título das páginas, na sigla lateral e na tela de login. A foto pertence ao usuário autenticado e pode ser trocada com prévia antes de salvar. São aceitos JPG, PNG e WebP de até 2 MB; o servidor identifica o formato pelo conteúdo. Nome inválido ou arquivo recusado não altera os dados anteriores. As fotos são guardadas no PostgreSQL e entregues por rota autenticada, sem cache compartilhado. Salvar somente o nome mantém a foto existente. A migração `usuarios.0001_configuracao_comercio_perfil` cria as configurações e os perfis, preservando os cadastros atuais.

A pesquisa dos carrinhos mostra um resultado por produto, com o estoque disponível somado. Ao adicionar, a quantidade é distribuída automaticamente entre os lotes disponíveis, do mais antigo para o mais novo, mantendo o preço de cada lote. A baixa no estoque ocorre ao concluir a venda.

Uma sessão nova começa com três carrinhos. O botão `+`, disponível na Página Principal e em Carrinhos, abre mais atendimentos sem limite fixo e seleciona o novo carrinho. Todos mantêm itens e cliente independentes na sessão. Na Página Principal, os cards permanecem alinhados acima dos respectivos painéis, com rolagem horizontal compartilhada quando necessário. As abas de Carrinhos também têm rolagem, mantendo o botão de abertura visível.

O botão `×` fecha qualquer carrinho, inclusive os três iniciais. Havendo itens ou cliente identificado, a interface pede confirmação antes de descartar o atendimento, sem vender nem baixar estoque. Fechar não afeta os demais carrinhos; cancelar ou concluir apenas limpa o atendimento e mantém sua posição aberta para reutilização. Se todos forem fechados, as duas telas exibem estado vazio e permitem reabrir pelo `+`. A lista aberta é persistida na sessão; números informados pela URL não criam carrinhos.

Cada lote pode ter uma data de validade opcional, informada no cadastro inicial do produto ou em uma nova entrada. Na edição do produto, a tabela de lotes permite consultar, corrigir ou limpar essa data. Lotes já existentes continuam sem validade informada; a ordem de saída e a disponibilidade para venda não são alteradas automaticamente pela validade.

O cadastro novo usa uma grade compacta de três colunas no desktop: Marca precede Categoria, Fornecedor fica abaixo de Forma de venda e Estoque mínimo abaixo de Quantidade em estoque. O botão de confirmação cabe sem rolagem nas resoluções desktop verificadas (1520 × 729, 1366 × 768 e 1280 × 720). Todos os campos e erros permanecem acessíveis; telas menores ou erros adicionais podem usar rolagem normal, sem ocultar conteúdo.

No cadastro novo, Enter avança para o próximo campo visível na ordem visual, sem enviar o formulário. No código de barras, Enter mantém a consulta do catálogo e leva ao Nome; depois o fluxo segue sem voltar ao código. Campos ocultos e desabilitados são ignorados, valores inválidos mantêm o foco para correção e o último campo leva ao botão Cadastrar produto. A confirmação continua explícita; Tab mantém o comportamento normal do navegador.

Em Continhas, a pesquisa por nome atualiza a lista automaticamente durante a digitação e mantém o filtro `busca` na URL. Limpar o campo mostra todas as contas novamente.

A lixeira permite apagar somente continhas com saldo exatamente zerado, mediante confirmação. O servidor confere o saldo em transação, com bloqueio da conta; dívidas e créditos impedem a remoção. A conta recebe `ExcluidaEm` e deixa a lista, preservando vendas e lançamentos. Contas inexistentes, removidas ou de outro proprietário retornam 404; a ação exige POST, login e CSRF e mantém a busca no retorno. Pagamentos em contas removidas são recusados. Uma nova compra na conta do mesmo cliente reabre o registro, cujo saldo anterior era zero, sem criar duplicata nem perder o histórico. Aplicar a migração `vendas.0006_contacliente_excluidaem`.

Em Estoque e Fornecedores, digitar atualiza os resultados sem botão nem recarregar a página, mantendo o foco no campo. Os formulários usam `inicio=1` para pesquisar nomes que começam com o texto, sem diferenciar acentos ou maiúsculas; Estoque também aceita o início do código de barras. Limpar o campo restaura a lista respeitando os filtros de estoque selecionados. Alterar categoria, fornecedor ou situação também atualiza automaticamente. Busca e filtros permanecem na URL; sem JavaScript, o formulário GET continua funcionando. URLs antigas sem `inicio=1` mantêm a pesquisa ampla por outros dados. O Enter do leitor continua abrindo uma entrada ou cadastro, sem baixar estoque durante a pesquisa.

A Consulta do estoque na Página Principal também atualiza enquanto se digita, com `busca` e `inicio=1` na URL. Apenas a tabela de consulta é substituída: o campo conserva o foco e os carrinhos, seus campos de pesquisa e os indicadores gerais permanecem intactos. Limpar a pesquisa restaura os produtos ativos; a consulta não inclui ações de manutenção nem altera saldos.

Em Vendas, a busca por cliente, produto ou número pode ser combinada com datas inicial e final (inclusive, no fuso local), forma de pagamento e situação atual/arquivada. Os filtros ficam na URL e também se aplicam às vendas antigas preservadas.

No carrinho e nos painéis da Página Principal, a opção PIX + dinheiro mostra primeiro recebido em dinheiro e depois valor no PIX, ambos inicialmente em branco, para permitir qualquer divisão. Ao digitar em dinheiro, o PIX é preenchido automaticamente com o valor restante; ao digitar no PIX, o dinheiro é atualizado da mesma forma. Limpar um valor também limpa o outro, e a atualização fica restrita ao carrinho editado. O valor recebido em dinheiro cobre somente o restante após o PIX; o excedente gera troco. O servidor valida os valores antes de concluir a venda ou baixar o estoque. A divisão fica disponível nos detalhes do Dashboard e do histórico, inclusive nas vendas arquivadas. Aplicar a migração `vendas.0007_pagamento_pix_dinheiro`.

A pesquisa de Vendas também atualiza durante a digitação, sem exigir o botão Filtrar. Datas, pagamento e situação atualizam ao serem alterados e continuam combinados com o termo na URL. A lista mantém a expansão dos itens após cada atualização; erros de datas são apresentados e removidos ao corrigir os campos, sem perder o foco ou recriar o formulário.

O leitor de código de barras funciona no modo teclado, com Enter ao final. O código é opcional, único por produto e preserva zeros à esquerda. Em Estoque, a barra de pesquisa também recebe o leitor: Enter sobre um código exato cadastrado abre uma nova entrada do produto; um GTIN novo (EAN/UPC de 8, 12, 13 ou 14 dígitos com dígito verificador válido) abre o cadastro com o código preenchido. Outros termos e códigos parciais continuam como pesquisa, preservando os filtros. O botão Filtrar somente pesquisa. A rota de leitura direta, sem `permitir_pesquisa=1`, continua abrindo o cadastro com qualquer código novo preenchido. Na página principal e em Carrinhos, a barra de pesquisa também recebe o leitor: Enter sobre um código exato cadastrado adiciona uma unidade ao carrinho do campo selecionado, sem recarregar a página; os demais termos continuam como pesquisa normal. O botão Pesquisar somente pesquisa, sem adicionar ao carrinho. Leituras sucessivas são processadas em fila. Produtos por peso ou metro solicitam a quantidade, e a seleção de lotes segue do mais antigo ao mais novo. Códigos desconhecidos ou produtos sem disponibilidade não entram no carrinho.

No cadastro novo vazio, o foco inicial fica no campo Código de barras para receber o leitor. O código recebido pela URL ou informado no campo inicia a identificação ao confirmar com Enter, sair do campo ou após 350 ms sem digitação em códigos numéricos completos de 8, 12, 13 ou 14 dígitos. Enter cancela o agendamento e uma consulta já em andamento para o mesmo código não é duplicada. Somente nome e marca são sugestões editáveis. Categoria, validade, fornecedor, preços e quantidade permanecem manuais. Campos editados pelo vendedor e respostas de códigos anteriores não são sobrescritos. A consulta não cria produtos nem lotes. Produtos locais, inclusive com códigos alfanuméricos, são verificados antes de qualquer consulta externa; produtos inativos não abrem nova entrada.

O fluxo verifica o produto local e depois `IdentificacaoProduto`, catálogo persistente no mesmo PostgreSQL (migração `produtos.0009_identificacaoproduto`). GTINs equivalentes com zeros de preenchimento compartilham a identificação de 14 dígitos, sem alterar o código original do produto. Sugestões externas mantêm fontes por campo e validade de 24 horas; depois precisam ser consultadas novamente. Ao confirmar o cadastro ou a edição, nome e marca revisados têm prioridade sobre futuras sugestões. Uma marca vazia confirmada também é respeitada. A atribuição dos campos mantidos é preservada. Ao salvar o cadastro ou uma identificação de produto, nome e marca recebem inicial maiúscula em cada palavra. Nenhum dado de estoque ou categoria entra nesse catálogo de identificação.

Sem identificação local completa, o GET consulta Open Food Facts (API v3.6, `product_type=all`), sem chave nem biblioteca adicional. Somente o GTIN é enviado, com User-Agent do projeto. A consulta pode redirecionar para Open Beauty Facts, Open Products Facts ou Open Pet Food Facts, com atribuição à fonte autorizada via HTTPS. Timeout de 4 segundos por conexão, resposta de até 64 KiB e espaçamento de 5 segundos por processo/cache. Quando o intervalo está ocupado, o formulário aguarda até 5 segundos e repete uma única vez, sem um ciclo infinito. O cache guarda resultados por 24 horas, ausências por 15 minutos e falhas por 30 segundos. Em vários processos, usar cache compartilhado e respeitar o limite global por IP do provedor. A atribuição e ODbL aparecem junto às sugestões. Respeitar a [licença e condições](https://openfoodfacts.github.io/documentation/docs/Product-Opener/api/tutorials/license-be-on-the-legal-side/), inclusive obrigações aplicáveis à distribuição de bases derivadas. Nenhum dado da loja é publicado.

## Pesquisa Complementar de Produtos

`CatalogoComplementar.json` mantém referências conferidas com fonte explícita. O código `7894650016091` sugere Pato Limpeza Profunda de Uso Geral Fruturistico 750ml, marca `pato`, conforme a CDA Distribuidora. Não sugere categoria e não é apresentado como dado ODbL.

Se ainda faltar nome ou marca, o formulário chama `/estoque/complementar-codigo` por POST com login e CSRF. O adaptador Cosmos consulta o GTIN exato e aceita apenas descrição e marca, ignorando preço, categoria e demais dados. Configurar `COSMOS_API_TOKEN` e `COSMOS_API_USER_AGENT` fornecidos pelo provedor; sem ambos, a etapa é pulada. Timeout de 4 segundos, resposta de até 64 KiB, sem seguir redirecionamentos com credenciais. Limites locais: uma consulta nova por segundo e `COSMOS_LIMITE_DIARIO` por dia UTC (padrão 25), por processo/cache; HTTP 429 pausa chamadas novas por 60 segundos. Resultados, ausências e falhas usam cache de 24 horas, 15 minutos e 30 segundos. Não há retentativa automática dessa etapa. Ajustar limites ao plano e conferir a [licença de cada item](https://api.cosmos.bluesoft.com.br/licenses) antes de ativar. Referência: [API Cosmos](https://api.cosmos.bluesoft.com.br/api).

Se ainda faltarem campos, o formulário pode pesquisar a internet automaticamente usando a API Responses da OpenAI com `web_search`, inclusive quando um catálogo retornou só nome ou só marca. As etapas preenchem progressivamente apenas os campos faltantes; falhas posteriores preservam as sugestões anteriores e as edições manuais. Essa integração é opcional, desativada por padrão e não instala biblioteca nova. Para ativar, configurar `OPENAI_API_KEY`, `PESQUISA_PRODUTO_IA_ATIVA=1` e, opcionalmente, `PESQUISA_PRODUTO_IA_MODELO` no `.env`, seguindo `.env.example`; reiniciar o servidor após configurar. Nunca incluir a chave no Git ou no navegador. A API tem cobrança própria e deve ter limites de gasto configurados na conta do provedor antes da ativação.

A pesquisa paga usa POST com login e CSRF, nunca o GET de consulta do catálogo. Somente o GTIN vai ao provedor, sem dados de clientes, vendas, fornecedor ou estoque. Exige pesquisa efetiva, saída estruturada, código exato, trecho de evidência contendo o código e fonte HTTPS presente entre as URLs consultadas. Não abre URLs retornadas no servidor. A correspondência do conteúdo é declarada pelo modelo, não uma validação independente da página; ainda pode haver erro, portanto os campos continuam editáveis e o vendedor confirma antes de salvar. Validade, preços e quantidade nunca são sugeridos. As fontes são mostradas como links, sem atribuir ODbL aos dados da web.

Há até três chamadas da ferramenta de busca por requisição, timeout de 30 segundos e limite de resposta de 256 KiB. O cache compartilha resultados por código/modelo por 24 horas, ausências por 15 minutos e falhas por 30 segundos. Consultas novas são espaçadas em cinco segundos e limitadas a 30 por usuário por hora, por processo/cache. A aplicação não faz retentativas automáticas de chamadas pagas. Em produção com múltiplos processos, configurar cache compartilhado e limites de gasto no provedor; os limites locais não substituem o controle de cobrança. Sem chave, com falha ou sem evidência, o cadastro manual permanece disponível.

Referências técnicas: [pesquisa na web da OpenAI](https://developers.openai.com/api/docs/guides/tools-web-search), [saída estruturada](https://developers.openai.com/api/docs/guides/structured-outputs) e [modelo configurado por padrão](https://developers.openai.com/api/docs/models/gpt-5.4-mini).

## Esboço — Página Principal

```text
┌ menu ┐┌─────────────────────────────────────────────┐
│      ││ Controle de estoque              Início Conta│
│      │├─────────────────────────────────────────────┤
│      ││ [Carrinho 1] [Carrinho 2] [Carrinho 3]      │
│      ││ [painel 1]   [painel 2]   [painel 3]        │
│      ││ [indicadores] [pesquisa de estoque]         │
│      ││ [tabela de estoque somente leitura]         │
└──────┘└─────────────────────────────────────────────┘
```

## Esboço — Carrinho de compras

```text
┌ menu ┐┌──────────────────────────────────────────────────┐
│      ││ [Carrinho 1] [Carrinho 2] [Carrinho 3]          │
│      ││ [pesquisar produto] [pesquisar]  │ itens + total │
│      ││ resultados com quantidade ou kg │ dinheiro/PIX/conta│
│      ││ [adicionar]                     │ troco         │
│      ││                                 │ cancelar/concluir│
└──────┘└──────────────────────────────────────────────────┘
```

## Esboço — Histórico de vendas

```text
┌ menu ┐┌─────────────────────────────────────────────┐
│      ││ Histórico de vendas       [abrir atendimento]│
│      ││ [busca por cliente, produto ou número]      │
│      ││ [data inicial] [data final]                 │
│      ││ [pagamento] [situação] [filtrar] [limpar]   │
│      ││ tabela: venda | data | cliente | total      │
│      ││ linhas expandem para itens cobrados         │
└──────┘└─────────────────────────────────────────────┘
```

## Esboço — Continhas dos clientes

```text
┌ menu ┐┌─────────────────────────────────────────────┐
│      ││ Continhas dos clientes                     │
│      ││ [busca por cliente]                         │
│      ││ cliente | saldo | últimos lançamentos       │
│      ││ [valor recebido] [observação] [registrar]   │
└──────┘└─────────────────────────────────────────────┘
```

## Esboço — Estoque

```text
┌ menu ┐┌─────────────────────────────────────────────┐
│      ││ Estoque                    [adicionar produto]│
│      ││ [busca] [categoria] [fornecedor] [situação]  │
│      ││ [produtos] [disponíveis] [estoque baixo]    │
│      ││ tabela: produto | marca | fornecedor | ações │
└──────┘└─────────────────────────────────────────────┘
```

## Esboço — Fornecedores

```text
┌ menu ┐┌─────────────────────────────────────────────┐
│      ││ Fornecedores          [adicionar fornecedor]│
│      ││ [pesquisa pelo início do nome]              │
│      ││ tabela: fornecedor | contato | produtos     │
└──────┘└─────────────────────────────────────────────┘
```

## Esboço — Dashboard

```text
┌ menu ┐┌─────────────────────────────────────────────┐
│      ││ Dashboard                                   │
│      ││ [produtos] [produtos em alerta] [vendas hoje]│
│      ││ tabela de vendas recentes                   │
└──────┘└─────────────────────────────────────────────┘
```
