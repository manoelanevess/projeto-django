# AGENTS.md

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
- Usar PascalCase para arquivos, funções e variáveis criados pelo projeto.
- Manter nomes exigidos pelo Django no padrão do framework, como `manage.py`, `settings.py`, `urls.py`, `asgi.py` e `wsgi.py`.
- Manter variáveis de ambiente em maiúsculas, como `POSTGRES_DB`.
- Separar acesso a dados, lógica e componente quando a feature crescer.
- Filtros, busca, paginação e ordenação devem ficar na query string.
- Links de navegação devem ser `<a href="...">` no HTML final.
- Criar estado vazio e rota 404 quando houver tela de listagem ou rota nova.

## Restrições

- Não usar SQLite neste projeto.
- Não instalar biblioteca nova sem perguntar antes.
- Não criar componentes compartilhados se eles forem usados por apenas uma feature.
- Não importar uma feature dentro de outra sem motivo claro; Página Principal, estoque e relatórios podem consumir funções públicas de outras features para montar indicadores.
- Manter três carrinhos independentes na sessão e reduzir o estoque quantitativo apenas ao concluir a venda.
- Produtos vendidos por quilograma usam disponibilidade, sem quantidade exata nem baixa numérica no estoque.
- Produtos devem selecionar um fornecedor ativo já cadastrado; fornecedores são inativados, não apagados fisicamente.
- Produtos possuem preço de custo e de venda; carrinhos mostram somente a venda, e tabelas administrativas mostram ambos.
- O lucro da venda usa o custo copiado no momento da conclusão, sem recálculo retroativo.
- O dia comercial dos indicadores diários começa às 07:00 e termina às 06:59 do dia seguinte.
- Indicadores de faturamento mostram a soma das vendas; o resultado financeiro separa entradas, custo dos produtos vendidos e lucro dos produtos.
- Linhas de vendas recentes na Dashboard expandem no próprio histórico para mostrar itens, quantidades e valores cobrados, sem expor custos.
- Vendas de meses encerrados são consolidadas antes da remoção dos detalhes para preservar os indicadores anuais.
- Tratar o nome do cliente no carrinho como opcional e temporário: copiar para a venda concluída e limpar ao concluir ou cancelar o atendimento.
- Usar `Decimal` para valores monetários, quantidades e pesos; não usar `float` nesses cálculos.
- Manter a consulta de estoque da Página Principal somente leitura; inclusão, edição e exclusão ficam na área Estoque e pertencem à feature Produtos.
- Priorizar a experiência desktop; manter apenas responsividade básica para evitar quebra de conteúdo em telas menores.
- Não commitar `.env`, `.venv/`, bancos locais ou arquivos de cache.

## Comandos

```powershell
python -m pip install -r requirements.txt
python manage.py check
python manage.py runserver
python manage.py migrate
```

## Contexto de roteamento

Django usa roteamento baseado em configuração. As rotas ficam em `src/configuracao/urls.py`; cada rota deve chamar um componente dentro da feature correspondente.
