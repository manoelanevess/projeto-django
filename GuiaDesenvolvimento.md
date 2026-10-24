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
