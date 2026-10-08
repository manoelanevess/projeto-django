# Mapa de rotas

As URLs usam substantivos no plural, letras minúsculas e hífen quando necessário. Filtros e buscas ficam na query string.

| rota | tela | parâmetro | protegida | query string | status |
| --- | --- | --- | --- | --- | --- |
| `/` | Página Principal | não | sim | não | implementada |
| `/login` | Login | não | não | não | implementada |
| `/logout` | Encerramento da sessão | não | sim | não | implementada |
| `/carrinho` | Carrinho de compras | não | sim | `carrinho`, `busca` | implementada |
| `/carrinho/pesquisar` | Pesquisa incremental de produtos no carrinho | não | sim | `busca` | implementada |
| `/carrinho/adicionar` | Adicionar item | não | sim | não, ação POST | implementada |
| `/carrinho/remover` | Remover item | não | sim | não, ação POST | implementada |
| `/carrinho/cancelar` | Cancelar atendimento | não | sim | não, ação POST | implementada |
| `/carrinho/concluir` | Concluir venda | não | sim | não, ação POST | implementada |
| `/carrinho/nome` | Identificar cliente do carrinho | não | sim | não, ação POST | implementada |
| `/vendas/historico` | Histórico de vendas atuais e antigas | não | sim | `busca` | implementada |
| `/continhas` | Continhas dos clientes | não | sim | `busca` | implementada |
| `/continhas/pagamento` | Registrar pagamento de continha | não | sim | não, ação POST | implementada |
| `/produtos` | Redirecionamento para Estoque | não | sim | não | implementada |
| `/estoque` | Produtos e controle de estoque | não | sim | `busca`, `categoria`, `fornecedor`, `estoque` | implementada |
| `/estoque/novo` | Cadastro de produto | não | sim | não | implementada |
| `/estoque/<id>/editar` | Edição de produto | `id` | sim | não | implementada |
| `/estoque/<id>/excluir` | Exclusão lógica de produto | `id` | sim | não, ação POST | implementada |
| `/dashboard` | Indicadores e vendas recentes | não | sim | não | implementada |
| `/fornecedores` | Lista de fornecedores | não | sim | `busca` | implementada |
| `/fornecedores/novo` | Cadastro de fornecedor | não | sim | não | implementada |
| `/fornecedores/<id>/editar` | Edição de fornecedor | `id` | sim | não | implementada |
| `/fornecedores/<id>/excluir` | Inativação de fornecedor | `id` | sim | não, ação POST | implementada |
| `*` | Página 404 | caminho inválido | sim | não | implementada |

O sistema não possui cadastro público. A conta do proprietário é criada pelo terminal e, após o login, tem acesso completo a todas as funcionalidades.

O menu lateral segue a ordem: Principal, Carrinhos, Estoque, Dashboard, Fornecedores, Continhas e Vendas.

A pesquisa dos carrinhos mostra um resultado por produto, com o estoque disponível somado. Ao adicionar, a quantidade é distribuída automaticamente entre os lotes disponíveis, do mais antigo para o mais novo, mantendo o preço de cada lote. A baixa no estoque ocorre ao concluir a venda.

Em Continhas, a pesquisa por nome atualiza a lista automaticamente durante a digitação e mantém o filtro `busca` na URL. Limpar o campo mostra todas as contas novamente.

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
│      ││ tabela: venda | data | cliente | total      │
│      ││ linhas expandem para itens cobrados         │
└──────┘└─────────────────────────────────────────────┘
```

## Esboço — Continhas dos clientes

```text
┌ menu ┐┌─────────────────────────────────────────────┐
│      ││ Continhas dos clientes    [abrir atendimento]│
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
│      ││ [pesquisa por nome, contato ou cidade]      │
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
