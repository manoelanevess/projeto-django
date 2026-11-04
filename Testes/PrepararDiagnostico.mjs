// Executar depois de subir o Compose isolado; nunca usa estoque-prod.
import {randomBytes} from 'node:crypto';
import {spawnSync} from 'node:child_process';
import {mkdir, readFile, writeFile} from 'node:fs/promises';

const Compose = ['compose', '-p', 'estoque-diagnostico', '-f', 'compose.prod.yaml', '-f', 'Testes/ComposeDiagnostico.yaml'];
await mkdir('relatorios', {recursive: true});
let Dados;
try {
  Dados = JSON.parse(await readFile('relatorios/AcessoDiagnostico.json', 'utf8'));
} catch (Erro) {
  if (Erro.code !== 'ENOENT') throw Erro;
  Dados = {usuario: 'diagnostico_aula', senha: randomBytes(32).toString('hex')};
  await writeFile('relatorios/AcessoDiagnostico.json', JSON.stringify(Dados), {mode: 0o600});
}
let Resultado = spawnSync('docker', [...Compose, 'cp', 'Testes/PrepararDiagnostico.py', 'app:/tmp/PrepararDiagnostico.py'], {encoding: 'utf8'});
if (Resultado.status !== 0) throw new Error(Resultado.stderr);
Resultado = spawnSync('docker', [...Compose, 'exec', '-T', 'app', 'python', 'manage.py', 'shell', '-c',
  'exec(open("/tmp/PrepararDiagnostico.py",encoding="utf-8").read())'],
{input: JSON.stringify(Dados), encoding: 'utf8'});
if (Resultado.status !== 0) throw new Error(Resultado.stderr);
console.log(Resultado.stdout.trim());
