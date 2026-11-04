# Performance e diagnóstico

Medições da aula realizadas em 04/11/2026, usando o ambiente Django de produção e Lighthouse 13.6.0.

## Condições da medição

- Página principal `/`, com login válido e três carrinhos inicialmente vazios; 60 produtos sintéticos, uma categoria e um fornecedor.
- Docker/Gunicorn/Nginx com `DEBUG=0`, mesma máquina Windows e mesmo banco sintético antes/depois.
- A produção do usuário já estava em `localhost:8080`. Para manter seus dados e sua sessão, foi criada uma cópia com `-p estoque-diagnostico`, porta `127.0.0.1:8082`, usando `compose.prod.yaml` e `Testes/ComposeDiagnostico.yaml`. O modo de execução continua sendo produção, sem volumes de código.
- Chrome 155.0.8059.79 headless, perfil temporário sem extensões, viewport celular 412×823, DPR 1,75 e simulação padrão Lighthouse: RTT de 150 ms, 1638,4 Kbps e CPU 4×.
- Três rodadas válidas antes e três depois, com cache do navegador limpo e cookies preservados somente para manter o login. As medições conferem que a URL final continua `/`, evitando medir o login por engano.
- A primeira tentativa de captura falhou com `NO_NAVSTART` e foi descartada por não produzir métricas válidas. O script passou a fornecer explicitamente a aba autenticada ao Lighthouse; as seis rodadas válidas usaram essa mesma configuração.

## Resultado antes e depois

Foi aplicada uma melhoria: `django.middleware.gzip.GZipMiddleware` após `SecurityMiddleware`, em `src/configuracao/settings.py`. O HTML tem CSS e JavaScript inline e representava praticamente todo o peso transferido. A compressão reduz esse transporte sem alterar o HTML que o navegador recebe após descomprimir. Foi usada a implementação nativa do Django, incluindo seu preenchimento aleatório de proteção HTB, sem biblioteca adicional de produção.

| Métrica | Antes — mediana de 3 | Depois — mediana de 3 |
| --- | ---: | ---: |
| Nota Lighthouse | 100 | 100 |
| FCP | 1,461 s | 1,065 s |
| LCP | 1,461 s | 1,065 s |
| TBT | 0 ms | 5 ms |
| CLS | 0 | 0,00575 |
| Transferência total da página | 132867 bytes | 19518 bytes |

Nesta amostra, FCP/LCP diminuíram **27,10%** e a transferência diminuiu **85,31%**. A nota já estava no máximo; o ganho aparece no tempo e nos bytes. TBT e CLS variaram para cima, mas permaneceram na faixa boa dos slides (TBT ≤ 200 ms e CLS ≤ 0,1). Três rodadas não permitem atribuir toda variação pequena à compressão.

| Etapa | Rodada | Nota | FCP (ms) | LCP (ms) | TBT (ms) | CLS | Bytes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Antes | 1 | 100 | 1418,64 | 1418,64 | 0 | 0 | 132867 |
| Antes | 2 | 100 | 1526,12 | 1526,12 | 0 | 0 | 132867 |
| Antes | 3 | 100 | 1461,24 | 1461,24 | 0 | 0 | 132867 |
| Depois | 1 | 100 | 1219,08 | 1219,08 | 36 | 0 | 19527 |
| Depois | 2 | 100 | 1065,20 | 1065,20 | 5 | 0,00575 | 19518 |
| Depois | 3 | 100 | 1039,83 | 1039,83 | 0,5 | 0,00575 | 19481 |

As medianas são calculadas por métrica; a rodada central de LCP foi a 3 antes e a 2 depois. Os valores não são médias nem seleção da melhor execução.

## Diagnóstico e prioridades

Nenhuma métrica medida ficou fora da faixa boa dos slides. O relatório inicial apontou economia potencial de aproximadamente 87 KiB na resposta do documento, além de CSS e JavaScript não minificados (cerca de 10 KiB cada). Não há imagem principal, fonte web ou grande biblioteca frontend a substituir nesta página.

