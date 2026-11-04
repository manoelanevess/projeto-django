# Plano de testes

Plano da aula **Testes, Performance e Diagnóstico**, adaptado ao Django 6.1.1 com PostgreSQL. O projeto é uma MPA: rotas, formulários e HTML são testados com `django.test`, sem criar frontend React nem API Express. Testes existentes serão reaproveitados e novas verificações serão adicionadas somente para lacunas relevantes.

## Funcionalidades críticas

| Funcionalidade | Caminho feliz | Erro esperado | Caso de borda | Tipo e ferramentas |
| --- | --- | --- | --- | --- |
| Autenticação e proteção das telas | Login válido abre a página principal; logout bloqueia acesso | Senha incorreta exibe erro; POST sem CSRF é recusado | Visitante em rota protegida vai para `/login`; sessão termina ao sair | Integração e HTML com `TestCase`/`Client`; navegador no fluxo principal |
| Cadastro de produtos, lotes e fornecedores | Cadastra com categoria e fornecedor existentes e preserva valores monetários | Categoria inventada, código duplicado ou preço inválido não salva | Código com zeros à esquerda; produto por peso sem quantidade exata; lista vazia | Integração PostgreSQL e formulários Django; HTML por rótulos e conteúdo visível |
| Carrinhos, pagamento e baixa do estoque | Conclui compra em dinheiro/PIX/misto, registra valores e baixa uma vez | Estoque ou pagamento insuficiente mantém carrinho e estoque | PIX de R$ 5 + dinheiro de R$ 10 em compra de R$ 15; estoque entre lotes; produtos por peso | Integração transacional e unidade com `Decimal`; prova real removendo uma validação apenas no contêiner de teste |
| Continhas dos clientes | Compra pendente gera saldo e pagamento reduz a dívida | Sem cliente ou pagamento inválido não lança; dívida impede exclusão | Conta quitada, crédito, cliente com nome normalizado e isolamento por proprietário | Integração das rotas e regras financeiras |
| Dashboard e histórico | Soma faturamento, custos e lucro e mostra itens vendidos | Filtros inválidos mostram mensagem; outro proprietário não acessa vendas | Virada às 07:00, cinco vendas recentes, mudança de mês e preservação de totais anuais | Integração com datas controladas e PostgreSQL; sem depender do relógio real |

## Execução e isolamento

Os testes usam um projeto Compose próprio e PostgreSQL em volume separado. O runner Django cria `test_controle_estoque`, que é destruído ao terminar. Não utilizar o banco nativo, os volumes `estoque-prod`/`estoque-dev`, credenciais de terceiros ou APIs pagas para testar.

As respostas HTTP seguem o comportamento do Django deste projeto: rotas protegidas redirecionam com 302, erros de formulário normalmente retornam HTML 200 com mensagens, ausência de CSRF retorna 403 e métodos não aceitos retornam 405. Não substituir esses contratos pelos códigos dos exemplos Express dos slides.

Ferramentas: `unittest` e `django.test` já presentes; coverage.py autorizado somente na imagem de testes. Lighthouse é uma ferramenta externa de diagnóstico, sem dependência na aplicação de produção. O desafio de navegador é complementar; a cobertura Python não executa JavaScript.

## Resultados

Execução realizada em 04/11/2026:

| Verificação | Resultado |
| --- | --- |
| Suíte inicial, ordem embaralhada com seed 20261104 | 242 testes aprovados em 61,228 s |
| Suíte após compressão, incluindo dois testes novos de HTTP/CSRF | 244 testes aprovados em 52,295 s |
| Cobertura de linhas | 95,21%: 2603 de 2734 instruções |
| Cobertura de ramificações | 86,25%: 571 de 662 caminhos |
| Indicador combinado do coverage.py | 93,46% |
| Conexões de rede Python real durante a suíte final | Zero tentativas; APIs externas substituídas nos testes |
| Prova real da validação de pagamento insuficiente | Verde → vermelho com `AssertionError` → verde |
| Fluxo real no Chromium | Aprovado duas vezes seguidas, sem esperas fixas nem erros JavaScript |

A prova real removeu `if ValorRecebido < TotalDinheiro` somente da cópia do código dentro de um contêiner descartável. O teste `TestePagamentoMisto.test_DinheiroInsuficienteMantemCarrinhoEEstoque` deixou de encontrar a mensagem de R$ 0,01 faltante e falhou. O script restaurou os bytes originais, conferiu o SHA-256 e executou o teste novamente com sucesso. Nenhuma expectativa foi relaxada para aceitar a falha.

O navegador executou login inválido e válido, proteção da rota, cadastro de produto com preços mascarados, leitura na lista, F5 e busca incremental nos estados carregando, sucesso, vazio e erro HTTP simulado. Os campos foram encontrados por rótulos e textos visíveis. A busca foi verificada por atributos semânticos e respostas controladas, sem sleeps. O desafio opcional foi adaptado para Puppeteer/Chromium, já incluído nas ferramentas do Lighthouse, sem acrescentar outro framework de testes.

Os testes Python de telas são verificações de HTML gerado pelo Django e integração com formulários, não componentes React isolados. O fluxo real complementa essa cobertura executando JavaScript. A suíte é instrumentada por `Testes/ExecutarSuite.py`, que bloqueia sockets Python de saída; o PostgreSQL de teste utiliza libpq nativa em seu serviço isolado.

