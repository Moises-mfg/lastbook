'use strict';
(() => {
  const $ = s => document.querySelector(s);
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  let S, draft, timer;
  const size = n => n >= 1e9 ? (n/1e9).toLocaleString('pt-BR',{maximumFractionDigits:2})+' GB' : (n/1e6).toLocaleString('pt-BR',{maximumFractionDigits:1})+' MB';
  async function api(path, body) {
    const r = await fetch('/api/brasil/' + path, body === undefined ? {} : {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
    const d = await r.json(); if (!r.ok) throw Error(d.error || 'Não foi possível concluir.'); return d;
  }
  function notice(text) { $('#status').textContent = text; }
  function failure(e) { notice(e.message || 'Não foi possível concluir. Tente novamente.'); }
  function options(items, selected) { return Object.entries(items).map(([id, v]) => `<option value="${esc(id)}"${selected === id ? ' selected' : ''}>${esc(v.nome || v)}</option>`).join(''); }
  function route() {
    if (!S) return;
    const page = location.hash.slice(1) || 'biblioteca';
    document.querySelectorAll('nav a').forEach(a => { a.removeAttribute('aria-current'); if (a.hash === '#' + page) a.setAttribute('aria-current','page'); });
    if (page === 'downloads') downloads(); else if (page === 'enciclopedias') enciclopedias(); else if (page === 'mapas') mapas(); else if (page === 'compras') compras(); else if (page === 'instalacao') instalacao(); else if (page === 'ia') ia(); else biblioteca();
  }
  function biblioteca() {
    $('#conteudo').innerHTML = '<p class="tag">Sua base de conhecimento</p><h1>O essencial, mesmo<br>sem conexão.</h1><p class="intro">Guias curtos para começar a preparação da sua casa. Consulte a fonte e adapte o plano às necessidades da sua família.</p><label for="busca">Buscar nos guias locais</label><input id="busca" type="search" placeholder="Água, energia, comunicação…"><div class="cards" id="guias"></div>';
    const draw = () => {
      const norm = t => t.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLocaleLowerCase('pt-BR');
      const q = norm($('#busca').value);
      const found = S.guias.filter(g => norm(g.titulo + ' ' + g.texto + ' ' + g.categoria).includes(q));
      $('#guias').innerHTML = found.length ? found.map(g => `<div class="card"><p class="tag">${esc(g.categoria)}</p><h2>${esc(g.titulo)}</h2><button data-guide="${esc(g.id)}">Ler guia →</button></div>`).join('') : '<p>Nenhum guia encontrado. Tente outra palavra. Consulte também a seção Enciclopédias para pesquisar seus arquivos ZIM.</p>';
      document.querySelectorAll('[data-guide]').forEach(b => b.onclick = () => guide(b.dataset.guide));
    }; $('#busca').oninput = draw; draw();
  }
  function guide(id) {
    const g = S.guias.find(x => x.id === id); if (!g) return;
    $('#conteudo').innerHTML = `<button class="secundario" id="voltar">← Biblioteca</button><p class="tag">${esc(g.categoria)}</p><h1>${esc(g.titulo)}</h1><article><p>${esc(g.texto)}</p><p class="fonte">Referência: ${esc(g.fonte)}<br>Endereço para consultar enquanto houver internet:<code>${esc(g.url)}</code></p></article>`;
    $('#voltar').onclick = biblioteca;
  }
  function compras() {
    $('#conteudo').innerHTML = `<p class="tag">Minha preparação</p><h1>Comece pelo que<br>você já tem.</h1><p class="intro">Marque os itens disponíveis em casa. Suas escolhas são salvas neste computador. Quantidades dependem das pessoas, dos dias e dos riscos da sua região.</p><div class="painel">${S.compras.map(i => `<label class="linha${i.feito ? ' feito' : ''}"><input type="checkbox" data-item="${i.id}"${i.feito ? ' checked' : ''}><span><b>${esc(i.titulo)}</b><br><small>${esc(i.grupo)}</small></span></label>`).join('')}</div><p class="aviso">Sem anúncios ou links de afiliado nesta versão. A prioridade é a utilidade para sua casa.</p>`;
    document.querySelectorAll('[data-item]').forEach(input => input.onchange = async () => {
      input.disabled = true;
      try { S.compras = await api('check',{id:input.dataset.item,feito:input.checked}); input.closest('label').classList.toggle('feito',input.checked); }
      catch(e) { input.checked = !input.checked; failure(e); } finally { input.disabled = false; }
    });
  }
  function instalacao() {
    draft = S.escolhas ? structuredClone(S.escolhas) : {perfil:S.recomendado,modelo:S.perfis[S.recomendado].modelo,wikis:[S.perfis[S.recomendado].wiki],mapa:S.perfis[S.recomendado].mapa,estados:[]};
    $('#conteudo').innerHTML = `<p class="tag">Brasil inteiro, escolhas locais</p><h1>Uma biblioteca do<br>tamanho da sua vida.</h1><p class="intro">Escolha modelos, idiomas e variantes. O botão de salvar guarda suas preferências; o download só começa quando você pedir. Para um i3 com 8 GB, comece pelo Leve.</p><button id="importarPlano" class="secundario">Importar plano do site (.json)</button><form id="escolhas"><div class="cards">${Object.entries(S.perfis).map(([id,p]) => `<label class="card perfil"><input type="radio" name="perfil" value="${id}"${draft.perfil === id ? ' checked' : ''}><h2>${p.nome}</h2><p>${p.ram_gib ? p.ram_gib + ' GB de RAM como alvo' : 'Você escolhe os componentes'}${S.recomendado === id ? ' · sugerido' : ''}</p></label>`).join('')}</div><fieldset><legend>IA local</legend><label for="modelo">Modelo</label><select id="modelo">${options(S.modelos,draft.modelo)}</select><p>O modelo menor ocupa cerca de 640 MB; os modelos 4B e 14B precisam de mais memória e espaço. Desempenho depende do processador e deve ser testado no computador real.</p></fieldset><fieldset><legend>Enciclopédias</legend>${Object.entries(S.wikis).map(([id,title]) => `<label class="linha"><input type="checkbox" name="wiki" value="${id}"${draft.wikis.includes(id) ? ' checked' : ''}><span>${esc(title)}<br><small>${size(S.catalogo[id].size)} · edição ${esc(S.catalogo[id].edition)}</small></span></label>`).join('')}<p>Mini: introduções e quadros. Sem imagens: artigos completos em texto. Completa: arquivo com imagens; o leitor atual exibe os artigos em texto.</p></fieldset><fieldset><legend>Mapas desejados</legend><label for="mapa">Abrangência</label><select id="mapa">${options(S.mapas,draft.mapa)}</select><p>O download de mapas ainda está em desenvolvimento. As escolhas abaixo registram suas regiões de interesse; você já pode importar mapas MBTiles locais.</p><div class="selecao">${Object.entries(S.estados).map(([id,title]) => `<label class="linha"><input type="checkbox" name="estado" value="${id}"${draft.estados.includes(id) ? ' checked' : ''}>${esc(title)} (${id})</label>`).join('')}</div></fieldset><div class="aviso" id="estimativa" aria-live="polite"></div><div class="acoes"><button>Salvar escolhas</button><button type="button" id="instalar">Baixar modelos e enciclopédias</button></div></form>`;
    $('#importarPlano').onclick=()=>importar('plano').catch(failure);
    function values(){return {perfil:$('[name=perfil]:checked').value,modelo:$('#modelo').value,mapa:$('#mapa').value,wikis:[...document.querySelectorAll('[name=wiki]:checked')].map(e=>e.value),estados:[...document.querySelectorAll('[name=estado]:checked')].map(e=>e.value)};}
    function estimate(){
      const c=values(),ids=[...c.wikis,...(c.modelo==='sem-ia'?[]:[c.modelo])];
      const bytes=ids.reduce((n,id)=>n+(S.catalogo[id].instalado?0:Math.max(0,S.catalogo[id].size-S.catalogo[id].parcial_bytes)),0);
      const model=S.modelos[c.modelo];const warning=model.ram_gib && S.hardware.ram_bytes && S.hardware.ram_bytes<model.ram_gib*2**30*.94;
      $('#estimativa').textContent=`Download restante: ${size(bytes)}. Espaço livre: ${size(S.hardware.livre_bytes)}. Reserva adicional: 1 GB. Mapas não estão incluídos nesta operação.${warning?' O modelo escolhido excede a memória alvo deste computador; prefira uma opção menor.':''}`;
      $('#instalar').disabled=!ids.length;
    }
    document.querySelectorAll('[name=perfil]').forEach(r => r.onchange = () => {
      const p = S.perfis[r.value]; $('#modelo').value = p.modelo; $('#mapa').value = p.mapa;
      document.querySelectorAll('[name=wiki]').forEach(w => w.checked = w.value === p.wiki); estimate();
    });
    $('#escolhas').addEventListener('change',estimate);estimate();
    async function save(){S.escolhas=await api('choices',values());S=await api('state');}
    $('#escolhas').onsubmit=async e=>{e.preventDefault();try{await save();notice('Escolhas salvas. O download começa apenas quando você pedir.');}catch(e){failure(e);}};
    $('#instalar').onclick=async()=>{try{await save();await begin('install-selected',{},`Baixar os modelos e enciclopédias selecionados? Download restante: ${size(S.plano.download_bytes)}. Mapas não serão baixados.`);}catch(e){failure(e);}};
  }
  async function begin(path,body,question){
    if(question && !confirm(question))return;
    await api(path,body);S=await api('state');location.hash='downloads';downloads();poll();
  }
  async function downloads(){
    S=await api('state');
    if(location.hash!=='#downloads')return;
    $('#conteudo').innerHTML=`<p class="tag">Sua biblioteca, verificada</p><h1>Baixe agora.<br>Consulte depois.</h1><p class="intro">Arquivos oficiais, com tamanho e checksum fixados nesta versão. Você pode pausar downloads e retomá-los depois; a biblioteca instalada continua acessível.</p><div class="painel"><p id="andamento" role="status">Consultando andamento…</p><div class="acoes"><button id="pausar" class="secundario">Pausar download</button><button id="retomar">Retomar instalação pendente</button></div></div><div class="cards">${Object.entries(S.catalogo).map(([id,p])=>`<article><p class="tag">${p.kind==='zim'?'Enciclopédia':'IA local'}</p><h3>${esc(p.kind==='zim'?S.wikis[id]:S.modelos[id].nome)}</h3><p>${size(p.size)}${p.edition?' · '+esc(p.edition):''}<br>${p.instalado?'Verificado e instalado':p.parcial_bytes?'Parcial: '+size(p.parcial_bytes):'Ainda não instalado'}</p><details><summary>Fonte e licença</summary><p>${esc(p.source)}<br>${esc(p.license)}</p><p class="fonte">Arquivo: ${esc(p.file)}<br>SHA-256: ${esc(p.sha256)}</p></details><button data-package="${id}" class="secundario">${p.instalado?'Verificar arquivo':'Baixar ou retomar'}</button></article>`).join('')}</div>`;
    document.querySelectorAll('[data-package]').forEach(b=>b.onclick=()=>begin('install-package',{id:b.dataset.package},`Baixar/verificar ${S.catalogo[b.dataset.package].file}? Tamanho total: ${size(S.catalogo[b.dataset.package].size)}.`).catch(failure));
    $('#pausar').onclick=()=>api('pause',{}).then(r=>notice(r.mensagem)).catch(failure);
    $('#retomar').onclick=()=>begin('resume',{}).catch(failure);
    const j=await api('job');jobLine(j);if(['executando','baixando'].includes(j.estado))poll();
  }
  function jobLine(j){
    if($('#andamento'))$('#andamento').textContent=j.estado==='baixando'?`${j.fase}: ${j.nome || ''} · ${Math.round(100*j.feito/j.total)}% (${size(j.feito)} de ${size(j.total)}) · arquivo ${j.indice || 1} de ${j.quantidade || 1}`:j.mensagem || (j.estado==='executando'?'Preparando operação…':'Nenhuma operação em andamento.');
    if($('#pausar'))$('#pausar').disabled=j.estado!=='baixando';
  }
  async function importar(tipo) {
    const result = await api('import',{tipo});
    if (!result.cancelado) { S=await api('state'); notice(tipo==='plano'?'Plano importado. Nenhum download iniciado.':'Arquivo local aberto. O original permanece na pasta escolhida.'); route(); }
  }
  function enciclopedias(){
    const books=S.enciclopedias || [];
    $('#conteudo').innerHTML=`<p class="tag">Conhecimento offline</p><h1>Suas enciclopédias,<br>no seu computador.</h1><p class="intro">Pesquise várias enciclopédias instaladas ou filtre uma coleção. Os artigos são apresentados em texto. Cada edição mantém seus autores, créditos e licenças.</p><div class="acoes"><button id="abrirZim">Importar arquivo .zim</button><a class="botao" href="#downloads">Baixar enciclopédias</a></div><p>${books.length?books.map(b=>esc(b.nome)+(b.disponivel?'':' (disco desconectado)')).join('<br>'):'Nenhuma enciclopédia instalada. Baixe uma edição ou importe seu arquivo ZIM.'}</p><form id="buscarZim"><label for="colecaoZim">Pesquisar em</label><select id="colecaoZim"><option value="">Todas as coleções</option>${books.map(b=>`<option value="${esc(b.id)}">${esc(b.nome)}</option>`).join('')}</select><label for="termoZim">Palavra ou assunto</label><input id="termoZim" type="search" required maxlength="200"><div class="acoes"><button${!books.length?' disabled':''}>Pesquisar offline</button></div></form><div id="resultadosZim"></div>`;
    $('#abrirZim').onclick=()=>importar('zim').catch(failure);
    $('#buscarZim').onsubmit=async e=>{
      e.preventDefault();const button=$('#buscarZim button');button.disabled=true;
      try{
        const data=await api('search-zim',{busca:$('#termoZim').value,colecao:$('#colecaoZim').value || null}),results=data.resultados;
        const target=$('#resultadosZim');if(!target)return;
        target.innerHTML=(data.indisponiveis.length?`<p>Não foi possível pesquisar: ${esc(data.indisponiveis.join(', '))}.</p>`:'')+(results.length?results.map((r,i)=>`<p><button class="secundario" data-zim="${i}">${esc(r.titulo)}</button><br><small>${esc(r.nome_colecao)}</small></p>`).join(''):'<p>Nenhum artigo encontrado. Tente palavras mais curtas.</p>');
        document.querySelectorAll('[data-zim]').forEach(b=>b.onclick=()=>openArticle(results[Number(b.dataset.zim)]).catch(failure));
      }catch(e){failure(e);}finally{button.disabled=false;}
    };
  }
  async function openArticle(source){
    const article=await api('article-zim',{colecao:source.colecao,entrada:source.entrada});
    $('#conteudo').innerHTML=`<button class="secundario" id="voltarZim">← Enciclopédias</button><article><h1>${esc(article.titulo)}</h1><p class="fonte">${esc(source.nome_colecao || source.colecao)} · artigo ${esc(source.entrada)}<br>Conteúdo Wikipedia/Kiwix ou coleção importada. Consulte os avisos da edição para créditos e licença.</p><p class="resposta">${esc(article.texto)}</p></article>`;
    $('#voltarZim').onclick=()=>{location.hash='enciclopedias';enciclopedias();};
  }
  async function mapas() {
    $('#conteudo').innerHTML=`<p class="tag">Orientação offline</p><h1>Mapas que<br>ficam com você.</h1><p class="intro">Abra um arquivo MBTiles raster (PNG, JPEG ou WebP). Mapas vetoriais e rotas ainda estão em desenvolvimento. Não há geolocalização ou informações em tempo real.</p><button id="abrirMapa">Abrir mapa .mbtiles</button><p>Arquivo: ${esc(S.arquivos.mapa || 'nenhum selecionado')}</p><div id="mapaLocal"></div>`;
    $('#abrirMapa').onclick=()=>importar('mapa').catch(failure);
    if(!S.arquivos.mapa)return;
    try{
      const info=await api('mapa');let {z,x,y}=info;
      function draw(){
        const n=2**z;x=((x%n)+n)%n;y=Math.max(0,Math.min(n-1,y));
        $('#mapaLocal').innerHTML=`<div class="acoes"><button data-move="-1,0" aria-label="Oeste">←</button><button data-move="0,-1" aria-label="Norte">↑</button><button data-move="0,1" aria-label="Sul">↓</button><button data-move="1,0" aria-label="Leste">→</button><button id="mais" aria-label="Aproximar">+</button><button id="menos" aria-label="Afastar">−</button></div><div class="mapa-quadro"><div class="mapa-imagens">${[-1,0,1].flatMap(dy=>[-1,0,1].map(dx=>`<img alt="" src="/api/brasil/tile?z=${z}&x=${((x+dx)%n+n)%n}&y=${y+dy}" width="256" height="256">`)).join('')}</div></div><p>Nível ${z}. Áreas sem imagens podem estar fora da cobertura do arquivo.</p><p class="fonte">${esc(info.atribuicao)}</p>`;
        document.querySelectorAll('[data-move]').forEach(b=>b.onclick=()=>{const [dx,dy]=b.dataset.move.split(',').map(Number);x+=dx;y+=dy;draw();});
        $('#mais').disabled=z>=Math.min(info.maxzoom,22);$('#menos').disabled=z<=info.minzoom;
        $('#mais').onclick=()=>{x*=2;y*=2;z++;draw();};$('#menos').onclick=()=>{x=Math.floor(x/2);y=Math.floor(y/2);z--;draw();};
      }draw();
    }catch(e){failure(e);}
  }
  function ia(){
    const selected=(S.escolhas || {}).modelo || 'qwen3-0.6b',enabled=selected!=='sem-ia',spec=S.catalogo[selected];
    $('#conteudo').innerHTML=`<p class="tag">Assistente local · experimental</p><h1>Pergunte à<br>sua biblioteca.</h1><p class="intro">O modelo roda neste computador. Respostas podem conter erros: confira as referências, principalmente em situações de emergência.</p><div class="painel"><p>Motor: <b>${S.ia.motor?'disponível':'não instalado'}</b> · Modelo: <b>${enabled?esc(S.modelos[selected].nome):'desativado'}</b></p>${enabled?`<p>${size(spec.size)} · contexto de ${spec.context.toLocaleString('pt-BR')} tokens · ${spec.ram_gib} GB RAM como alvo.</p><button id="baixar" class="secundario">Baixar ou verificar modelo selecionado</button>`:'<p>Escolha um modelo em Minha instalação para ativar o assistente.</p>'}<p>O download é opcional. As perguntas e os trechos usados na resposta permanecem neste computador.</p></div><form id="pergunta"><label for="texto">Sua pergunta</label><textarea id="texto" maxlength="1500" required placeholder="Como começar a organizar minha preparação?"></textarea><div class="acoes"><button id="enviar"${!enabled || !S.ia.motor || !S.ia.modelo?' disabled':''}>Perguntar à IA</button><button type="button" class="secundario" id="buscar">Consultar guias sem IA</button></div></form><div id="resposta" class="resposta" aria-live="polite"></div><div id="fontesResposta"></div>`;
    $('#buscar').onclick=()=>{location.hash='biblioteca';};
    if($('#baixar'))$('#baixar').onclick=()=>begin('install-package',{id:selected},`Baixar/verificar o modelo selecionado (${size(spec.size)})?`).catch(failure);
    $('#pergunta').onsubmit=async e=>{e.preventDefault();try{await api('ask',{pergunta:$('#texto').value});$('#enviar').disabled=true;poll();}catch(e){failure(e);}};
    api('job').then(j=>{if(['executando','baixando'].includes(j.estado))poll();}).catch(failure);
  }
  async function poll(){
    clearTimeout(timer);
    try{
      const j=await api('job');jobLine(j);
      if(['executando','baixando'].includes(j.estado)){
        notice(j.estado==='baixando'?`${j.fase}: ${j.nome || ''} · ${Math.round(100*j.feito/j.total)}%`:'Processando neste computador…');timer=setTimeout(poll,1000);return;
      }
      notice(j.estado==='erro'?j.mensagem:j.mensagem || 'Resposta concluída. Confira as referências.');S=await api('state');
      if($('#resposta') && j.resposta){
        $('#resposta').textContent=j.resposta;
        $('#fontesResposta').innerHTML=(j.fontes || []).map((f,i)=>`<p><button class="secundario" data-source="${i}">${esc(typeof f==='string'?f:f.ref+' · '+f.titulo)}</button></p>`).join('');
        document.querySelectorAll('[data-source]').forEach(b=>b.onclick=()=>{const f=j.fontes[Number(b.dataset.source)];if(f.tipo==='zim')openArticle(f).catch(failure);else if(f.tipo==='guia')guide(f.id);});
      }
      if($('#enviar'))$('#enviar').disabled=!S.ia.motor || !S.ia.modelo || ((S.escolhas || {}).modelo || 'qwen3-0.6b')==='sem-ia';
      if(location.hash==='#downloads')downloads();
    }catch(e){failure(e);}
  }
  window.addEventListener('hashchange',route);
  api('state').then(s => { S=s; $('#hardware').textContent = `${s.hardware.ram_bytes ? (s.hardware.ram_bytes/2**30).toFixed(1) + ' GB RAM' : 'RAM não identificada'} · ${s.hardware.arch} · offline`; route(); }).catch(failure);
})();
