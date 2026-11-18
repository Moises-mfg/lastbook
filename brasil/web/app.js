'use strict';
(() => {
  const $ = s => document.querySelector(s);
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  let S, draft, timer, chatPending = '', chatBusy = false;
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
    if (page === 'downloads') downloads(); else if (page === 'enciclopedias') enciclopedias(); else if (page === 'mapas') mapas(); else if (page === 'compras') compras(); else if (page === 'instalacao') instalacao(); else if (page === 'fontes') fontes(); else if (page === 'ia') ia(); else biblioteca();
  }
  function biblioteca() {
    const pdfs = S.guias_pdf || [];
    $('#conteudo').innerHTML = `<p class="tag">Sua base de conhecimento</p><h1>O essencial, mesmo<br>sem conexão.</h1><p class="intro">Os guias desta biblioteca já vêm com o aplicativo. Você pode consultá-los sem internet.</p>${pdfs.length ? `<section aria-label="Guias em PDF"><h2>Guias em PDF</h2><div class="cards">${pdfs.map(g => `<article class="card"><h3>${esc(g.titulo)}</h3><p>${esc(g.descricao)}</p><button data-pdf="${esc(g.id)}">Ler PDF offline</button></article>`).join('')}</div></section>` : ''}<h2>Guias rápidos</h2><label for="busca">Buscar nos guias locais</label><input id="busca" type="search" placeholder="Água, energia, comunicação…"><div class="cards" id="guias"></div>`;
    document.querySelectorAll('[data-pdf]').forEach(button => button.onclick = () => pdfGuide(button.dataset.pdf));
    const draw = () => {
      const norm = t => t.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLocaleLowerCase('pt-BR');
      const q = norm($('#busca').value);
      const found = S.guias.filter(g => norm(g.titulo + ' ' + g.texto + ' ' + g.categoria).includes(q));
      $('#guias').innerHTML = found.length ? found.map(g => `<div class="card"><p class="tag">${esc(g.categoria)}</p><h2>${esc(g.titulo)}</h2><button data-guide="${esc(g.id)}">Ler guia →</button></div>`).join('') : '<p>Nenhum guia encontrado. Tente outra palavra. Consulte também a seção Enciclopédias para pesquisar seus arquivos ZIM.</p>';
      document.querySelectorAll('[data-guide]').forEach(b => b.onclick = () => guide(b.dataset.guide));
    }; $('#busca').oninput = draw; draw();
  }
  function pdfGuide(id) {
    const guide = (S.guias_pdf || []).find(item => item.id === id);
    if (!guide) return;
    $('#conteudo').innerHTML = `<button class="secundario" id="voltar">← Biblioteca</button><h1>${esc(guide.titulo)}</h1><p>${esc(guide.descricao)}</p><button id="abrirPdf">Abrir arquivo PDF no leitor do sistema</button><div class="paginas-pdf">${guide.paginas.map((page, i) => `<figure><figcaption>Página ${i+1} de ${guide.paginas.length}</figcaption><img src="${esc(page)}" alt="Página ${i+1} de ${esc(guide.titulo)}" loading="lazy"></figure>`).join('')}</div>`;
    $('#voltar').onclick = biblioteca;
    $('#abrirPdf').onclick = () => api('open-pdf',{id}).then(r => notice(r.mensagem)).catch(failure);
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
      document.querySelectorAll('[data-open-resource]').forEach(b=>b.onclick=()=>api('open-resource',{id:b.dataset.openResource}).then(r=>notice(r.mensagem)).catch(failure));
    }
    $('#buscaFonte').oninput=draw;$('#categoriaFonte').onchange=draw;draw();
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
    const first = !S.escolhas, hardware = S.hardware, recommended = S.perfis[S.recomendado];
    const ram = hardware.ram_bytes ? (hardware.ram_bytes/2**30).toLocaleString('pt-BR',{maximumFractionDigits:1})+' GiB de RAM detectada' : 'RAM não identificada';
    const cpu = hardware.processadores_logicos ? ' · '+hardware.processadores_logicos+' processadores lógicos' : '';
    const weak = !hardware.ram_bytes || hardware.ram_bytes < 7*2**30;
    draft = S.escolhas ? structuredClone(S.escolhas) : {perfil:S.recomendado,modelo:weak?'sem-ia':S.perfis[S.recomendado].modelo,wikis:[S.perfis[S.recomendado].wiki],mapa:S.perfis[S.recomendado].mapa,estados:[],municipios:[]};
    const selected=new Set(draft.municipios||[]),mapItems=new Map();let request=0,offset=0,total=0;
    $('#conteudo').innerHTML = `<p class="tag">Brasil inteiro, escolhas locais</p><h1>${first?'Escolha o que baixar':'Minha instalação'}</h1><p class="intro">Escolha agora os conteúdos que quer consultar sem internet. Os arquivos começam a baixar quando você confirmar.</p><div class="painel" id="recomendacaoInstalacao"><h2>${weak?'Comece pela biblioteca':'Perfil sugerido: '+esc(recommended.nome)}</h2><p>${esc(ram+cpu)} · ${esc(hardware.arch)} · ${size(hardware.livre_bytes)} livres no disco.</p><p>${weak?'Comece pelos guias, enciclopédias e mapas. Você ainda pode selecionar o modelo Leve se houver memória suficiente.':'A sugestão usa a RAM detectada. Para notebooks com cerca de 8 GB, o perfil Leve é o ponto de partida. A velocidade da IA depende do processador.'}</p>${first?'<button id="somenteGuias" type="button" class="secundario">Abrir biblioteca sem baixar agora</button>':''}</div><button id="importarPlano" class="secundario">Importar plano do site (.json)</button><form id="escolhas"><div class="cards">${Object.entries(S.perfis).map(([id,p]) => `<label class="card perfil"><input type="radio" name="perfil" value="${id}"${draft.perfil === id ? ' checked' : ''}><h2>${p.nome}</h2><p>${p.ram_gib ? p.ram_gib + ' GB de RAM como alvo' : 'Você escolhe os componentes'}${S.recomendado === id ? ' · sugerido' : ''}</p></label>`).join('')}</div><fieldset><legend>IA local</legend><label for="modelo">Modelo</label><select id="modelo">${options(S.modelos,draft.modelo)}</select><p>O menor modelo ocupa cerca de 640 MB. O desempenho depende do processador; os modelos maiores exigem mais memória.</p></fieldset><fieldset><legend>Enciclopédias</legend>${Object.entries(S.wikis).map(([id,title]) => `<label class="linha"><input type="checkbox" name="wiki" value="${id}"${draft.wikis.includes(id) ? ' checked' : ''}><span>${esc(title)}<br><small>${size(S.catalogo[id].size)} · edição ${esc(S.catalogo[id].edition)}</small></span></label>`).join('')}<p>Mini: introduções e quadros. Sem imagens: artigos completos em texto. Completa: arquivo com imagens; o leitor atual exibe os artigos em texto.</p></fieldset><fieldset><legend>Mapas offline</legend><label for="mapa">Abrangência</label><select id="mapa">${options(S.mapas,draft.mapa)}</select><p>Ruas, água, localidades e serviços para consulta. Recortes por município e estado incluem o entorno delimitado pelo retângulo da região. Sem rotas automáticas, relevo ou informações em tempo real.</p><div id="mapaMunicipios"><label for="ufMunicipio">Estado para buscar municípios</label><select id="ufMunicipio"><option value="">Todo o Brasil</option>${options(S.estados,'')}</select><label for="buscaMunicipio">Nome do município</label><input id="buscaMunicipio" type="search" maxlength="100" placeholder="Ex.: Campinas"><p id="municipiosStatus" role="status"></p><div id="municipiosResultados" class="selecao"></div><button type="button" id="maisMunicipios" class="secundario">Próximos municípios</button><h3>Municípios escolhidos</h3><div id="municipiosSelecionados"></div></div><div id="mapaEstados" class="selecao">${Object.entries(S.estados).map(([id,title]) => `<label class="linha"><input type="checkbox" name="estado" value="${id}"${draft.estados.includes(id) ? ' checked' : ''}>${esc(title)} (${id})</label>`).join('')}</div><p id="mapaNacional">O mapa detalhado nacional inclui todos os estados e exige mais espaço, inclusive durante a montagem do arquivo.</p><p>Visão geral do Brasil incluída nas opções municipais e estaduais. Créditos: © contribuidores do OpenStreetMap, Geofabrik e IBGE. Licença ODbL 1.0.</p></fieldset><div class="aviso" id="estimativa" aria-live="polite"></div><div class="acoes"><button>Salvar escolhas</button><button type="button" id="instalar">Baixar seleção</button><a class="botao" href="#biblioteca">Abrir biblioteca</a></div></form>`;
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
    function estimate(){
      const c=values(),ids=[...c.wikis,...(c.modelo==='sem-ia'?[]:[c.modelo])];
      if(S.mapas_disponiveis && c.mapa!=='sem-mapas'){if(c.mapa==='brasil')ids.push('map-br-full');else{ids.push('map-br-base');ids.push(...(c.mapa==='estado'?c.estados.map(uf=>'map-uf-'+uf):c.municipios.map(id=>'map-city-'+id)));}}
      let bytes=0,extra=0,unknown=false;
      for(const id of ids){const p=S.catalogo[id]||mapItems.get(id);if(!p){unknown=true;continue;}if(!p.instalado){bytes+=Math.max(0,p.size-(p.parcial_bytes||0));if(p.parts)extra+=p.size;}}
      const model=S.modelos[c.modelo],warning=model.ram_gib && S.hardware.ram_bytes && S.hardware.ram_bytes<model.ram_gib*2**30*.94;
      $('#mapaMunicipios').hidden=c.mapa!=='municipio';$('#mapaEstados').hidden=c.mapa!=='estado';$('#mapaNacional').hidden=c.mapa!=='brasil';
      $('#estimativa').textContent=`Download restante estimado: ${size(bytes)}${unknown?' (aguardando tamanhos dos mapas)':''}. Espaço livre: ${size(S.hardware.livre_bytes)}. Reserva adicional: 1 GB${extra?' e '+size(extra)+' para montar o mapa nacional':''}.${!S.mapas_disponiveis?' Catálogo de mapas ainda indisponível nesta versão.':''}${warning?' O modelo escolhido excede a memória alvo deste computador; prefira uma opção menor.':''}`;
      $('#instalar').disabled=!ids.length;
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
        document.querySelectorAll('[data-city]').forEach(b=>b.onchange=()=>{b.checked?selected.add(b.dataset.city):selected.delete(b.dataset.city);drawSelected();estimate();});drawSelected();estimate();
      }catch(e){failure(e);}
    }
    $('#ufMunicipio').onchange=()=>searchCities();let debounce;
    $('#buscaMunicipio').oninput=()=>{clearTimeout(debounce);debounce=setTimeout(()=>searchCities(),200);};
    $('#maisMunicipios').onclick=()=>searchCities(offset+50);
    document.querySelectorAll('[name=perfil]').forEach(r => r.onchange = () => {const p=S.perfis[r.value];$('#modelo').value=p.modelo;$('#mapa').value=p.mapa;document.querySelectorAll('[name=wiki]').forEach(w=>w.checked=w.value===p.wiki);estimate();});
    $('#escolhas').addEventListener('change',estimate);estimate();drawSelected();searchCities();
    async function save(){S.escolhas=await api('choices',values());S=await api('state');}
    $('#escolhas').onsubmit=async e=>{e.preventDefault();try{await save();estimate();notice('Escolhas salvas. O download começa apenas quando você pedir.');}catch(e){failure(e);}};
    $('#instalar').onclick=async()=>{try{await save();await begin('install-selected',{},`Baixar modelos, enciclopédias e mapas selecionados? Download restante: ${size(S.plano.download_bytes)}. Espaço necessário: ${size(S.plano.necessario_bytes)}.`);}catch(e){failure(e);}};
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
      window.ULMapas.open(info,{api,notice});
    }catch(e){failure(e);}
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
    $('#conteudo').innerHTML=`<p class="tag">Assistente local · experimental</p><h1>Converse com sua biblioteca</h1><p class="intro">Faça perguntas de seguimento. O assistente usa os turnos recentes, e suas conversas ficam neste computador. Confira as referências antes de agir.</p><div class="painel"><p>Motor: <b>${S.ia.motor?'disponível':'não instalado'}</b> · Modelo: <b>${enabled?esc(S.modelos[selected].nome):'desativado'}</b></p>${enabled?`<p>${size(spec.size)} · contexto de ${spec.context.toLocaleString('pt-BR')} tokens · ${spec.ram_gib} GB RAM como alvo.</p><button id="baixar" class="secundario">Baixar ou verificar modelo selecionado</button>`:'<p>Escolha um modelo em Minha instalação para ativar o assistente.</p>'}</div><div class="acoes"><button type="button" class="secundario" id="novaConversa" disabled>Nova conversa</button><a class="botao" href="#biblioteca">Consultar guias</a></div><section id="turnosChat" aria-label="Histórico da conversa" aria-live="polite"></section><p id="chatPendente" class="mensagem-chat" role="status"></p><form id="pergunta"><label for="texto">Sua mensagem</label><textarea id="texto" maxlength="1500" required placeholder="O que você quer perguntar?"></textarea><div class="acoes"><button id="enviar" disabled>Enviar</button></div></form>`;
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
      if(['executando','baixando'].includes(j.estado)){chatBusy=true;chatControls();poll();}
      else if(!chatPending){chatBusy=false;chatControls();}
    }).catch(failure);
  }
  async function poll(){
    clearTimeout(timer);
    try{
      const j=await api('job');jobLine(j);
      if(['executando','baixando'].includes(j.estado)){
        chatBusy=true;chatControls();
        notice(j.estado==='baixando'?`${j.fase}: ${j.nome || ''} · ${Math.round(100*j.feito/j.total)}%`:'Processando neste computador…');timer=setTimeout(poll,1000);return;
      }
      if(j.estado==='erro' && chatPending && $('#texto') && !$('#texto').value)$('#texto').value=chatPending;
      chatPending='';chatBusy=false;
      S=await api('state');
      chatControls();
      notice(j.estado==='erro'?j.mensagem:j.mensagem || 'Resposta concluída. Confira as referências.');
      if($('#turnosChat'))await refreshChat();
      if(location.hash==='#downloads')downloads();
    }catch(e){failure(e);if(chatBusy)timer=setTimeout(poll,1500);}
  }
  window.addEventListener('hashchange',route);
  api('state').then(s => { S=s; $('#hardware').textContent = `${s.hardware.ram_bytes ? (s.hardware.ram_bytes/2**30).toFixed(1) + ' GB RAM' : 'RAM não identificada'} · ${s.hardware.arch} · consulta local`; route(); }).catch(failure);
})();