| Prioridade | Mudança | Métrica e motivo | Arquivos e risco | Situação |
| --- | --- | --- | --- | --- |
| 1 | Comprimir HTML com gzip nativo | Menos bytes na resposta principal; favorece FCP/LCP em rede lenta | `src/configuracao/settings.py`; risco de negociação HTTP/CSRF, coberto por `test_compressao.py` | Aplicada e medida |
| 2 | Extrair CSS/JS compartilhados para estáticos versionados | Reduz repetição entre páginas e permite cache; favorece FCP/LCP em navegações seguintes | `src/componentes/*`, componentes das features e configuração de estáticos; risco médio sobre seletores e ordem dos scripts | Sugestão futura, sem alteração nesta tarefa |
| 3 | Minificar os estáticos depois da extração | Reduz bytes de CSS/JS e trabalho de parse, com possível efeito em FCP/TBT | Mesmos componentes e processo de build; risco médio sobre scripts inline e mensagens | Sugestão futura, sem acrescentar uma cadeia de build agora |

Proteções: os 244 testes passaram após a compressão, incluindo descompressão do HTML, login com CSRF, `Vary`, sessão e cliente sem gzip. O fluxo no Chromium foi aprovado duas vezes com cadastro mascarado, F5, busca incremental e falha de rede simulada. Conferência manual recomendada no notebook de destino: digitação rápida, leitura por código de barras e operação com os periféricos usados no comércio.

## Reproduzir e consultar os relatórios

Com `.env.docker` já preparado, Docker Desktop e Node 22+:

```powershell
docker compose -p estoque-diagnostico -f compose.prod.yaml -f Testes/ComposeDiagnostico.yaml up --build -d --wait
node Testes/PrepararDiagnostico.mjs
npm.cmd ci --prefix Testes
node Testes/MedirPerformance.mjs Depois
node Testes/FluxoNavegador.mjs
docker compose -p estoque-diagnostico -f compose.prod.yaml -f Testes/ComposeDiagnostico.yaml down
```

Os scripts usam Chrome no caminho padrão do Windows; para outro caminho, defina `CHROME_PATH`. `PASTA_FERRAMENTAS` permite usar uma instalação externa do Lighthouse; nesta execução as ferramentas foram instaladas em pasta temporária separada, sem `node_modules` na aplicação.

`MedirPerformance.mjs Antes` serve para coletar uma linha de base **antes de aplicar uma alteração**. O código atual já contém gzip. Para reconstruir o antes histórico, a única diferença funcional foi a ausência da linha `django.middleware.gzip.GZipMiddleware`; use uma cópia de diagnóstico apropriada e reconstrua a imagem, mantendo todos os demais dados e condições. Não renomeie uma execução do código otimizado como se fosse a linha de base histórica.

Relatórios HTML/JSON completos ficam em `relatorios/lighthouse/Antes-1.*` a `Antes-3.*` e `Depois-1.*` a `Depois-3.*`. Resumos em `Antes-Resumo.json` e `Depois-Resumo.json`. A pasta é local e ignorada pelo Git. Capturas e resultado do navegador ficam em `relatorios/navegador/`.

Estes são dados de laboratório local, não dados de usuários reais nem garantia de desempenho na VPS ou no notebook antigo. O Lighthouse de navegação não mediu INP; TBT não é INP. Não há base CrUX/p75 de 28 dias para este localhost. PageSpeed Insights e GTmetrix precisam de URL pública e ficam para depois do deploy.

Referências: [métricas e nota Lighthouse](https://developer.chrome.com/docs/lighthouse/performance/performance-scoring), [autenticação na medição](https://github.com/GoogleChrome/lighthouse/blob/main/docs/authenticated-pages.md) e [gzip nativo do Django](https://docs.djangoproject.com/en/6.1/ref/middleware/#module-django.middleware.gzip).
