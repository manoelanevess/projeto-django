// Lighthouse e Chromium em perfil temporario, com login real na copia de diagnostico.
import {createRequire} from 'node:module';
import {readFile, writeFile, mkdir} from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';

const Etapa = process.argv[2];
if (!['Antes', 'Depois'].includes(Etapa)) throw new Error('Informe Antes ou Depois.');
const PastaFerramentas = process.env.PASTA_FERRAMENTAS || path.resolve('Testes');
const Importar = createRequire(path.join(PastaFerramentas, 'package.json'));
const {default: Lighthouse} = await import(pathToFileURL(Importar.resolve('lighthouse')).href);
const ChromeLauncher = await import(pathToFileURL(Importar.resolve('chrome-launcher')).href);
const {default: Puppeteer} = await import(pathToFileURL(Importar.resolve('puppeteer-core')).href);
const Dados = JSON.parse(await readFile(path.resolve('relatorios/AcessoDiagnostico.json'), 'utf8'));
const Base = 'http://127.0.0.1:8082';
const PastaSaida = path.resolve('relatorios/lighthouse');
await mkdir(PastaSaida, {recursive: true});
const Resumo = [];

for (let Numero = 1; Numero <= 3; Numero++) {
  const Chrome = await ChromeLauncher.launch({
    chromePath: process.env.CHROME_PATH || 'C:/Program Files/Google/Chrome/Application/chrome.exe',
    chromeFlags: ['--headless=new', '--disable-extensions', '--no-first-run', '--no-default-browser-check'],
  });
  let Navegador;
  try {
    Navegador = await Puppeteer.connect({browserURL: `http://127.0.0.1:${Chrome.port}`});
    const Pagina = await Navegador.newPage();
    await Pagina.goto(Base + '/login', {waitUntil: 'networkidle0'});
    await Pagina.locator('::-p-aria(Usuário)').fill(Dados.usuario);
    await Pagina.locator('::-p-aria(Senha)').fill(Dados.senha);
    await Promise.all([
      Pagina.waitForNavigation({waitUntil: 'networkidle0'}),
      Pagina.locator('::-p-aria(Entrar)').click(),
    ]);
    if (new URL(Pagina.url()).pathname !== '/') throw new Error('O login do diagnostico falhou.');
    const SessaoCdp = await Pagina.createCDPSession();
    await SessaoCdp.send('Network.clearBrowserCache');
    const Resultado = await Lighthouse(Base + '/', {
      port: Chrome.port, output: ['html', 'json'], onlyCategories: ['performance'],
      formFactor: 'mobile', disableStorageReset: true, logLevel: 'error',
    }, undefined, Pagina);
    const Relatorio = Resultado.lhr;
    if (Relatorio.runtimeError) throw new Error(JSON.stringify(Relatorio.runtimeError));
    const EnderecoFinal = Relatorio.finalDisplayedUrl || Relatorio.finalUrl;
    if (new URL(EnderecoFinal).pathname !== '/') throw new Error('Lighthouse mediu a tela de login.');
    await writeFile(path.join(PastaSaida, `${Etapa}-${Numero}.html`), Resultado.report[0]);
    await writeFile(path.join(PastaSaida, `${Etapa}-${Numero}.json`), Resultado.report[1]);
    const Metricas = {
      rodada: Numero, nota: Math.round(Relatorio.categories.performance.score * 100),
      FCP_ms: Relatorio.audits['first-contentful-paint'].numericValue,
      LCP_ms: Relatorio.audits['largest-contentful-paint'].numericValue,
      TBT_ms: Relatorio.audits['total-blocking-time'].numericValue,
      CLS: Relatorio.audits['cumulative-layout-shift'].numericValue,
      bytes: Relatorio.audits['total-byte-weight'].numericValue,
      configuracao: Relatorio.configSettings, versao: Relatorio.lighthouseVersion,
      navegador: Relatorio.environment.networkUserAgent,
    };
    Resumo.push(Metricas);
    console.log(JSON.stringify({etapa: Etapa, ...Metricas, configuracao: undefined}));
  } finally {
    if (Navegador) Navegador.disconnect();
    await Chrome.kill();
  }
}
await writeFile(path.join(PastaSaida, `${Etapa}-Resumo.json`), JSON.stringify(Resumo, null, 2));
