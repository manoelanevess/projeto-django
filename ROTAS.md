# Mapa de rotas

As URLs usam substantivos no plural, letras minúsculas e hífen quando necessário. Filtros e buscas ficam na query string.

| rota | tela | parâmetro | protegida | query string | status |
| --- | --- | --- | --- | --- | --- |
| `/` | Dashboard | não | sim | não | implementada |
| `/login` | Login | não | não | não | implementada |
| `/logout` | Encerramento da sessão | não | sim | não | implementada |
| `/produtos` | Lista de produtos | não | sim | `busca`, `estoque` | implementada |
| `/produtos/novo` | Cadastro de produto | não | sim | não | planejada |
| `/produtos/<id>` | Detalhe do produto | `id` | sim | não | planejada |
| `/estoque` | Controle de estoque | não | sim | `status`, `produto` | implementada |
| `/fornecedores` | Lista de fornecedores | não | sim | `busca` | implementada |
| `*` | Página 404 | caminho inválido | sim | não | implementada |

O sistema não possui cadastro público. A conta do proprietário é criada pelo terminal e, após o login, tem acesso completo a todas as funcionalidades.

## Esboço — Dashboard

```text
┌ menu ┐┌─────────────────────────────────────────────┐
│      ││ Estoque Nuvem                    Início Conta│
│      │├─────────────────────────────────────────────┤
│      ││ Dashboard                                   │
│      ││ [estoque baixo] [qtd estoque] [custo total] │
│      ││ Atalhos                                     │
│      ││ [Produtos] [Estoque] [Fornecedores]         │
└──────┘└─────────────────────────────────────────────┘
```

## Esboço — Produtos

```text
┌ menu ┐┌─────────────────────────────────────────────┐
│      ││ Produtos                                    │
│      ││ [busca por nome/categoria] [estoque] [filtrar]│
│      ││ [produtos encontrados] [itens] [estoque baixo]│
│      ││ tabela: produto | categoria | qtd | mínimo  │
└──────┘└─────────────────────────────────────────────┘
```

## Esboço — Estoque

```text
┌ menu ┐┌─────────────────────────────────────────────┐
│      ││ Estoque                                     │
│      ││ [total itens] [produtos em alerta] [mov hoje]│
│      ││ lista futura de entradas e saídas           │
└──────┘└─────────────────────────────────────────────┘
```
