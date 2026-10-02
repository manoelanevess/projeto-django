# Mapa de rotas

As URLs usam substantivos no plural, letras minúsculas e hífen quando necessário. Filtros e buscas ficam na query string.

| rota | tela | parâmetro | protegida | query string | status |
| --- | --- | --- | --- | --- | --- |
| `/` | Página Principal | não | sim | não | implementada |
| `/login` | Login | não | não | não | implementada |
| `/logout` | Encerramento da sessão | não | sim | não | implementada |
| `/carrinho` | Carrinho de compras | não | sim | `carrinho`, `busca` | implementada |
| `/carrinho/adicionar` | Adicionar item | não | sim | não, ação POST | implementada |
| `/carrinho/remover` | Remover item | não | sim | não, ação POST | implementada |
| `/carrinho/cancelar` | Cancelar atendimento | não | sim | não, ação POST | implementada |
| `/carrinho/concluir` | Concluir venda | não | sim | não, ação POST | implementada |
| `/carrinho/nome` | Identificar cliente do carrinho | não | sim | não, ação POST | implementada |
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

## Esboço — Página Principal

```text
┌ menu ┐┌─────────────────────────────────────────────┐
│      ││ Estoque Nuvem                    Início Conta│
│      │├─────────────────────────────────────────────┤
│      ││ Página Principal                            │
│      ││ [Carrinho 1] [Carrinho 2] [Carrinho 3]      │
│      ││ [painéis expansíveis dos carrinhos]         │
│      ││ [indicadores] [pesquisa de estoque]         │
│      ││ [tabela de estoque somente leitura]         │
└──────┘└─────────────────────────────────────────────┘
```

## Esboço — Carrinho de compras

```text
┌ menu ┐┌──────────────────────────────────────────────────┐
│      ││ [Carrinho 1] [Carrinho 2] [Carrinho 3]          │
│      ││ [pesquisar produto] [pesquisar]  │ itens + total │
│      ││ resultados com quantidade ou kg │ dinheiro/PIX  │
│      ││ [adicionar]                     │ troco         │
│      ││                                 │ cancelar/concluir│
└──────┘└──────────────────────────────────────────────────┘
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
