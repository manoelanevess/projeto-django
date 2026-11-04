# Guia de Desenvolvimento

## Projeto

Sistema de controle de estoque para a matéria de Frameworks Web.

Framework: Django 6.1.1.
Banco de dados: PostgreSQL configurado por `.env`.
Roteamento: MPA com `path()` no arquivo `src/configuracao/urls.py`.

## Estrutura obrigatória

- `src/configuracao/` guarda configurações globais, rotas principais, ASGI e WSGI.
- `src/features/<nome-da-feature>/` guarda API, lógica e componentes da feature.
- `src/componentes/` guarda apenas código usado por duas ou mais features.
- `ROTAS.md` guarda o mapa de navegação e os esboços de telas.
- A rota deve ser uma casca fina: registrar URL em `urls.py` e importar o componente da feature.

## Regras de código

- Usar português nos nomes do domínio do projeto.
- Salvar nomes de produtos, marcas, categorias, fornecedores, cidades e clientes com inicial maiúscula em cada palavra, removendo espaços excedentes. Aplicar a regra no servidor, inclusive em cadastros e edições, e mostrar a padronização ao sair do campo.
- Usar PascalCase para arquivos, funções e variáveis criados pelo projeto.
- Manter nomes exigidos pelo Django no padrão do framework, como `manage.py`, `settings.py`, `urls.py`, `asgi.py` e `wsgi.py`.
- Manter variáveis de ambiente em maiúsculas, como `POSTGRES_DB`.
- Separar acesso a dados, lógica e componente quando a feature crescer.
- Filtros, busca, paginação e ordenação devem ficar na query string.
- Links de navegação devem ser `<a href="...">` no HTML final.
- Permitir navegar entre campos visíveis e editáveis pelas setas do teclado, seguindo a posição visual. Ignorar campos ocultos, desabilitados e somente leitura; manter a navegação dentro de diálogos abertos.
- Usar as confirmações visuais de `componentes/AvisosSistema.py` para ações que descartam atendimentos ou removem dados. Priorizar o botão de cancelamento, permitir Esc e devolver o foco ao acionador; confirmar deve enviar o formulário original uma única vez. Carrinhos vazios e sem cliente identificado fecham diretamente.
- Criar estado vazio e rota 404 quando houver tela de listagem ou rota nova.

## Restrições

- Não usar SQLite neste projeto.
- Não instalar biblioteca nova sem perguntar antes.
- Não criar componentes compartilhados se eles forem usados por apenas uma feature.
- Não importar uma feature dentro de outra sem motivo claro; Página Principal, estoque e relatórios podem consumir funções públicas de outras features para montar indicadores.
- Iniciar com três carrinhos independentes na sessão e permitir abrir mais pelo botão +, sem limite fixo. Reduzir o estoque quantitativo apenas ao concluir a venda.
- Produtos vendidos por quilograma usam disponibilidade, sem quantidade exata nem baixa numérica no estoque.
- Produtos devem selecionar um fornecedor ativo já cadastrado; fornecedores são inativados, não apagados fisicamente.
- Cadastrar categorias pelo botão + ao lado do filtro de categorias do estoque. Cadastro e edição de produtos devem selecionar uma categoria existente; preservar categorias mesmo sem produtos e aproveitar as categorias já usadas.
- Produtos possuem preço de custo e de venda; carrinhos mostram somente a venda, e tabelas administrativas mostram ambos.
- O lucro da venda usa o custo copiado no momento da conclusão, sem recálculo retroativo.
- O dia comercial dos indicadores diários começa às 07:00 e termina às 06:59 do dia seguinte.
- Vendas recentes da Dashboard mostram até cinco vendas do dia comercial atual e reiniciam diariamente às 07:00, sem apagar o histórico de vendas.
- Indicadores de faturamento mostram a soma das vendas; o resultado financeiro separa entradas, custo dos produtos vendidos e lucro dos produtos.
- Linhas de vendas recentes na Dashboard expandem no próprio histórico para mostrar itens, quantidades e valores cobrados, sem expor custos.
- Vendas de meses encerrados são consolidadas antes da remoção dos detalhes para preservar os indicadores anuais.
- Tratar o nome do cliente no carrinho como opcional e temporário: copiar para a venda concluída e limpar ao concluir ou cancelar o atendimento.
- Usar `Decimal` para valores monetários, quantidades e pesos; não usar `float` nesses cálculos.
- Aplicar máscaras brasileiras visíveis de moeda, quantidade e telefone nas entradas numéricas, inclusive campos carregados dinamicamente: mostrar R$ nos valores monetários, a unidade nas quantidades quando conhecida e exemplos nos campos vazios. Formatar durante a digitação, normalizar antes da validação no servidor e preservar códigos de barras e zeros à esquerda.
- Permitir pagamento em PIX + dinheiro com os dois valores inicialmente em branco, mostrando recebido em dinheiro antes do valor no PIX. Ao editar um dos valores, preencher o outro com o restante da compra. Calcular o troco somente sobre a parte em dinheiro e preservar a divisão nas vendas arquivadas.
- Manter a consulta de estoque da Página Principal somente leitura; inclusão, edição e exclusão ficam na área Estoque e pertencem à feature Produtos.
- Priorizar a experiência desktop; manter apenas responsividade básica para evitar quebra de conteúdo em telas menores.
- Não commitar `.env`, `.venv/`, bancos locais ou arquivos de cache.
- O acesso Proprietário no cabeçalho abre as configurações. Persistir o nome do comércio para todas as páginas e o login; a foto pertence ao usuário autenticado, aceita JPG, PNG e WebP de até 2 MB e é servida somente com login. Nome e foto devem ser salvos juntos apenas quando o formulário inteiro for válido.

