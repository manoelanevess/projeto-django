# Mapa de rotas

As URLs usam substantivos no plural, letras minúsculas e hífen quando necessário. Filtros e buscas ficam na query string.

| rota | tela | parâmetro | protegida | query string | status |
| --- | --- | --- | --- | --- | --- |
| `/` | Página Principal | não | sim | `busca`, `inicio`, `carrinho`, `busca_carrinho`, `carrinhos_abertos` | implementada |
| `/login` | Login | não | não | não | implementada |
| `/logout` | Encerramento da sessão | não | sim | não | implementada |
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
| `/produtos` | Redirecionamento para Estoque | não | sim | não | implementada |
| `/estoque` | Produtos e controle de estoque | não | sim | `busca`, `inicio`, `categoria`, `fornecedor`, `estoque` | implementada |
| `/estoque/novo` | Cadastro de produto | não | sim | `codigo` | implementada |
| `/estoque/ler-codigo` | Localizar produto para nova entrada ou cadastro | não | sim | `codigo`, `permitir_pesquisa`, `inicio`, `categoria`, `fornecedor`, `estoque` | implementada |
| `/estoque/consultar-codigo` | Sugestões de nome, marca e categoria (JSON) | não | sim | `codigo` | implementada |
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

O menu lateral segue a ordem: Principal, Carrinhos, Estoque, Dashboard, Fornecedores, Continhas e Vendas.

A pesquisa dos carrinhos mostra um resultado por produto, com o estoque disponível somado. Ao adicionar, a quantidade é distribuída automaticamente entre os lotes disponíveis, do mais antigo para o mais novo, mantendo o preço de cada lote. A baixa no estoque ocorre ao concluir a venda.

Uma sessão nova começa com três carrinhos. O botão `+`, disponível na Página Principal e em Carrinhos, abre mais atendimentos sem limite fixo e seleciona o novo carrinho. Todos mantêm itens e cliente independentes na sessão. Na Página Principal, os cards permanecem alinhados acima dos respectivos painéis, com rolagem horizontal compartilhada quando necessário. As abas de Carrinhos também têm rolagem, mantendo o botão de abertura visível.

O botão `×` fecha qualquer carrinho, inclusive os três iniciais. Havendo itens ou cliente identificado, a interface pede confirmação antes de descartar o atendimento, sem vender nem baixar estoque. Fechar não afeta os demais carrinhos; cancelar ou concluir apenas limpa o atendimento e mantém sua posição aberta para reutilização. Se todos forem fechados, as duas telas exibem estado vazio e permitem reabrir pelo `+`. A lista aberta é persistida na sessão; números informados pela URL não criam carrinhos.

Cada lote pode ter uma data de validade opcional, informada no cadastro inicial do produto ou em uma nova entrada. Na edição do produto, a tabela de lotes permite consultar, corrigir ou limpar essa data. Lotes já existentes continuam sem validade informada; a ordem de saída e a disponibilidade para venda não são alteradas automaticamente pela validade.

O cadastro novo usa uma grade compacta de três colunas no desktop: Marca precede Categoria, Fornecedor fica abaixo de Forma de venda e Estoque mínimo abaixo de Quantidade em estoque. O botão de confirmação cabe sem rolagem nas resoluções desktop verificadas (1520 × 729, 1366 × 768 e 1280 × 720). Todos os campos e erros permanecem acessíveis; telas menores ou erros adicionais podem usar rolagem normal, sem ocultar conteúdo.

No cadastro novo, Enter avança para o próximo campo visível na ordem visual, sem enviar o formulário. No código de barras, Enter mantém a consulta do catálogo e leva ao Nome; depois o fluxo segue sem voltar ao código. Campos ocultos e desabilitados são ignorados, valores inválidos mantêm o foco para correção e o último campo leva ao botão Cadastrar produto. A confirmação continua explícita; Tab mantém o comportamento normal do navegador.

Em Continhas, a pesquisa por nome atualiza a lista automaticamente durante a digitação e mantém o filtro `busca` na URL. Limpar o campo mostra todas as contas novamente.

Em Estoque e Fornecedores, digitar atualiza os resultados sem botão nem recarregar a página, mantendo o foco no campo. Os formulários usam `inicio=1` para pesquisar nomes que começam com o texto, sem diferenciar acentos ou maiúsculas; Estoque também aceita o início do código de barras. Limpar o campo restaura a lista respeitando os filtros de estoque selecionados. Alterar categoria, fornecedor ou situação também atualiza automaticamente. Busca e filtros permanecem na URL; sem JavaScript, o formulário GET continua funcionando. URLs antigas sem `inicio=1` mantêm a pesquisa ampla por outros dados. O Enter do leitor continua abrindo uma entrada ou cadastro, sem baixar estoque durante a pesquisa.

A Consulta do estoque na Página Principal também atualiza enquanto se digita, com `busca` e `inicio=1` na URL. Apenas a tabela de consulta é substituída: o campo conserva o foco e os carrinhos, seus campos de pesquisa e os indicadores gerais permanecem intactos. Limpar a pesquisa restaura os produtos ativos; a consulta não inclui ações de manutenção nem altera saldos.

Em Vendas, a busca por cliente, produto ou número pode ser combinada com datas inicial e final (inclusive, no fuso local), forma de pagamento e situação atual/arquivada. Os filtros ficam na URL e também se aplicam às vendas antigas preservadas.

A pesquisa de Vendas também atualiza durante a digitação, sem exigir o botão Filtrar. Datas, pagamento e situação atualizam ao serem alterados e continuam combinados com o termo na URL. A lista mantém a expansão dos itens após cada atualização; erros de datas são apresentados e removidos ao corrigir os campos, sem perder o foco ou recriar o formulário.

