'use strict';
(() => {
  const $ = s => document.querySelector(s);
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  let S, draft, timer;
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
    if (page === 'enciclopedias') enciclopedias(); else if (page === 'mapas') mapas(); else if (page === 'compras') compras(); else if (page === 'instalacao') instalacao(); else if (page === 'ia') ia(); else biblioteca();
  }
  function biblioteca() {
    $('#conteudo').innerHTML = '<p class="tag">Sua base de conhecimento</p><h1>O essencial, mesmo<br>sem conexão.</h1><p class="intro">Guias curtos para começar a preparação da sua casa. Consulte a fonte e adapte o plano às necessidades da sua família.</p><label for="busca">Buscar nos guias locais</label><input id="busca" type="search" placeholder="Água, energia, comunicação…"><div class="cards" id="guias"></div>';
    const draw = () => {
      const norm = t => t.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLocaleLowerCase('pt-BR');
      const q = norm($('#busca').value);
      const found = S.guias.filter(g => norm(g.titulo + ' ' + g.texto + ' ' + g.categoria).includes(q));
      $('#guias').innerHTML = found.length ? found.map(g => `<div class="card"><p class="tag">${esc(g.categoria)}</p><h2>${esc(g.titulo)}</h2><button data-guide="${esc(g.id)}">Ler guia →</button></div>`).join('') : '<p>Nenhum guia encontrado. Tente outra palavra. A Wikipedia ainda não está instalada nesta versão.</p>';
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
    $('#conteudo').innerHTML = `<p class="tag">Brasil inteiro, escolhas locais</p><h1>Uma biblioteca do<br>tamanho da sua vida.</h1><p class="intro">Escolha o perfil e ajuste idiomas e regiões. Para um i3 com 8 GB, comece pelo Leve. Esta tela salva preferências; os pacotes de Wikipedia e mapas ainda não estão publicados.</p><form id="escolhas"><div class="cards">${Object.entries(S.perfis).map(([id,p]) => `<label class="card perfil"><input type="radio" name="perfil" value="${id}"${draft.perfil === id ? ' checked' : ''}><h2>${p.nome}</h2><p>${p.ram_gib ? p.ram_gib + ' GB de RAM como alvo' : 'Você escolhe os componentes'}${S.recomendado === id ? ' · sugerido' : ''}</p></label>`).join('')}</div><fieldset><legend>IA local</legend><label for="modelo">Modelo desejado</label><select id="modelo">${options(S.modelos,draft.modelo)}</select><p>Os modelos 4B e 14B são planejados. Somente o 0.6B experimental tem integração inicial; qualidade e velocidade no i3 ainda precisam de teste.</p></fieldset><fieldset><legend>Enciclopédias desejadas</legend>${Object.entries(S.wikis).map(([id,title]) => `<label class="linha"><input type="checkbox" name="wiki" value="${id}"${draft.wikis.includes(id) ? ' checked' : ''}>${esc(title)}</label>`).join('')}</fieldset><fieldset><legend>Mapas desejados</legend><label for="mapa">Abrangência</label><select id="mapa">${options(S.mapas,draft.mapa)}</select><p>Selecionar município: recurso ainda em desenvolvimento. Os estados abaixo registram suas regiões de interesse.</p><div class="selecao">${Object.entries(S.estados).map(([id,title]) => `<label class="linha"><input type="checkbox" name="estado" value="${id}"${draft.estados.includes(id) ? ' checked' : ''}>${esc(title)} (${id})</label>`).join('')}</div></fieldset><button>Salvar minhas escolhas</button></form><p class="aviso">Nenhum download será iniciado ao salvar. Tamanhos reais aparecerão quando o catálogo validado estiver disponível.</p>`;
    document.querySelectorAll('[name=perfil]').forEach(r => r.onchange = () => {
      const p = S.perfis[r.value]; $('#modelo').value = p.modelo; $('#mapa').value = p.mapa;
      document.querySelectorAll('[name=wiki]').forEach(w => w.checked = w.value === p.wiki);
    });
    $('#escolhas').onsubmit = async e => {
      e.preventDefault();
      try { S.escolhas = await api('choices',{perfil:$('[name=perfil]:checked').value,modelo:$('#modelo').value,mapa:$('#mapa').value,wikis:[...document.querySelectorAll('[name=wiki]:checked')].map(e=>e.value),estados:[...document.querySelectorAll('[name=estado]:checked')].map(e=>e.value)}); notice('Escolhas salvas neste computador. Nenhum download iniciado.'); } catch(e) { failure(e); }
    };
  }
  async function importar(tipo) {
    const result = await api('import',{tipo});
    if (!result.cancelado) { S=await api('state'); notice('Arquivo local aberto. O original permanece na pasta escolhida.'); route(); }
  }
  function enciclopedias() {
    $('#conteudo').innerHTML = `<p class="tag">Conhecimento offline</p><h1>Sua enciclopédia,<br>no seu computador.</h1><p class="intro">Abra um arquivo ZIM já baixado. Esta primeira versão pesquisa uma enciclopédia por vez e mostra os artigos em texto, sem imagens.</p><button id="abrirZim">Abrir enciclopédia .zim</button><p>Arquivo: ${esc(S.arquivos.zim || 'nenhum selecionado')}</p><form id="buscarZim"><label for="termoZim">Pesquisar na enciclopédia</label><input id="termoZim" type="search" required maxlength="200"><div class="acoes"><button${!S.arquivos.zim ? ' disabled' : ''}>Pesquisar</button></div></form><div id="resultadosZim"></div>`;
    $('#abrirZim').onclick=()=>importar('zim').catch(failure);
    $('#buscarZim').onsubmit=async e=>{
      e.preventDefault(); const button=$('#buscarZim button');button.disabled=true;
      try {
        const results=await api('search-zim',{busca:$('#termoZim').value});
        $('#resultadosZim').innerHTML=results.length ? results.map((r,i)=>`<p><button class="secundario" data-zim="${i}">${esc(r.titulo)}</button></p>`).join('') : '<p>Nenhum artigo encontrado.</p>';
        document.querySelectorAll('[data-zim]').forEach(b=>b.onclick=async()=>{
          try{const article=await api('article-zim',{entrada:results[Number(b.dataset.zim)].entrada});$('#resultadosZim').innerHTML='<article><h2>'+esc(article.titulo)+'</h2><p class="resposta">'+esc(article.texto)+'</p></article>';}catch(e){failure(e);}
        });
      }catch(e){failure(e);}finally{button.disabled=false;}
    };
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
  function ia() {
    $('#conteudo').innerHTML = `<p class="tag">Assistente local · experimental</p><h1>Pergunte aos<br>guias da biblioteca.</h1><p class="intro">O modelo roda neste computador. Respostas podem conter erros: confira as referências, principalmente em situações de emergência.</p><div class="painel"><p>Motor local: <b>${S.ia.motor ? 'disponível' : 'não instalado'}</b> · Modelo: <b>${S.ia.modelo ? 'disponível' : 'não baixado'}</b></p><p>Qwen3 0.6B Q8 · cerca de 640 MB · CPU · contexto de 2.048 tokens.</p><button id="baixar" class="secundario">Baixar ou retomar modelo</button><p>Somente este botão acessa a internet para obter o modelo. O download verifica a integridade do arquivo.</p></div><form id="pergunta"><label for="texto">Sua pergunta</label><textarea id="texto" maxlength="1500" required placeholder="Como começar a organizar minha preparação?"></textarea><div class="acoes"><button id="enviar"${!S.ia.motor || !S.ia.modelo ? ' disabled' : ''}>Perguntar à IA</button><button type="button" class="secundario" id="buscar">Consultar guias sem IA</button></div></form><div id="resposta" class="resposta" aria-live="polite"></div>`;
    $('#buscar').onclick = () => { location.hash = 'biblioteca'; };
    $('#baixar').onclick = async () => { if (!confirm('Baixar o modelo de aproximadamente 640 MB? O arquivo ficará neste computador.')) return; try { await api('download-model',{}); poll(); } catch(e) { failure(e); } };
    $('#pergunta').onsubmit = async e => { e.preventDefault(); try { await api('ask',{pergunta:$('#texto').value}); $('#enviar').disabled = true; poll(); } catch(e) { failure(e); } };
    api('job').then(j => { if (['executando','baixando'].includes(j.estado)) poll(); }).catch(failure);
  }
  async function poll() {
    clearTimeout(timer);
    try {
      const j = await api('job');
      if (j.estado === 'executando' || j.estado === 'baixando') {
        notice(j.estado === 'baixando' ? `${j.fase}: ${Math.round(100*j.feito/j.total)}%` : 'A IA está trabalhando neste computador…'); timer = setTimeout(poll,1000); return;
      }
      notice(j.estado === 'erro' ? j.mensagem : j.mensagem || 'Resposta concluída. Confira as referências.');
      S = await api('state');
      if ($('#resposta') && j.resposta) { $('#resposta').textContent = j.resposta + '\n\nGuias consultados: ' + j.fontes.join(', '); }
      if ($('#enviar')) $('#enviar').disabled = !S.ia.motor || !S.ia.modelo;
    } catch(e) { failure(e); }
  }
  window.addEventListener('hashchange',route);
  api('state').then(s => { S=s; $('#hardware').textContent = `${s.hardware.ram_bytes ? (s.hardware.ram_bytes/2**30).toFixed(1) + ' GB RAM' : 'RAM não identificada'} · ${s.hardware.arch} · offline`; route(); }).catch(failure);
})();
