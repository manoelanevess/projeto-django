// Fluxo real em Chromium, somente na copia isolada de diagnostico.
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
import {readFile, writeFile, mkdir} from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';

const Importar = createRequire(path.join(process.env.PASTA_FERRAMENTAS || path.resolve('Testes'), 'package.json'));
const {default: Puppeteer} = await import(pathToFileURL(Importar.resolve('puppeteer-core')).href);
const Dados = JSON.parse(await readFile('relatorios/AcessoDiagnostico.json', 'utf8'));
const Base = 'http://127.0.0.1:8082';
const Resultados = [];

for (let Rodada = 1; Rodada <= 2; Rodada++) {
  const Navegador = await Puppeteer.launch({
    executablePath: process.env.CHROME_PATH || 'C:/Program Files/Google/Chrome/Application/chrome.exe',
    headless: true, defaultViewport: {width: 1440, height: 1000},
    args: ['--disable-extensions', '--no-first-run'],
  });
  try {
    const Pagina = await Navegador.newPage();
    Pagina.setDefaultTimeout(15000);
    const ErrosJavascript = [];
    Pagina.on('pageerror', Erro => ErrosJavascript.push(Erro.message));
    await Pagina.goto(Base + '/estoque', {waitUntil: 'networkidle0'});
    assert.equal(new URL(Pagina.url()).pathname, '/login');
    await Pagina.locator('::-p-aria(Usuário)').fill(Dados.usuario);
    await Pagina.locator('::-p-aria(Senha)').fill('senha-incorreta-de-teste');
    await Promise.all([Pagina.waitForNavigation(), Pagina.locator('::-p-aria(Entrar)').click()]);
    await Pagina.waitForSelector('::-p-text(Usuário ou senha inválidos.)', {visible: true});
    await Pagina.locator('::-p-aria(Senha)').fill(Dados.senha);
    await Promise.all([Pagina.waitForNavigation(), Pagina.locator('::-p-aria(Entrar)').click()]);
    assert.equal(new URL(Pagina.url()).pathname, '/');

    const Nome = 'Produto Navegador ' + Date.now();
    await Pagina.goto(Base + '/estoque/novo', {waitUntil: 'networkidle0'});
    await Pagina.locator('::-p-aria(Nome do produto)').fill(Nome);
    const Categoria = await Pagina.$('::-p-aria(Categoria)');
    await Categoria.select('Diagnostico');
    const Fornecedor = await Pagina.$('::-p-aria(Fornecedor)');
    const ValorFornecedor = await Fornecedor.evaluate(Elemento => [...Elemento.options]
      .find(Opcao => Opcao.textContent === 'Fornecedor Diagnostico').value);
    await Fornecedor.select(ValorFornecedor);
    await Pagina.locator('::-p-aria(Preço de custo (R$))').fill('2,50');
    await Pagina.locator('::-p-aria(Preço de venda (R$))').fill('5,00');
    await Pagina.locator('::-p-aria(Quantidade em estoque)').fill('10');
    await Pagina.locator('::-p-aria(Estoque mínimo)').fill('1');
    await Promise.all([Pagina.waitForNavigation(), Pagina.locator('::-p-aria(Cadastrar produto)').click()]);
    assert.equal(new URL(Pagina.url()).pathname, '/estoque');
    await Pagina.goto(Base + '/estoque?busca=' + encodeURIComponent(Nome), {waitUntil: 'networkidle0'});
    await Pagina.waitForSelector(`::-p-text(${Nome})`, {visible: true});
    await Pagina.reload({waitUntil: 'networkidle0'});
    await Pagina.waitForSelector(`::-p-text(${Nome})`, {visible: true});

    // Estados da busca incremental: carregando, sucesso, vazio e erro de rede.
    await Pagina.setRequestInterception(true);
    let Modo = 'normal';
    let ResolverPendente;
    const ProximaRequisicao = () => new Promise(Resolver => { ResolverPendente = Resolver; });
    Pagina.on('request', Requisicao => {
      if (Requisicao.resourceType() === 'fetch' && new URL(Requisicao.url()).pathname === '/estoque') {
        if (Modo === 'segurar') { ResolverPendente(Requisicao); return; }
        if (Modo === 'erro') { Requisicao.respond({status: 500, contentType: 'text/plain', body: 'Falha simulada'}); return; }
      }
      Requisicao.continue();
    });
    const CampoBusca = await Pagina.$('::-p-aria(Produto ou código de barras)');
    assert.ok(CampoBusca, 'Campo de busca sem nome acessivel/identificacao');
    // Rótulos e atributos semânticos identificam os campos, sem classes CSS.
    Modo = 'segurar';
    const Pendente = ProximaRequisicao();
    const RespostaSucesso = Pagina.waitForResponse(Resposta => {
      const Endereco = new URL(Resposta.url());
      return Endereco.pathname === '/estoque' && Endereco.searchParams.get('busca') === 'Produto Diagnostico 001';
    });
    await Pagina.locator('::-p-aria(Produto ou código de barras)').fill('Produto Diagnostico 001');
    assert.equal(await CampoBusca.evaluate(Elemento => Elemento.value), 'Produto Diagnostico 001');
    const Requisicao = await Pendente;
    await Pagina.waitForSelector('[aria-busy="true"]');
    Modo = 'normal';
    await Requisicao.continue();
    assert.equal((await RespostaSucesso).status(), 200);
    await Pagina.waitForSelector('::-p-text(Produto Diagnostico 001)', {visible: true});
    await Pagina.waitForFunction(() => !document.querySelector('[aria-busy="true"]'));
    const BuscaVazia = 'NenhumResultado' + Date.now();
    const RespostaVazia = Pagina.waitForResponse(Resposta => new URL(Resposta.url()).searchParams.get('busca') === BuscaVazia);
    await Pagina.locator('::-p-aria(Produto ou código de barras)').fill(BuscaVazia);
    assert.equal(await CampoBusca.evaluate(Elemento => Elemento.value), BuscaVazia);
    assert.equal((await RespostaVazia).status(), 200);
    await Pagina.waitForSelector('::-p-text(Nenhum produto encontrado)', {visible: true});
    Modo = 'erro';
    const RespostaErro = Pagina.waitForResponse(Resposta => new URL(Resposta.url()).searchParams.get('busca') === 'ErroSimulado');
    await Pagina.locator('::-p-aria(Produto ou código de barras)').fill('ErroSimulado');
    assert.equal(await CampoBusca.evaluate(Elemento => Elemento.value), 'ErroSimulado');
    assert.equal((await RespostaErro).status(), 500);
    await Pagina.waitForSelector('::-p-text(Não foi possível pesquisar agora. Tente novamente.)', {visible: true});
    assert.deepEqual(ErrosJavascript, []);
    await mkdir('relatorios/navegador', {recursive: true});
    await Pagina.screenshot({path: `relatorios/navegador/Rodada-${Rodada}.png`, fullPage: true});
    Resultados.push({rodada: Rodada, produto: Nome, resultado: 'OK',
      verificacoes: ['rota protegida', 'login invalido', 'login valido', 'cadastro com campos mascarados',
        'produto na lista', 'F5', 'busca carregando', 'busca sucesso', 'busca vazia', 'erro da busca', 'sem erros JavaScript']});
    console.log(`Rodada ${Rodada}: fluxo real aprovado, sem esperas fixas.`);
  } finally {
    await Navegador.close();
  }
}
await writeFile('relatorios/navegador/Resultado.json', JSON.stringify(Resultados, null, 2));
