import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {JSDOM} from 'jsdom';
import {execFileSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';

const html=readFileSync(new URL('../index.html',import.meta.url),'utf8');
const catalog=readFileSync(new URL('../catalogo.js',import.meta.url),'utf8');
const downloads=readFileSync(new URL('../downloads.js',import.meta.url),'utf8');
const script=readFileSync(new URL('../app.js',import.meta.url),'utf8');
function start(saved,configureDownloads){
  const dom=new JSDOM(html,{url:'https://ultimo-livro.invalid/',runScripts:'outside-only'});
  if(saved)dom.window.localStorage.setItem('ul-checklist',saved);
  dom.window.eval(catalog);dom.window.eval(downloads);
  if(configureDownloads)configureDownloads(dom.window.ULTIMO_LIVRO_DOWNLOADS);
  dom.window.eval(script);return dom;
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
  assert.ok(d.querySelector('a[href="https://github.com/Moises-mfg/o-ultimo-livro/releases/tag/v0.4.0-alpha.6"]'));
  dom.window.close();
});

test('downloads apresentam plataformas, requisitos e apenas links de pacotes publicados',()=>{
  const dom=start(),d=dom.window.document;
  const section=d.querySelector('#downloads');
  assert.equal(d.querySelector('#'+section.getAttribute('aria-labelledby')).tagName,'H2');
  const cards=[...section.querySelectorAll('article[data-platform]')];
  assert.deepEqual(cards.map(card=>card.dataset.platform),['linux','macos-arm64','macos-x64','windows-x64']);
  for(const card of cards){
    assert.equal(d.getElementById(card.getAttribute('aria-labelledby')).tagName,'H3');
    assert.ok(card.querySelector('.download-instrucoes').textContent.length>30);
  }
  const linux=cards[0];
  assert.match(linux.textContent,/v0\.4\.0-alpha\.6 · Alpha disponível/);
  assert.match(linux.querySelector('.download-requisitos').textContent,/Ubuntu 24\.04–26\.04 x86_64/);
  const files='https://github.com/Moises-mfg/o-ultimo-livro/releases/download/v0.4.0-alpha.6/';
  assert.equal(linux.querySelector('a').href,files+'ultimo-livro_0.4.0-alpha6_amd64.deb');
  for(const mac of cards.slice(1,3))assert.match(mac.querySelector('.download-requisitos').textContent,/macOS 13\.3 ou posterior/);
  assert.match(cards[1].textContent,/Apple Silicon/);assert.match(cards[2].textContent,/Intel/);
  assert.match(cards[3].querySelector('.download-requisitos').textContent,/Windows 10 versão 1809 ou posterior, x64/);
  assert.match(cards[3].querySelector('.download-instrucoes').textContent,/WebView2/);
  assert.equal(cards[1].querySelector('a').href,files+'ultimo-livro_0.4.0-alpha6_macos-arm64.dmg');
  assert.equal(cards[2].querySelector('a').href,files+'ultimo-livro_0.4.0-alpha6_macos-x64.dmg');
  assert.equal(cards[3].querySelector('a').href,'https://github.com/Moises-mfg/o-ultimo-livro/releases/tag/v0.4.0-alpha.6');
  assert.ok(section.querySelector('a[href="https://github.com/Moises-mfg/o-ultimo-livro/blob/main/docs/brasil/INSTALACAO-DESKTOP.md"]'));
  assert.ok(section.querySelector('a[href="https://github.com/Moises-mfg/o-ultimo-livro/tree/v0.4.0-alpha.6"]'));
  const scripts=[...d.querySelectorAll('script[src]')].map(s=>s.getAttribute('src'));
  assert.ok(scripts.indexOf('downloads.js')<scripts.indexOf('app.js'));
  dom.window.close();
});

test('disponibilidade exige URL publicada e ignora links de plataforma ainda em validação',()=>{
  const dom=start(undefined,platforms=>{
    platforms[0].releaseUrl=null;
    platforms[0].downloadUrl=null;
    platforms[1].available=false;
  });
  const d=dom.window.document;
  assert.equal(d.querySelectorAll('#downloads-lista a').length,2);
  assert.match(d.querySelector('[data-platform=linux] .download-status').textContent,/download indisponível/);
  assert.match(d.querySelector('[data-platform=macos-arm64] .download-status').textContent,/Em validação/);
  dom.window.close();
});
