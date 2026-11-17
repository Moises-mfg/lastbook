import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {JSDOM} from 'jsdom';
import {execFileSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';

const html=readFileSync(new URL('../index.html',import.meta.url),'utf8');
const catalog=readFileSync(new URL('../catalogo.js',import.meta.url),'utf8');
const script=readFileSync(new URL('../app.js',import.meta.url),'utf8');
function start(saved){
  const dom=new JSDOM(html,{url:'https://ultimo-livro.invalid/',runScripts:'outside-only'});
  if(saved)dom.window.localStorage.setItem('ul-checklist',saved);
  dom.window.eval(catalog);dom.window.eval(script);return dom;
}

test('perfis reais e aviso de RAM respondem à escolha do visitante',()=>{
  const dom=start(),w=dom.window,d=w.document;
  assert.equal(d.querySelectorAll('[name=perfil]').length,4);
  const large=d.querySelector('[name=perfil][value=parruda]');large.checked=true;
  large.dispatchEvent(new w.Event('change',{bubbles:true}));
  assert.match(d.querySelector('#resumo').textContent,/excede/);
  d.querySelector('#ram').value='16';d.querySelector('#ram').dispatchEvent(new w.Event('change'));
  assert.equal(d.querySelector('[name=perfil]:checked').value,'moderada');
  assert.equal(d.querySelectorAll('#estado option').length,28);
  dom.window.close();
});

test('checklist persiste e pode ser limpo sem enviar dados',()=>{
  const first=start();first.window.document.querySelector('#checklist input').click();
  const saved=first.window.localStorage.getItem('ul-checklist');assert.equal(saved,'[0]');first.window.close();
  const second=start(saved),d=second.window.document;
  assert.equal(d.querySelector('#checklist input').checked,true);
  d.querySelector('#limpar').click();assert.equal(second.window.localStorage.getItem('ul-checklist'),null);
  assert.equal(d.querySelectorAll('#checklist input:checked').length,0);second.window.close();
});

test('exportação gera o plano escolhido, sem conta nem requisição externa',async()=>{
  const dom=start(),w=dom.window,d=w.document;let blob,clicked;
  w.Blob=globalThis.Blob;w.URL.createObjectURL=b=>{blob=b;return 'blob:teste';};w.URL.revokeObjectURL=()=>{};
  w.HTMLAnchorElement.prototype.click=function(){clicked={name:this.download,url:this.href};};
  d.querySelector('#estado').value='SP';d.querySelector('[name=idioma][value=es]').click();d.querySelector('#exportar').click();
  assert.equal(clicked.name,'meu-plano-ultimo-livro.json');assert.equal(clicked.url,'blob:teste');
  const plan=JSON.parse(await blob.text());assert.equal(plan.estado,'SP');assert.deepEqual(plan.idiomas,['pt','es']);assert.equal(plan.perfil,'leve');
  const accepted=JSON.parse(execFileSync('python3',['-c','import json,sys;from brasil.core import validate_choices;print(json.dumps(validate_choices(json.load(sys.stdin))))'],{cwd:fileURLToPath(new URL('../../',import.meta.url)),input:JSON.stringify(plan),encoding:'utf8'}));
  assert.equal(accepted.modelo,'qwen3-0.6b');assert.deepEqual(accepted.estados,['SP']);assert.deepEqual(accepted.wikis,['es-mini','pt-mini']);
  dom.window.close();
});

test('município escolhido entra no plano aceito pelo aplicativo',async()=>{
  const dom=start(),w=dom.window,d=w.document;let blob;
  w.Blob=globalThis.Blob;w.URL.createObjectURL=b=>{blob=b;return 'blob:teste';};w.URL.revokeObjectURL=()=>{};w.HTMLAnchorElement.prototype.click=function(){};
  assert.equal(Object.values(w.ULTIMO_LIVRO_MAPAS).filter(p=>p.scope==='municipio').length,5571);
  d.querySelector('#estado').value='MT';d.querySelector('#estado').dispatchEvent(new w.Event('change'));
  const city=d.querySelector('#municipio-site');city.value='5101837';city.dispatchEvent(new w.Event('change'));d.querySelector('#exportar').click();
  const plan=JSON.parse(await blob.text());assert.deepEqual(plan.municipios,['5101837']);assert.equal(plan.mapa,'municipio');
  const accepted=JSON.parse(execFileSync('python3',['-c','import json,sys;from brasil.core import validate_choices;print(json.dumps(validate_choices(json.load(sys.stdin))))'],{cwd:fileURLToPath(new URL('../../',import.meta.url)),input:JSON.stringify(plan),encoding:'utf8'}));
  assert.deepEqual(accepted.municipios,['5101837']);assert.match(d.querySelector('#resumo').textContent,/incluem os mapas/);dom.window.close();
});

test('navegação local encontra seções e scripts não carregam terceiros',()=>{
  const dom=start(),d=dom.window.document;
  for(const a of d.querySelectorAll('a[href^="#"]'))assert.ok(d.querySelector(a.getAttribute('href')),a.outerHTML);
  for(const script of d.querySelectorAll('script[src]'))assert.equal(new URL(script.src).origin,'https://ultimo-livro.invalid');
  assert.ok(d.querySelector('a[href="https://github.com/Moises-mfg/lastbook/releases"]'));
  dom.window.close();
});
