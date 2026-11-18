'use strict';
(() => {
  const $ = s => document.querySelector(s);
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  let S, timer, chatPending = '', chatBusy = false, mapFocus;
  let libraryQuery = '', libraryResults, zimQuery = '', zimCollection = '', zimResults;
  let offlineReport;
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
    window.ULMapas?.close();
    const page = location.hash.slice(1) || (S.escolhas ? 'biblioteca' : 'instalacao');
    document.querySelectorAll('nav a').forEach(a => { a.removeAttribute('aria-current'); if (a.hash === '#' + page) a.setAttribute('aria-current','page'); });
    if (page === 'downloads') downloads(); else if (page === 'enciclopedias') enciclopedias(); else if (page === 'mapas') mapas(); else if (page === 'compras') compras(); else if (page === 'instalacao') instalacao(); else if (page === 'fontes') fontes(); else if (page === 'ia') ia(); else if (page === 'offline') offline(); else biblioteca();
  }
  function biblioteca() {
    const pdfs = S.guias_pdf || [];
    $('#conteudo').innerHTML = `<h1>Biblioteca</h1>
      <p class="intro">Pesquise guias, PDFs, Wikipedia (enciclopédia) e lugares dos mapas instalados.</p>
      <form id="buscaBiblioteca"><label for="busca">Buscar na biblioteca offline</label>
      <input id="busca" type="search" required maxlength="160" value="${esc(libraryQuery)}"><button>Buscar</button></form>
      <div id="buscaResultados" aria-live="polite"></div>
      ${situacoesHtml(pdfs)}
      <section aria-label="Guias em PDF"><h2>Guias em PDF</h2><div class="cards">
      ${pdfs.map(g => `<article><h3>${esc(g.titulo)}</h3><button data-pdf="${esc(g.id)}">Ler PDF</button></article>`).join('')}
      </div></section><section aria-label="Guias em texto"><h2>Guias em texto</h2><div class="cards" id="guias">
      ${S.guias.map(g => `<article><h3>${esc(g.titulo)}</h3><button data-guide="${esc(g.id)}">Ler guia</button></article>`).join('')}
      </div></section>`;
    document.querySelectorAll('[data-pdf-situacao]').forEach(button => {
      button.onclick = () => pdfGuide(button.dataset.pdfSituacao, Number(button.dataset.pagina));
    });
    bindResources();
    document.querySelectorAll('[data-pdf]').forEach(button => button.onclick = () => pdfGuide(button.dataset.pdf));
    document.querySelectorAll('[data-guide]').forEach(button => button.onclick = () => guide(button.dataset.guide));
    const form = $('#buscaBiblioteca'), target = $('#buscaResultados');
    if (libraryResults) drawLibraryResults(target, libraryResults);
    form.onsubmit = async event => {
      event.preventDefault();
      const query = $('#busca').value.trim();
      if (!query) return;
      const send = form.querySelector('button');
      send.disabled = true;
      target.textContent = 'Pesquisando nos arquivos locais…';
      try {
        const results = await api('search-offline', {busca:query});
        if (!target.isConnected) return;
        libraryQuery = query;
        libraryResults = results;
        drawLibraryResults(target, results);
      } catch(error) {
        if (target.isConnected) target.textContent = error.message;
      } finally { send.disabled = false; }
    };
  }

  function drawLibraryResults(target, results) {
    const groups = [
      ['Guias', results.guias, item => item.titulo, item => guide(item.id)],
      ['PDFs', results.pdfs, item => item.titulo + ' · página ' + item.pagina, item => pdfGuide(item.id, item.pagina)],
      ['Wikipedia (enciclopédia)', results.zim, item => item.titulo + ' · ' + item.nome_colecao, item => openArticle(item, biblioteca)],
      ['Lugares', results.mapas, item => item.nome + ' · ' + item.nome_mapa, openPlace],
    ];
    target.replaceChildren();
    if (!groups.some(([, items]) => items.length)) target.textContent = 'Nenhum resultado nos arquivos locais.';
    for (const [label, items, title, open] of groups) {
      if (!items.length) continue;
      const heading = document.createElement('h2'), list = document.createElement('ul');
      heading.textContent = label;
      for (const item of items) {
        const row = document.createElement('li'), button = document.createElement('button');
        button.className = 'secundario';
        button.textContent = title(item);
        button.onclick = () => Promise.resolve(open(item)).catch(failure);
        row.append(button);
        list.append(row);
      }
      target.append(heading, list);
    }
    if (results.indisponiveis.length) {
      const p = document.createElement('p');
      p.textContent = 'Arquivos que ficaram fora da busca: ' + results.indisponiveis.map(item => item.nome).join(', ') + '.';
      target.append(p);
    }
  }

  async function openPlace(place) {
    await api('select-map', {id:place.mapa_id});
    S = await api('state');
    mapFocus = place;
    location.hash = 'mapas';
  }

  function situacoesHtml(pdfs) {
    const situations = S.situacoes || [];
    if (!situations.length) return '';
    return `<section aria-labelledby="situacoes-titulo"><h2 id="situacoes-titulo">Guias por situação</h2>
      <p>Leia o resumo e os guias deste computador sem internet. Os botões de referência abrem o navegador.</p>
      <div class="cards">${situations.map(situation => `<article data-situacao="${esc(situation.id)}">
        <h3>${esc(situation.titulo)}</h3><p>${esc(situation.resumo)}</p>
        <p><small>Revisão editorial em <time datetime="${esc(situation.revisado)}">${esc(situation.revisado.split('-').reverse().join('/'))}</time></small></p>
        <ul>${situation.leituras.map(ref => {
          const guide = pdfs.find(item => item.id === ref.id);
          return guide ? `<li><button class="secundario" data-pdf-situacao="${esc(ref.id)}" data-pagina="${esc(ref.pagina)}">${esc(guide.titulo)} · página ${esc(ref.pagina)}</button></li>` : '';
        }).join('')}
        ${situation.fontes.map(source => `<li><button class="secundario" data-open-resource="${esc(source.id)}">${esc(source.titulo)} · internet</button></li>`).join('')}</ul>
      </article>`).join('')}</div></section>`;
  }

  function bindResources() {
    document.querySelectorAll('[data-open-resource]').forEach(button => {
      button.onclick = () => api('open-resource', {id:button.dataset.openResource})
        .then(result => notice(result.mensagem)).catch(failure);
    });
  }

  function pdfGuide(id, page) {
    const guide = (S.guias_pdf || []).find(item => item.id === id);
    if (!guide) return;
    const texts = guide.texto_paginas || [];
    $('#conteudo').innerHTML = `<button class="secundario" id="voltar">← Biblioteca</button>
      <h1>${esc(guide.titulo)}</h1><p>${esc(guide.descricao)}</p>
      <button id="abrirPdf">Abrir arquivo PDF no leitor do sistema</button>
      ${texts.length ? `<section class="texto-pdf" aria-label="Texto selecionável">
        ${texts.map((text, i) => `<article tabindex="-1"><h2>Página ${i + 1} de ${texts.length}</h2>
          ${text.split('\n\n').map(paragraph => `<p>${esc(paragraph)}</p>`).join('')}</article>`).join('')}
      </section>` : ''}
      <details class="paginas-pdf"${texts.length ? '' : ' open'}>
        <summary>Ver imagens das páginas</summary>
        ${guide.paginas.map((image, i) => `<figure><figcaption>Página ${i + 1} de ${guide.paginas.length}</figcaption>
        <img src="${esc(image)}" alt="Página ${i + 1} de ${esc(guide.titulo)}" loading="lazy"></figure>`).join('')}
      </details>`;
    $('#voltar').onclick = biblioteca;
    if (page) {
      const target = document.querySelectorAll('.texto-pdf article')[page - 1];
      if (target) { target.focus({preventScroll:true}); target.scrollIntoView({block:'start'}); }
    }
    $('#abrirPdf').onclick = () => api('open-pdf', {id}).then(result => notice(result.mensagem)).catch(failure);
  }

  function guide(id) {
    const g = S.guias.find(x => x.id === id); if (!g) return;
    $('#conteudo').innerHTML = `<button class="secundario" id="voltar">← Biblioteca</button><p class="tag">${esc(g.categoria)}</p><h1>${esc(g.titulo)}</h1><article><p>${esc(g.texto)}</p><p class="fonte">Referência: ${esc(g.fonte)}<br>Endereço para consultar enquanto houver internet:<code>${esc(g.url)}</code></p></article>`;
    $('#voltar').onclick = biblioteca;
  }
  function fontes(){
    const resources=S.recursos||[],categories=[...new Set(resources.map(r=>r.categoria))];
    $('#conteudo').innerHTML=`<p class="tag">Aprenda enquanto há conexão</p><h1>Fontes para estudar.<br>Pessoas para conhecer.</h1><p class="intro">O diretório e seus endereços ficam neste computador. Abrir as páginas usa seu navegador e requer internet. Não há cópia de vídeos, assinatura de canais ou participação automática em grupos.</p><div class="painel"><h2>Antes de ficar offline</h2><p>Baixe sua biblioteca e mapas; abra os arquivos e teste a consulta sem conexão. Carregue seus aparelhos, confira cópias e mantenha contatos essenciais também em papel. Conheça grupos locais e teste seus equipamentos com outras pessoas.</p></div><label for="categoriaFonte">Tema</label><select id="categoriaFonte"><option value="">Todos os temas</option>${categories.map(c=>`<option>${esc(c)}</option>`).join('')}</select><label for="buscaFonte">Buscar fonte ou comunidade</label><input id="buscaFonte" type="search" placeholder="LoRa, água, canais…"><div class="cards" id="listaFontes"></div><p>Fontes oficiais, comunidades e criadores têm papéis distintos. A inclusão no diretório não aprova todos os conteúdos publicados nem estabelece parceria comercial.</p>`;
    function draw(){
      const fold=s=>s.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase(),query=fold($('#buscaFonte').value),category=$('#categoriaFonte').value;
      const hits=resources.filter(r=>(!category||r.categoria===category)&&fold(r.nome+' '+r.resumo+' '+r.categoria).includes(query));
      $('#listaFontes').innerHTML=hits.length?hits.map(r=>`<article data-resource="${esc(r.id)}"><p class="tag">${esc(r.tipo)}</p><h2>${esc(r.nome)}</h2><p>${esc(r.resumo)}</p><p>${esc(r.observacao)}</p><p class="fonte">Verificado em ${esc(r.revisado)}<br><code>${esc(r.url)}</code></p><button data-open-resource="${esc(r.id)}">Abrir no navegador · internet</button></article>`).join(''):'<p>Nenhuma referência encontrada.</p>';
      bindResources();
    }
    $('#buscaFonte').oninput=draw;$('#categoriaFonte').onchange=draw;draw();
  }
  function compras() {
    $('#conteudo').innerHTML = `<p class="tag">Minha preparação</p><h1>Comece pelo que<br>você já tem.</h1><p class="intro">Marque os itens disponíveis em casa. Suas escolhas são salvas neste computador. Quantidades dependem das pessoas, dos dias e dos riscos da sua região.</p><div class="painel">${S.compras.map(i => `<label class="linha${i.feito ? ' feito' : ''}"><input type="checkbox" data-item="${i.id}"${i.feito ? ' checked' : ''}><span><b>${esc(i.titulo)}</b><br><small>${esc(i.grupo)}</small></span></label>`).join('')}</div><section class="painel"><h2>Se prepare enquanto há tempo</h2><p>Compare opções de energia, água e primeiros socorros no site. O guia abre no navegador e pode pedir acesso.</p><button data-open-resource="ultimo-livro-preparacao">Abrir guia no navegador · internet</button></section>`;
    bindResources();
    document.querySelectorAll('[data-item]').forEach(input => input.onchange = async () => {
      input.disabled = true;
      try { S.compras = await api('check',{id:input.dataset.item,feito:input.checked}); input.closest('label').classList.toggle('feito',input.checked); }
      catch(e) { input.checked = !input.checked; failure(e); } finally { input.disabled = false; }
    });
  }
  function instalacao() {
    const first = !S.escolhas, hardware = S.hardware, recommended = S.perfis[S.recomendado];
    const ram = hardware.ram_bytes ? (hardware.ram_bytes/2**30).toLocaleString('pt-BR',{maximumFractionDigits:1})+' GiB de RAM detectada' : 'RAM não identificada';
    const cpu = hardware.processadores_logicos ? ' · '+hardware.processadores_logicos+' processadores lógicos' : '';
    const weak = !hardware.ram_bytes || hardware.ram_bytes < 7*2**30;
    const draft = S.escolhas || {perfil:'leve', modelo:'sem-ia', wikis:['pt-mini'],
      mapa:'municipio', estados:[], municipios:[]};
    const selected = new Set(draft.municipios || []), mapItems = new Map();
    let request = 0, offset = 0, total = 0;
    $('#conteudo').innerHTML = `<p class="tag">Brasil inteiro, escolhas locais</p><h1>${first?'Escolha o que baixar':'Minha instalação'}</h1><p class="intro">Os arquivos começam a baixar após sua confirmação.</p><div class="painel" id="recomendacaoInstalacao"><h2>${first?'Comece pela biblioteca':'Perfil sugerido: '+esc(recommended.nome)}</h2><p>${esc(ram+cpu)} · ${esc(hardware.arch)} · ${size(hardware.livre_bytes)} livres no disco.</p><p>${weak?'Comece pelos guias, enciclopédias e mapas. Você ainda pode selecionar o modelo Leve se houver memória suficiente.':'A sugestão usa a RAM detectada. Para notebooks com cerca de 8 GB, o perfil Leve é o ponto de partida. A velocidade da IA depende do processador.'}</p>${first?'<p>Para começar, sugerimos a edição Mini em português e um mapa do seu município. Escolha a cidade abaixo. A IA é opcional e o modelo Leve ocupa cerca de 640 MB.</p><button id="somenteGuias" type="button" class="secundario">Abrir biblioteca sem baixar agora</button>':''}</div><button id="importarPlano" class="secundario">Importar plano do site (.json)</button><form id="escolhas"><div class="cards">${Object.entries(S.perfis).map(([id,p]) => `<label class="card perfil"><input type="radio" name="perfil" value="${id}"${draft.perfil === id ? ' checked' : ''}><h2>${p.nome}</h2><p>${p.ram_gib ? p.ram_gib + ' GB de RAM como alvo' : 'Você escolhe os componentes'}${S.recomendado === id ? ' · sugerido' : ''}</p></label>`).join('')}</div><fieldset><legend>IA local</legend><label for="modelo">Modelo</label><select id="modelo">${options(S.modelos,draft.modelo)}</select><p>O menor modelo ocupa cerca de 640 MB. O desempenho depende do processador; os modelos maiores exigem mais memória.</p></fieldset><fieldset><legend>Wikipedia (enciclopédia)</legend>${Object.entries(S.wikis).map(([id,title]) => `<label class="linha"><input type="checkbox" name="wiki" value="${id}"${draft.wikis.includes(id) ? ' checked' : ''}><span>${esc(title)}<br><small>${size(S.catalogo[id].size)} · edição ${esc(S.catalogo[id].edition)}</small></span></label>`).join('')}<p>Mini: introduções e quadros. Sem imagens: artigos completos em texto. Completa: arquivo com imagens; o leitor atual exibe os artigos em texto.</p></fieldset><fieldset><legend>Mapas offline</legend><label for="mapa">Abrangência</label><select id="mapa">${options(S.mapas,draft.mapa)}</select><p>Ruas, água, localidades e serviços para consulta. Recortes por município e estado incluem o entorno delimitado pelo retângulo da região. Sem rotas automáticas, relevo ou informações em tempo real.</p><div id="mapaMunicipios"><label for="ufMunicipio">Estado para buscar municípios</label><select id="ufMunicipio"><option value="">Todo o Brasil</option>${options(S.estados,'')}</select><label for="buscaMunicipio">Nome do município</label><input id="buscaMunicipio" type="search" maxlength="100" placeholder="Ex.: Campinas"><p id="municipiosStatus" role="status"></p><div id="municipiosResultados" class="selecao"></div><button type="button" id="maisMunicipios" class="secundario">Próximos municípios</button><h3>Municípios escolhidos</h3><div id="municipiosSelecionados"></div></div><div id="mapaEstados" class="selecao">${Object.entries(S.estados).map(([id,title]) => `<label class="linha"><input type="checkbox" name="estado" value="${id}"${draft.estados.includes(id) ? ' checked' : ''}>${esc(title)} (${id})</label>`).join('')}</div><p id="mapaNacional">O mapa detalhado nacional inclui todos os estados e exige mais espaço, inclusive durante a montagem do arquivo.</p><p>Visão geral do Brasil incluída nas opções municipais e estaduais. Créditos: © contribuidores do OpenStreetMap, Geofabrik e IBGE. Licença ODbL 1.0.</p></fieldset><div class="aviso" id="estimativa" aria-live="polite"></div><ul id="resumoPacotes"></ul><div class="acoes"><button>Salvar escolhas</button><button type="button" id="instalar" disabled>Revisar e baixar seleção</button><a class="botao" href="#biblioteca">Abrir biblioteca</a></div></form><p><a href="#offline">Verificar uso offline e acessar backup</a></p>`;
    if ($('#somenteGuias')) $('#somenteGuias').onclick = async () => {
      try {
        await api('choices',{perfil:'personalizada',modelo:'sem-ia',wikis:[],mapa:'sem-mapas'});
        S=await api('state');
        location.hash='biblioteca';
        notice('Os guias já estão disponíveis. Você pode alterar suas escolhas em Minha instalação.');
      } catch(e) { failure(e); }
    };
    $('#importarPlano').onclick=()=>importar('plano').catch(failure);
    function values(){return {perfil:$('[name=perfil]:checked').value,modelo:$('#modelo').value,mapa:$('#mapa').value,wikis:[...document.querySelectorAll('[name=wiki]:checked')].map(e=>e.value),estados:[...document.querySelectorAll('[name=estado]:checked')].map(e=>e.value),municipios:[...selected]};}
    let estimateTimer, estimateRequest = 0;
    const summary = $('#estimativa'), installButton = $('#instalar');
    function estimate() {
      const choices = values();
      const ticket = ++estimateRequest;
      clearTimeout(estimateTimer);
      $('#mapaMunicipios').hidden = choices.mapa !== 'municipio';
      $('#mapaEstados').hidden = choices.mapa !== 'estado';
      $('#mapaNacional').hidden = choices.mapa !== 'brasil';
      installButton.disabled = true;
      summary.textContent = 'Calculando o espaço para esta seleção…';
      estimateTimer = setTimeout(async () => {
        try {
          const plan = await api('install-preview', choices);
          if (ticket !== estimateRequest || !summary.isConnected) return;
          renderPlan(plan, choices);
        } catch(error) {
          if (ticket === estimateRequest && summary.isConnected) summary.textContent = error.message;
        }
      }, 120);
    }
    function renderPlan(plan, choices) {
      const model = S.modelos[choices.modelo];
      const memoryWarning = model.ram_gib && S.hardware.ram_bytes &&
        S.hardware.ram_bytes < model.ram_gib * 2**30 * .94;
      summary.textContent = `A baixar: ${size(plan.download_bytes)}. Espaço necessário: ${size(plan.necessario_bytes)}. Livre: ${size(plan.livre_bytes)}.` +
        (plan.montagem_bytes ? ` Inclui ${size(plan.montagem_bytes)} para montar o mapa nacional.` : '') +
        (plan.espaco_suficiente ? '' : ' Reduza a seleção ou libere espaço para continuar.') +
        (memoryWarning ? ' O modelo escolhido recomenda mais RAM do que foi detectada.' : '');
      const list = $('#resumoPacotes');
      list.replaceChildren();
      for (const item of plan.pacotes) {
        const row = document.createElement('li');
        const label = S.wikis[item.id] || S.modelos[item.id]?.nome || item.name || item.id;
        row.textContent = `${label} · ${item.instalado ? 'já instalado' : size(item.size) + (item.parcial_bytes ? ' · ' + size(item.parcial_bytes) + ' em disco' : '')}`;
        list.append(row);
      }
      installButton.disabled = !plan.espaco_suficiente || plan.pacotes.every(item => item.instalado);
    }
    function drawSelected(){
      const out=$('#municipiosSelecionados');out.replaceChildren();
      if(!selected.size)out.textContent='Nenhum município escolhido. Você pode baixar somente a visão geral ou escolher sua cidade.';
      for(const code of selected){const p=mapItems.get('map-city-'+code)||S.catalogo['map-city-'+code],b=document.createElement('button');b.type='button';b.className='secundario';b.textContent=(p?p.name+' · '+size(p.size):code)+' · remover';b.onclick=()=>{selected.delete(code);drawSelected();searchCities(offset);estimate();};out.append(b);}
    }
    async function searchCities(start=0){
      const ticket=++request;
      try{
        const data=await api('map-catalog',{uf:$('#ufMunicipio').value,busca:$('#buscaMunicipio').value,offset:start,selecionados:[...selected]});
        if(ticket!==request||!$('#municipiosResultados'))return;
        for(const p of [...data.resultados,...data.estados,...(data.nacionais||[]),...(data.selecionados||[])])mapItems.set(p.id,p);
        offset=start;total=data.total;$('#municipiosStatus').textContent=data.disponivel?`${total} municípios encontrados · mostrando ${total?start+1:0} a ${Math.min(start+50,total)}.`:'Catálogo ainda em preparação. É possível importar mapas locais na seção Mapas.';
        $('#maisMunicipios').hidden=start+50>=total;
        $('#municipiosResultados').innerHTML=data.resultados.map(p=>`<label class="linha"><input type="checkbox" data-city="${esc(p.code)}"${selected.has(p.code)?' checked':''}><span>${esc(p.name)}<br><small>${size(p.size)}</small></span></label>`).join('');
        document.querySelectorAll('[data-city]').forEach(b=>b.onchange=()=>{b.checked?selected.add(b.dataset.city):selected.delete(b.dataset.city);drawSelected();estimate();});drawSelected();
      }catch(e){failure(e);}
    }
    $('#ufMunicipio').onchange=()=>searchCities();let debounce;
    $('#buscaMunicipio').oninput=()=>{clearTimeout(debounce);debounce=setTimeout(()=>searchCities(),200);};
    $('#maisMunicipios').onclick=()=>searchCities(offset+50);
    document.querySelectorAll('[name=perfil]').forEach(r => r.onchange = () => {const p=S.perfis[r.value];$('#modelo').value=p.modelo;$('#mapa').value=p.mapa;document.querySelectorAll('[name=wiki]').forEach(w=>w.checked=w.value===p.wiki);estimate();});
    $('#escolhas').addEventListener('change',estimate);estimate();drawSelected();searchCities();
    async function save(choices=values()){await api('choices',choices);S=await api('state');offlineReport=undefined;}
    $('#escolhas').onsubmit=async e=>{e.preventDefault();try{await save();estimate();notice('Escolhas salvas. O download começa apenas quando você pedir.');}catch(e){failure(e);}};
    installButton.onclick = async () => {
      installButton.disabled = true;
      const choices = values();
      try {
        const plan = await api('install-preview', choices);
        if (!summary.isConnected) return;
        renderPlan(plan, choices);
        if (installButton.disabled || !confirm(`Baixar ${size(plan.download_bytes)} da seleção? São necessários ${size(plan.necessario_bytes)} livres no disco.`)) return;
        installButton.disabled = true;
        await save(choices);
        await begin('install-selected', {});
      } catch(error) { failure(error); }
      finally { if (summary.isConnected) estimate(); }
    };
  }
  async function begin(path,body,question){
    if(question && !confirm(question))return;
    await api(path,body);S=await api('state');location.hash='downloads';downloads();poll();
  }
  async function downloads(){
    S=await api('state');
    if(location.hash!=='#downloads')return;
    $('#conteudo').innerHTML=`<p class="tag">Sua biblioteca, verificada</p><h1>Baixe agora.<br>Consulte depois.</h1><p class="intro">Arquivos oficiais, com tamanho e checksum fixados nesta versão. Você pode pausar downloads e retomá-los depois; a biblioteca instalada continua acessível.</p><div class="painel"><p id="andamento" role="status">Consultando andamento…</p><div class="acoes"><button id="pausar" class="secundario">Pausar download</button><button id="retomar">Retomar instalação pendente</button></div></div><div class="cards">${Object.entries(S.catalogo).map(([id,p])=>`<article><p class="tag">${p.kind==='zim'?'Enciclopédia':p.kind==='map'?'Mapa':'IA local'}</p><h3>${esc(p.kind==='zim'?S.wikis[id]:p.kind==='map'?p.name:S.modelos[id].nome)}</h3><p>${size(p.size)}${p.edition?' · '+esc(p.edition):''}<br>${p.instalado?'Verificado e instalado':p.parcial_bytes?'Parcial: '+size(p.parcial_bytes):'Ainda não instalado'}</p><details><summary>Fonte e licença</summary><p>${esc(p.source)}<br>${esc(p.license)}</p><p class="fonte">Arquivo: ${esc(p.file)}<br>SHA-256: ${esc(p.sha256)}</p></details><button data-package="${id}" class="secundario">${p.instalado?'Verificar arquivo':'Baixar ou retomar'}</button></article>`).join('')}</div>`;
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
    if (!result.cancelado) { S=await api('state'); offlineReport = undefined; libraryResults = undefined; zimResults = undefined; notice(tipo==='plano'?'Plano importado. Nenhum download iniciado.':'Arquivo local aberto. O original permanece na pasta escolhida.'); route(); }
  }
  function enciclopedias(){
    const books=S.enciclopedias || [];
    $('#conteudo').innerHTML=`<p class="tag">Conhecimento offline</p><h1>Wikipedia (enciclopédia)</h1><p class="intro">Pesquise várias enciclopédias instaladas ou filtre uma coleção. Os artigos são apresentados em texto. Cada edição mantém seus autores, créditos e licenças.</p><div class="acoes"><button id="abrirZim">Importar arquivo .zim</button><a class="botao" href="#downloads">Baixar edições da Wikipedia</a></div><p>${books.length?books.map(b=>esc(b.nome)+(b.disponivel?'':' (disco desconectado)')).join('<br>'):'Nenhuma enciclopédia instalada. Baixe uma edição ou importe seu arquivo ZIM.'}</p><form id="buscarZim"><label for="colecaoZim">Pesquisar em</label><select id="colecaoZim"><option value="">Todas as coleções</option>${books.map(b=>`<option value="${esc(b.id)}">${esc(b.nome)}</option>`).join('')}</select><label for="termoZim">Palavra ou assunto</label><input id="termoZim" type="search" required maxlength="200"><div class="acoes"><button${!books.length?' disabled':''}>Pesquisar offline</button></div></form><div id="resultadosZim"></div>`;
    $('#abrirZim').onclick = () => importar('zim').catch(failure);
    $('#termoZim').value = zimQuery;
    if (books.some(book => book.id === zimCollection)) $('#colecaoZim').value = zimCollection;
    const target = $('#resultadosZim');
    if (zimResults) drawZim(target, zimResults);
    $('#buscarZim').onsubmit = async event => {
      event.preventDefault();
      const button = event.currentTarget.querySelector('button');
      button.disabled = true;
      const query = $('#termoZim').value, collection = $('#colecaoZim').value;
      try {
        const results = await api('search-zim', {busca:query, colecao:collection || null});
        if (!target.isConnected) return;
        zimQuery = query;
        zimCollection = collection;
        zimResults = results;
        drawZim(target, results);
      } catch(error) { failure(error); }
      finally { button.disabled = false; }
    };
  }

  function drawZim(target, data) {
    target.innerHTML = (data.indisponiveis.length ? `<p>Não foi possível pesquisar: ${esc(data.indisponiveis.join(', '))}.</p>` : '') +
      (data.resultados.length ? data.resultados.map((result, i) =>
        `<p><button class="secundario" data-zim="${i}">${esc(result.titulo)}</button> ${esc(result.nome_colecao)}</p>`).join('') :
        '<p>Nenhum artigo encontrado.</p>');
    target.querySelectorAll('[data-zim]').forEach(button => {
      button.onclick = () => openArticle(data.resultados[Number(button.dataset.zim)], enciclopedias).catch(failure);
    });
  }

  async function openArticle(source, back) {
    const page = location.hash;
    const article = await api('article-zim', {colecao:source.colecao, entrada:source.entrada});
    if (location.hash !== page) return;
    $('#conteudo').innerHTML = `<button class="secundario" id="voltarZim">← Voltar</button>
      <article><h1>${esc(article.titulo)}</h1><p class="fonte">${esc(source.nome_colecao || source.colecao)} · artigo ${esc(source.entrada)}</p>
      <p class="resposta">${esc(article.texto)}</p></article>`;
    $('#voltarZim').onclick = back || (() => { location.hash = 'enciclopedias'; enciclopedias(); });
  }
  async function mapas(){
    const maps=S.mapas_instalados || [];
    $('#conteudo').innerHTML=`<p class="tag">Orientação offline</p><h1>Encontre seu caminho,<br>mesmo sem conexão.</h1><p class="intro">Mapas locais de ruas, água, localidades e pontos de interesse. Use o mouse, arraste ou navegue com as setas do teclado. Os mapas são históricos: não mostram bloqueios, riscos ou atendimento em tempo real.</p><div class="acoes"><button id="abrirMapa">Importar mapa local</button><a class="botao" href="#instalacao">Escolher mapas para baixar</a></div><label for="mapaEscolhido">Mapa instalado</label><select id="mapaEscolhido">${maps.length?maps.map(m=>`<option value="${esc(m.id)}"${m.id===S.mapa_ativo?' selected':''}>${esc(m.nome)}${m.disponivel?'':' (disco desconectado)'}</option>`).join(''):'<option>Nenhum mapa instalado</option>'}</select><div id="mapaLocal"></div>`;
    $('#abrirMapa').onclick=()=>importar('mapa').catch(failure);
    $('#mapaEscolhido').onchange=async()=>{try{await api('select-map',{id:$('#mapaEscolhido').value});S=await api('state');mapas();}catch(e){failure(e);}};
    if(!maps.length)return;
    try{
      const info=await api('mapa');if(!$('#mapaLocal'))return;
      const vector=info.formato==='ulmap';
      $('#mapaLocal').innerHTML=`${vector?'<form id="mapaBusca"><label for="mapaTermo">Localidade, rua ou serviço neste mapa</label><input id="mapaTermo" type="search" required maxlength="160"><button>Buscar offline</button></form><div id="mapaResultados" class="acoes"></div>':''}<div class="acoes"><button data-map-move="-1,0" aria-label="Oeste">←</button><button data-map-move="0,-1" aria-label="Norte">↑</button><button data-map-move="0,1" aria-label="Sul">↓</button><button data-map-move="1,0" aria-label="Leste">→</button><button id="mapaMais" aria-label="Aproximar">+</button><button id="mapaMenos" aria-label="Afastar">−</button></div>${vector?'<div class="mapa-camadas">'+[['road','Ruas'],['water','Água'],['place','Localidades'],['poi','Serviços']].map(([id,label])=>`<label><input type="checkbox" data-map-layer="${id}" checked>${label}</label>`).join('')+'</div>':''}<canvas id="mapaCanvas" tabindex="0" role="img" aria-label="Mapa offline. Setas para mover, mais e menos para aproximar. A busca lista lugares como texto."></canvas><p id="mapaEstado" role="status"></p><p id="mapaDetalhe" aria-live="polite"></p><p class="fonte">${esc(info.nome)}${info.data?' · '+esc(info.data):''}<br>${esc(info.atribuicao)}${info.licenca?' · '+esc(info.licenca):''}<br>${esc(info.licenca_url||'')}</p>`;
      window.ULMapas.open(info, {api, notice, focus:mapFocus});
      if (mapFocus) $('#mapaDetalhe').textContent = mapFocus.nome + ' · ' + mapFocus.nome_mapa;
      mapFocus = undefined;
    }catch(e){failure(e);}
  }
  function offline() {
    $('#conteudo').innerHTML = `<h1>Verificar uso offline</h1>
      <p class="intro">O teste abre os arquivos locais e, quando possível, faz uma resposta curta com a IA. Pode levar alguns segundos. Nenhum download é iniciado.</p>
      <button id="verificarOffline">Verificar agora</button><div id="resultadoOffline" aria-live="polite"></div>
      ${S.backup_disponivel ? `<section class="painel"><h2>Backup e recuperação</h2>
      <p>Salve suas escolhas e o checklist em um arquivo. Use o seletor de pasta para salvar em um pendrive. Incluir o chat grava perguntas e respostas no backup.</p>
      <label class="linha"><input type="checkbox" id="incluirChat"> Incluir histórico do chat</label>
      <div class="acoes"><button id="exportarBackup">Exportar backup</button>
      <button id="restaurarBackup" class="secundario">Restaurar backup</button></div>
      <h3>Reconectar arquivos grandes</h3><p>Importe mapas e enciclopédias já salvos no computador ou em um disco externo.</p>
      <div class="acoes"><button class="secundario" id="reconectarWiki">Importar Wikipedia (.zim)</button>
      <button class="secundario" id="reconectarMapa">Importar mapa (.ulmap ou .mbtiles)</button></div></section>` : ''}`;
    const button = $('#verificarOffline');
    renderOfflineReport();
    button.onclick = async () => {
      button.disabled = true;
      try {
        await api('check-offline', {});
        offlineReport = undefined;
        $('#resultadoOffline').textContent = 'Verificando os arquivos locais…';
        poll();
      } catch(error) {
        failure(error);
        button.disabled = false;
      }
    };
    api('job').then(job => {
      if (!button.isConnected) return;
      button.disabled = ['executando', 'baixando'].includes(job.estado);
      if (button.disabled) poll();
    }).catch(failure);
    if (S.backup_disponivel) {
      $('#exportarBackup').onclick = () => backup('exportar');
      $('#restaurarBackup').onclick = () => backup('restaurar');
      $('#reconectarWiki').onclick = () => importar('zim').catch(failure);
      $('#reconectarMapa').onclick = () => importar('mapa').catch(failure);
    }
  }

  function renderOfflineReport() {
    const out = $('#resultadoOffline');
    if (!out || !offlineReport) return;
    const labels = {ok:'Pronto', pendente:'Pendente', ignorado:'Opcional', erro:'Precisa de atenção'};
    out.innerHTML = `<ul>${offlineReport.map(item =>
      `<li><strong>${esc(item.titulo)} · ${esc(labels[item.estado])}</strong><br>${esc(item.mensagem)}</li>`).join('')}</ul>`;
  }

  async function backup(action) {
    const restore = action === 'restaurar';
    if (restore && !confirm('Restaurar escolhas e checklist do arquivo? Se ele contiver chat, também substituirá o histórico atual.')) return;
    const buttons = [$('#exportarBackup'), $('#restaurarBackup')];
    buttons.forEach(button => button.disabled = true);
    try {
      const result = await api('backup', {acao:action, incluir_chat:$('#incluirChat').checked});
      if (result.cancelado) return;
      if (restore) {
        S = await api('state');
        offlineReport = undefined;
        route();
      }
      notice(result.mensagem);
    } catch(error) { failure(error); }
    finally { buttons.forEach(button => button.disabled = false); }
  }

  function stopControl(job) {
    const button = $('#pararResposta');
    if (button) button.disabled = !job.cancelavel;
  }

  function memoryLine() {
    const target = $('#memoriaIA'), memory = S.hardware.ram_disponivel_bytes;
    if (!target) return;
    target.textContent = (memory == null ? 'RAM disponível não identificada.' :
      'RAM disponível: ' + (memory/2**30).toLocaleString('pt-BR', {maximumFractionDigits:1}) + ' GiB.') +
      ' Mínimo para esta IA: ' + S.ia.ram_necessaria_gib.toLocaleString('pt-BR') + ' GiB.';
  }

  function chatControls() {
    const send = $('#enviar');
    if (!send) return;
    const enabled = ((S.escolhas || {}).modelo || 'qwen3-0.6b') !== 'sem-ia';
    send.disabled = chatBusy || !enabled || !S.ia.motor || !S.ia.modelo;
    const reset = $('#novaConversa');
    reset.disabled = chatBusy || !$('#turnosChat').querySelector('.turno-chat');
    $('#chatPendente').textContent = chatPending ? 'Processando: ' + chatPending : '';
  }
  async function refreshChat() {
    const container = $('#turnosChat');
    if (!container) return;
    const {history} = await api('chat');
    if (!container.isConnected) return;
    container.replaceChildren();
    for (const item of history) {
      const turn = document.createElement('article');
      turn.className = 'turno-chat';
      turn.innerHTML = `<h3>Você</h3><p class="mensagem-chat">${esc(item.pergunta)}</p><h3>Assistente local</h3><p class="resposta mensagem-chat">${esc(item.resposta)}</p>`;
      const sources = document.createElement('div');
      sources.className = 'referencias-chat acoes';
      for (const source of item.fontes) {
        const button = document.createElement('button');
        button.type = 'button'; button.className = 'secundario';
        button.textContent = source.ref + ' · ' + source.titulo;
        button.onclick = () => {
          if (source.tipo === 'zim') openArticle(source).catch(failure);
          else if (source.tipo === 'guia') guide(source.id);
        };
        sources.append(button);
      }
      if (!item.fontes.length) sources.textContent = 'Sem referência local nesta resposta.';
      turn.append(sources); container.append(turn);
    }
    chatControls();
  }
  function ia(){
    const selected=(S.escolhas || {}).modelo || 'qwen3-0.6b',enabled=selected!=='sem-ia',spec=S.catalogo[selected];
    $('#conteudo').innerHTML=`<p class="tag">Assistente local · experimental</p><h1>Converse com sua biblioteca</h1><p class="intro">Faça perguntas de seguimento. O assistente usa os turnos recentes, e suas conversas ficam neste computador. Confira as referências antes de agir.</p><div class="painel"><p>Motor: <b>${S.ia.motor?'disponível':'não instalado'}</b> · Modelo: <b>${enabled?esc(S.modelos[selected].nome):'desativado'}</b></p>${enabled?`<p>${size(spec.size)} · contexto de ${spec.context.toLocaleString('pt-BR')} tokens · ${spec.ram_gib} GB RAM como alvo.</p><p id="memoriaIA"></p><button id="baixar" class="secundario">Baixar ou verificar modelo selecionado</button>`:'<p>Escolha um modelo em Minha instalação para ativar o assistente.</p>'}</div><div class="acoes"><button type="button" class="secundario" id="novaConversa" disabled>Nova conversa</button><a class="botao" href="#biblioteca">Consultar guias</a></div><section id="turnosChat" aria-label="Histórico da conversa" aria-live="polite"></section><p id="chatPendente" class="mensagem-chat" role="status"></p><form id="pergunta"><label for="texto">Sua mensagem</label><textarea id="texto" maxlength="1500" required placeholder="O que você quer perguntar?"></textarea><div class="acoes"><button id="enviar" disabled>Enviar</button></div></form>`;
    memoryLine();
    api('memory').then(({ram_disponivel_bytes}) => {
      S.hardware.ram_disponivel_bytes = ram_disponivel_bytes;
      memoryLine();
    }).catch(failure);
    const stop = document.createElement('button');
    stop.type = 'button';
    stop.id = 'pararResposta';
    stop.className = 'secundario';
    stop.textContent = 'Parar resposta';
    stop.disabled = true;
    $('#enviar').after(stop);
    stop.onclick = async () => {
      stop.disabled = true;
      try {
        const result = await api('stop-answer', {});
        notice(result.mensagem);
        poll();
      } catch(error) { failure(error); }
    };
    if($('#baixar'))$('#baixar').onclick=()=>begin('install-package',{id:selected},`Baixar ou verificar o modelo selecionado (${size(spec.size)})?`).catch(failure);
    $('#novaConversa').onclick=async()=>{
      if(!confirm('Apagar o histórico desta conversa e começar outra?'))return;
      try {
        chatBusy=true;chatControls();
        await api('clear-chat',{});
        await refreshChat();notice('Nova conversa iniciada.');
      } catch(e){failure(e);}
      finally{chatBusy=false;chatControls();}
    };
    const form=$('#pergunta'), input=$('#texto');
    form.onsubmit=async e=>{
      e.preventDefault();
      if(chatBusy || !input.value.trim())return;
      chatBusy=true;chatPending=input.value.trim();chatControls();
      try {
        await api('ask',{pergunta:chatPending});
        input.value='';poll();
      } catch(e) {chatBusy=false;chatPending='';chatControls();failure(e);}
    };
    refreshChat().catch(failure);
    api('job').then(j=>{
      stopControl(j);
      if(['executando','baixando'].includes(j.estado)){chatBusy=true;chatControls();poll();}
      else if(!chatPending){chatBusy=false;chatControls();}
    }).catch(failure);
  }
  async function poll(){
    clearTimeout(timer);
    try{
      const j=await api('job');jobLine(j);stopControl(j);
      if(['executando','baixando'].includes(j.estado)){
        chatBusy=true;chatControls();
        notice(j.estado==='baixando'?`${j.fase}: ${j.nome || ''} · ${Math.round(100*j.feito/j.total)}%`:'Processando neste computador…');timer=setTimeout(poll,1000);return;
      }
      if(['erro','cancelado'].includes(j.estado) && chatPending && $('#texto') && !$('#texto').value)$('#texto').value=chatPending;
      chatPending='';chatBusy=false;
      S=await api('state');
      chatControls();
      memoryLine();
      if (j.verificacao_offline) offlineReport = j.verificacao_offline;
      const check = $('#verificarOffline');
      if (check) {
        check.disabled = false;
        $('#resultadoOffline').replaceChildren();
        renderOfflineReport();
      }
      notice(j.estado==='erro'?j.mensagem:j.mensagem || 'Resposta concluída. Confira as referências.');
      if($('#turnosChat'))await refreshChat();
      if(location.hash==='#downloads')downloads();
    }catch(e){failure(e);if(chatBusy)timer=setTimeout(poll,1500);}
  }
  window.addEventListener('hashchange',route);
  api('state').then(s => { S=s; $('#hardware').textContent = `${s.hardware.ram_bytes ? (s.hardware.ram_bytes/2**30).toFixed(1) + ' GB RAM' : 'RAM não identificada'} · ${s.hardware.arch} · consulta local`; route(); }).catch(failure);
})();
