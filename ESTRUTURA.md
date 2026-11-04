# Estrutura do projeto

```text
Dockerfile          Imagens Django (dev/prod) e Nginx (web-prod).
.dockerignore       Exclusoes do contexto de build.
compose.yaml        Desenvolvimento em localhost:8000.
compose.prod.yaml   Producao local em localhost:8080.
compose.testes.yaml Testes e cobertura com PostgreSQL isolado.
TESTES.md           Plano, resultados, cobertura e revisao dos testes.
PERFORMANCE.md      Lighthouse antes/depois e diagnostico.
Testes/             Prova de mutacao, bloqueio de rede e scripts de navegador.
.env.docker.example Exemplo sem segredos para os conteineres.
Docker/
  Auditoria.md           Conferencias e tamanhos das imagens para a aula.
  Iniciar.py             Migracoes antes de iniciar o servidor.
  Nginx.conf             Proxy HTTP e arquivos estaticos em producao.
  PrepararAmbiente.ps1    Configuracao inicial sem sobrescrever segredos.
  RequisitosProducao.txt  Dependencias exclusivas do Docker de producao.
src/
  componentes/       Componentes usados por duas ou mais features.
  configuracao/      Configurações globais do Django.
  features/
    pagina_principal/ Pesquisa rápida e acesso aos atendimentos.
    usuarios/        Login do proprietário.
    produtos/        Cadastro, manutenção e regras dos produtos no estoque.
    estoque/         Tela de estoque e Dashboard de indicadores.
    fornecedor/      Cadastro, consulta e manutenção de fornecedores.
    vendas/          Carrinhos, vendas e baixa automática do estoque.
```
