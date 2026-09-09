# Mapa de rotas

As URLs usam substantivos no plural, letras minúsculas e hífen quando necessário. Filtros e buscas ficam na query string.

| rota | tela | parâmetro | protegida | query string | status |
| --- | --- | --- | --- | --- | --- |
| `/` | Dashboard | não | sim | não | implementada |
| `/login` | Login | não | não | não | implementada |
| `/produtos` | Lista de produtos | não | sim | `busca`, `estoque` | implementada |
| `/produtos/novo` | Cadastro de produto | não | sim | não | planejada |
| `/produtos/<id>` | Detalhe do produto | `id` | sim | não | planejada |
| `/estoque` | Controle de estoque | não | sim | `status`, `produto` | implementada |
| `/fornecedores` | Lista de fornecedores | não | sim | `busca` | implementada |
| `*` | Página 404 | caminho inválido | não | não | implementada |

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