## Comandos

```powershell
python -m pip install -r requirements.txt
python manage.py check
python manage.py runserver
python manage.py migrate
```

## Contexto de roteamento

Django usa roteamento baseado em configuração. As rotas ficam em `src/configuracao/urls.py`; cada rota deve chamar um componente dentro da feature correspondente.

## Docker

- Manter o `Dockerfile` na raiz, com estágios `dev`, `build`, `prod` e `web-prod`. Django é uma MPA: não criar frontend Node nem fallback de SPA para este projeto.
- `compose.yaml` é o ambiente de desenvolvimento, com código montado e recarga automática; `compose.prod.yaml` simula produção local em `http://localhost:8080`, com Gunicorn e Nginx, sem volumes de código.
- Fixar versões das imagens, copiar requisitos antes do código e executar aplicação e proxy sem root. Não adicionar a chave obsoleta `version` aos arquivos Compose.
- Segredos entram em tempo de execução por `.env.docker`, que deve ficar fora do Git e do contexto de build. Versionar somente `.env.docker.example`, sem segredos. Não reutilizar nem alterar o `.env` do ambiente nativo para subir Docker.
- PostgreSQL 18 usa volume em `/var/lib/postgresql`. Manter volumes separados para desenvolvimento e produção e nunca publicar a porta do banco por padrão. Não trocar PostgreSQL por SQLite.
- Aplicar migrations antes de iniciar o servidor, aguardar banco saudável e manter `GET /health` sem autenticação, consultando o banco e retornando 503 sem detalhes sensíveis se ele falhar.
- As exceções de cookies e redirecionamento HTTPS nos Composes valem para a simulação local em HTTP. Em deploy público, usar HTTPS e os padrões seguros; não alterar os padrões de produção de `settings.py` para acomodar testes locais.
- Gunicorn foi autorizado para o Docker e fica em `Docker/RequisitosProducao.txt`; não instalar no ambiente virtual Windows. Dependências adicionais continuam exigindo consulta prévia.
- Documentar os comandos e a persistência no README. Não executar `down -v`, apagar volumes ou importar dados reais como parte de testes rotineiros.

## Testes e diagnóstico

- Manter o plano em `TESTES.md` e as medições em `PERFORMANCE.md`, adaptando exemplos de outras stacks ao Django MPA.
- A imagem `testes` e `compose.testes.yaml` têm PostgreSQL e volume próprios. O runner cria banco `test_...`; nunca utilizar dados do comércio como fixture.
- coverage.py foi autorizado somente para a imagem de testes; Lighthouse foi autorizado como ferramenta de diagnóstico, com dependências em `Testes/package.json`. Não levá-los à imagem de produção.
- Manter provas de mutação apenas em contêiner descartável, restaurar o código e conferir o hash. Nunca modificar código no host ou na produção para provocar falha.
- O fluxo de navegador usa rótulos, textos e atributos semânticos, sem esperas fixas. A execução de HTML nos testes Django não substitui testes de JavaScript no navegador.
- Medir performance em produção, página autenticada, cache controlado e três rodadas em condições iguais. Informar mediana, variação e limites; não chamar TBT de INP nem dados de laboratório de dados reais de usuários.
- `Testes/ComposeDiagnostico.yaml` cria uma cópia isolada em 8082. Exigir `AMBIENTE_DIAGNOSTICO=1` antes de criar os dados sintéticos. Guardar credenciais e relatórios em `relatorios/`, fora do Git e do build.
- A compressão HTTP usa `GZipMiddleware` nativo do Django, com negociação de conteúdo e proteção HTB. Preservar os testes de login e CSRF ao alterá-la.
