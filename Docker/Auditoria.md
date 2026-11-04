# Auditoria Docker

Registro da dockerização inicial. As linhas e os tamanhos abaixo referem-se àquela versão, anterior ao estágio `testes` e à compressão HTTP. Os resultados atuais estão em `TESTES.md` e `PERFORMANCE.md`.

Verificação realizada em 04/11/2026, seguindo os itens da aula e adaptando-os ao Django MPA com PostgreSQL. Os exemplos de Node/SQLite/SPA dos slides não se aplicam à arquitetura deste trabalho. O contexto de build é único e fica na raiz, compartilhando `Dockerfile` e `.dockerignore` entre aplicação e proxy.

## Itens da revisão

| Item dos slides | Resultado | Evidência |
| --- | --- | --- |
| Segredos e banco fora da imagem | OK | `.dockerignore:5` exclui `.env*`; linhas 14 a 19 excluem bancos e backups. `Dockerfile:14`, `Dockerfile:31` e `Dockerfile:48` copiam somente requisitos, código e inicialização. A inspeção da aplicação em produção não encontrou `.env*` nem backups em `/app`. Credenciais entram por `env_file` em `compose.prod.yaml:22`. |
| `.dockerignore` para cada contexto de build | OK | Os dois serviços usam o contexto da raiz (`compose.prod.yaml:20` e `compose.prod.yaml:47`), protegido pelo mesmo `.dockerignore`. Git, ambientes virtuais, caches e `node_modules` ficam fora. |
| Cache de dependências antes do código | OK | `Dockerfile:14` instala os requisitos antes das cópias de `src`, nas linhas 19 e 32. A construção da imagem dev reutilizou as camadas de dependências. |
| Produção sem root | OK | `Dockerfile:49` usa `estoque` e `Dockerfile:58` usa `nginx`. Confirmados UIDs 10001 e 101 em execução. O entrypoint oficial do PostgreSQL inicializa o volume e entrega o servidor ao usuário `postgres`. |
| Imagem final com somente o necessário | OK | `Dockerfile:45` copia o ambiente Python do build e a linha 47 copia o código necessário ao Django. `Dockerfile:34` remove os testes desse código antes da cópia. O Nginx recebe somente configuração e estáticos coletados (`Dockerfile:56`). Nenhum compilador foi instalado. Django precisa de código Python em execução, ao contrário de um frontend SPA estático. |
| Versões explícitas, sem `latest` | OK | Python `3.13.18-slim-bookworm` (`Dockerfile:1` e `Dockerfile:37`), Nginx `1.30.6-alpine` (`Dockerfile:55`) e PostgreSQL `18.6-alpine` (`compose.prod.yaml:5`). Gunicorn `26.2.0` em `Docker/RequisitosProducao.txt:2`. |
| Persistência depois de `down` | OK | Volume nomeado em `compose.yaml:8` e `compose.prod.yaml:8`. Desenvolvimento e produção possuem nomes de projeto diferentes. Testado cadastro e login antes e depois de `down`/`up` em ambos, sem `-v`. |

Não foram encontrados problemas graves na revisão. Os Composes validaram sem a chave obsoleta `version`.

## Tamanhos medidos

Tamanho lógico obtido com `docker image inspect --format '{{.Size}}'`; MB decimal (1 MB = 1.000.000 bytes). Os tamanhos em disco e de transferência podem diferir por compressão, camadas compartilhadas e metadados. Como a auditoria não exigiu correções nas imagens, os tamanhos antes e depois são iguais.

| Imagem | Antes da auditoria | Após a auditoria | Bytes |
| --- | ---: | ---: | ---: |
| `controle-estoque-app:dev` | 293,53 MB | 293,53 MB | 293528631 |
| `controle-estoque-app:prod` | 296,09 MB | 296,09 MB | 296092312 |
| `controle-estoque-web:prod` | 94,92 MB | 94,92 MB | 94924696 |
| `postgres:18.6-alpine` | 432,74 MB | 432,74 MB | 432741923 |

A aplicação prod é ligeiramente maior que dev porque inclui Gunicorn. A maior imagem geral é o PostgreSQL, já baseado em Alpine; reduzi-la exigiria avaliar uma imagem personalizada com menos ferramentas, acrescentando manutenção ao banco. Para reduzir a maior imagem construída pelo projeto (`app:prod`), uma próxima avaliação pode remover ferramentas de instalação, como pip, do ambiente final e medir o ganho. Essas otimizações adicionais não foram aplicadas: o trabalho já usa Python slim, instalação sem cache e estágios separados, com dependências fixadas.

## Validações executadas

- Construção dos estágios `dev`, `prod` e `web-prod` a partir do ambiente Docker existente, sem Python ou PostgreSQL do Windows dentro dos contêineres.
- Inicialização com volumes novos e aplicação automática de todas as migrations.
- 242 testes Django aprovados no contêiner dev, com banco PostgreSQL de teste separado, em 48,489 segundos.
- Login HTTP real com CSRF e sessão, cadastro de fornecedor e leitura dos dados após recriar os contêineres, nos dois ambientes.
- Acesso direto e requisição repetida (equivalente ao F5 no servidor) em `/estoque`, `/dashboard`, `/fornecedores`, `/carrinho`, `/vendas/historico`, `/configuracoes` e `/continhas`.
- Arquivos estáticos do admin entregues no dev e pelo Nginx na produção.
- Recarga automática comprovada nos logs: `/app/src/configuracao/ComponenteSaude.py changed, reloading.`, usando `StatReloader`.
- `GET /health` retornando 200 com banco disponível, 503 com PostgreSQL parado e recuperação para 200 ao reiniciá-lo; POST com CSRF válido retorna 405.
- Backup `pg_dump` em formato custom, cópia sem redirecionamento binário do PowerShell e restauração transacional em outro banco temporário; conferido o fornecedor restaurado.
- O script de preparação cria segredos aleatórios, preserva um `.env.docker` existente e não modifica `.env`. `.env.docker` está ignorado pelo Git; somente o exemplo sem segredos é versionável.

Os testes utilizaram somente dados temporários nos volumes Docker. O banco atual do comércio não foi importado nem alterado. A porta dev 8000 estava ocupada e a validação usou `PORTA_DESENVOLVIMENTO=8001`; a produção foi validada em `localhost:8080`.

## Limite desta configuração

`compose.prod.yaml` é a simulação de produção **local por HTTP** solicitada na aula. Publicação na internet exige domínio, HTTPS e ajuste de cookies seguros, redirecionamento e HSTS, conforme o README. A importação dos dados reais deve ser uma operação separada, a partir de backup conferido e volume novo.

Referências técnicas: [build em múltiplos estágios](https://docs.docker.com/build/building/multi-stage/), [ordem de inicialização e healthchecks](https://docs.docker.com/compose/how-tos/startup-order/), [volume da imagem PostgreSQL 18](https://github.com/docker-library/docs/blob/master/postgres/README.md#pgdata) e [Gunicorn com proxy](https://gunicorn.org/deploy/).