O leitor de código de barras funciona no modo teclado, com Enter ao final. O código é opcional, único por produto e preserva zeros à esquerda. Em Estoque, a barra de pesquisa também recebe o leitor: Enter sobre um código exato cadastrado abre uma nova entrada do produto; um GTIN novo (EAN/UPC de 8, 12, 13 ou 14 dígitos com dígito verificador válido) abre o cadastro com o código preenchido. Outros termos e códigos parciais continuam como pesquisa, preservando os filtros. O botão Filtrar somente pesquisa. A rota de leitura direta, sem `permitir_pesquisa=1`, continua abrindo o cadastro com qualquer código novo preenchido. Na página principal e em Carrinhos, a barra de pesquisa também recebe o leitor: Enter sobre um código exato cadastrado adiciona uma unidade ao carrinho do campo selecionado, sem recarregar a página; os demais termos continuam como pesquisa normal. O botão Pesquisar somente pesquisa, sem adicionar ao carrinho. Leituras sucessivas são processadas em fila. Produtos por peso ou metro solicitam a quantidade, e a seleção de lotes segue do mais antigo ao mais novo. Códigos desconhecidos ou produtos sem disponibilidade não entram no carrinho.

No cadastro novo vazio, o foco inicial fica no campo Código de barras para receber o leitor. O código recebido pela URL ou informado no campo consulta a família Open Food Facts (API v3.6, `product_type=all`) ao confirmar com Enter, sair do campo ou após 350 ms sem digitação em códigos numéricos completos de 8, 12, 13 ou 14 dígitos. Enter cancela o agendamento e uma consulta já em andamento para o mesmo código não é duplicada. Nome, marca e categoria, quando disponíveis, são sugestões editáveis. Campos preenchidos manualmente e respostas de códigos anteriores não são sobrescritos. O vendedor informa validade, fornecedor, preços, quantidade e confirma o cadastro; a consulta não cria produtos nem lotes. Códigos internos, produtos ausentes, respostas incompletas e falhas de rede mantêm o cadastro manual. Produtos locais, inclusive com códigos alfanuméricos, são verificados antes de qualquer consulta externa; produtos inativos não abrem nova entrada.

As sugestões de alimentos, perecíveis ou não, usam a categoria `Alimentos`, inclusive quando o registro alimentício não traz uma categoria específica. Produtos de higiene/cosméticos e medicamentos reconhecidos usam `Farmácia`; ferramentas e ferragens reconhecidas usam `Ferragem`. O tipo do produto e as categorias retornadas pelo catálogo orientam a classificação; na ausência de categorias, o nome pode identificar termos claros de farmácia ou ferragem. Produtos genéricos ou classificações ambíguas não recebem uma categoria inventada. As marcas sugeridas são convertidas para minúsculas; o nome do produto é preservado. As regras se aplicam somente ao preenchimento automático: não alteram cadastros existentes nem valores digitados manualmente. A cobertura depende dos dados disponíveis nos catálogos públicos e não garante identificação de todos os medicamentos ou itens de ferragem.

A integração não exige chave nem biblioteca adicional. Somente o GTIN é enviado ao catálogo, com User-Agent identificando o projeto; nenhum dado de vendas, clientes, fornecedor ou estoque é enviado. A consulta universal pode redirecionar para Open Beauty Facts, Open Products Facts ou Open Pet Food Facts, e o tipo e a atribuição são identificados pela resposta do catálogo autorizado via HTTPS. As consultas têm timeout de 4 segundos por conexão, limite de resposta de 64 KiB e espaçamento de 5 segundos por processo/cache. O cache padrão do Django guarda resultados por 24 horas, ausências por 15 minutos e falhas por 30 segundos; a versão do cache foi atualizada para não reutilizar sugestões antigas de marca/categoria. Em implantação com vários processos, usar cache compartilhado e revisar o limite global de requisições por IP do provedor. A atribuição ao catálogo de origem e ODbL aparece junto às sugestões. A reutilização dos dados deve respeitar a [licença e condições do catálogo](https://openfoodfacts.github.io/documentation/docs/Product-Opener/api/tutorials/license-be-on-the-legal-side/), incluindo as obrigações aplicáveis à distribuição de bases derivadas; esta integração é somente leitura, sem publicar dados da loja.

## Pesquisa Complementar de Produtos

Produtos de limpeza reconhecidos usam a categoria `Limpeza`; higiene pessoal continua em `Farmácia`. `CatalogoComplementar.json` mantém referências conferidas, com fonte explícita, para complementar os catálogos públicos. O código `7894650016091` sugere Pato Limpeza Profunda de Uso Geral Fruturistico 750ml, marca `pato`, categoria `Limpeza`, conforme a CDA Distribuidora. Essa referência não cria produto ou lote e não é apresentada como dado ODbL.

Quando o estoque e os catálogos não identificam o código, o formulário pode pesquisar a internet automaticamente usando a API Responses da OpenAI com `web_search`. Essa integração é opcional, desativada por padrão e não instala biblioteca nova. Para ativar, configurar `OPENAI_API_KEY`, `PESQUISA_PRODUTO_IA_ATIVA=1` e, opcionalmente, `PESQUISA_PRODUTO_IA_MODELO` no `.env`, seguindo `.env.example`; reiniciar o servidor após configurar. Nunca incluir a chave no Git ou no navegador. A API tem cobrança própria e deve ter limites de gasto configurados na conta do provedor antes da ativação.

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