## Revisão por arquivo

Inspeção dos 12 arquivos de teste: todos possuem asserções; nenhum possui espera fixa Python. `TestCase` e `SimpleTestCase`, dados próprios e datas controladas sustentam o isolamento. A suíte embaralhada passou. Mocks de provedores externos verificam também o resultado produzido pela lógica real, não apenas valores pré-configurados.

| Arquivo e linha de referência | Resultado | Avaliação |
| --- | --- | --- |
| `src/configuracao/test_saude.py:10` | OK | Consulta real do componente, resposta 200/503 e método permitido; simula indisponibilidade do banco sem revelar erro. |
| `src/configuracao/test_compressao.py:15` | OK | Conteúdo HTTP descomprimido, redução de tamanho, Vary, login com CSRF e compatibilidade sem gzip. |
| `src/features/usuarios/tests.py:22` | OK | Autenticação real, erro visível, sessão e redirecionamento. |
| `src/features/usuarios/test_configuracoes.py:41` | OK com ressalva | Persistência, atomicidade e acesso à foto são verificados; alguns contratos de HTML são sensíveis a mudanças de marcação. Não cobrem o seletor de arquivos no navegador. |
| `src/features/fornecedor/tests.py:16` | OK com ressalva | Cadastro, inativação e filtros reais; linha 81 também confere IDs/script, o que não prova a execução do JavaScript. |
| `src/features/pagina_principal/tests.py:41` | OK com ressalva | Busca e ausência de alteração do estoque/carrinhos; linha 50 verifica parte do script como texto. |
| `src/features/produtos/tests.py:45` | OK com ressalva | Integrações externas simuladas e resultados reais conferidos; diversos casos de cadastro, lote, códigos e estoque. Linhas 1069, 1114 e 1163 incluem contratos de marcação. |
| `src/features/produtos/test_categorias.py:38` | OK | Cadastro, seleção existente, duplicidade, CSRF e migração idempotente. O diálogo tem verificação de marcação, não interação completa. |
| `src/features/produtos/test_mascaras_numericas.py:17` | OK | Decimais reais e persistência de valores; digitação no navegador complementada pelo fluxo E2E. |
| `src/features/produtos/test_nomes_cadastro.py:15` | OK | Resultados da normalização e gravação reais, inclusive zeros e duplicatas. |
| `src/features/vendas/test_pagamento_misto.py:39` | OK | Dinheiro, PIX, troco, estoque e preservação histórica. Prova real detectou remoção da validação. Alguns alertas também são conferidos por classe HTML. |
| `src/features/vendas/tests.py:46` | OK com ressalva | Datas, isolamento, contas e estoque são conferidos por dados reais; alguns testes de tela usam IDs, classes e trechos de script. |

Limitação identificada: as verificações de marcação acima podem precisar de manutenção em uma refatoração visual. Foram mantidas junto das asserções de negócio e complementadas por `Testes/FluxoNavegador.mjs`, que exerce comportamento observável. Não foram encontrados testes sem asserção, dependência obrigatória da ordem ou acesso efetivo a API externa durante a execução final. A inspeção estática foi auxiliar, não substituiu a execução.

Cobertura não mede se as asserções são boas, se o JavaScript funciona, se duas operações simultâneas disputam estoque corretamente ou se o notebook real tem bom desempenho. A prova de mutação e os testes do navegador fornecem evidência adicional. Continuam fora desta execução o diálogo de categoria, envio de foto, navegação por setas e divisão automática PIX/dinheiro no navegador; suas regras de servidor e/ou marcação têm testes, mas o fluxo E2E não exercitou essas interações.

## Reproduzir no Docker

Na raiz, com Docker Desktop aberto e `.env.docker` preparado:

```powershell
docker compose -f compose.testes.yaml build app
docker compose -f compose.testes.yaml run --rm app sh -c 'python -m coverage run Testes/ExecutarSuite.py test configuracao features --noinput --shuffle=20261104 && python -m coverage report && python -m coverage html && python -m coverage json'
docker compose -f compose.testes.yaml run --rm app python Testes/ProvaReal.py
docker compose -f compose.testes.yaml down
```

Relatórios locais, fora do Git: `relatorios/cobertura/index.html`, `relatorios/cobertura.json`, `relatorios/Cobertura.txt`, `relatorios/Suite-Depois.log`, `relatorios/Rede.json` e `relatorios/ProvaReal-*.log`. Na reprodução acima o resumo de cobertura aparece no terminal; para salvá-lo, acrescente `> /relatorios/Cobertura.txt` ao comando `coverage report` dentro do `sh`.

O teste de navegador usa dados sintéticos e a cópia de produção descrita em [PERFORMANCE.md](PERFORMANCE.md). Não execute os preparadores no ambiente de uso do comércio. `relatorios/AcessoDiagnostico.json` contém apenas a credencial temporária dessa cópia e deve continuar fora do Git.

Referências: [testes Django e isolamento](https://docs.djangoproject.com/en/6.1/topics/testing/overview/), [coverage.py](https://coverage.readthedocs.io/en/latest/) e [Lighthouse em páginas autenticadas](https://github.com/GoogleChrome/lighthouse/blob/main/docs/authenticated-pages.md).
