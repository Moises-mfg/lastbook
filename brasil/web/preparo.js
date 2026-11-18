'use strict';
(() => {
  let opening = 0;
  const planFields = [
    ['encontro1', 'Primeiro ponto de encontro'], ['encontro2', 'Ponto alternativo de encontro'],
    ['contato', 'Contato de referência e como falar com ele'], ['apoio', 'Quem precisa de apoio e como ajudar'],
    ['levar', 'O que levar ao sair']
  ];
  const uid = () => globalThis.crypto?.randomUUID?.() || 'local-' + Date.now().toString(36) + '-' + Math.random().toString(36).slice(2);
  const today = () => {
    const now = new Date();
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
  };

  async function open(page, {api, esc, notice, failure, openPlace, container}) {
    const target = typeof container === 'string' ? document.querySelector(container) : container;
    if (!target) throw Error('Área de preparo indisponível.');
    const ticket = ++opening;
    const shell = document.createElement('div');
    shell.className = 'preparo';
    shell.innerHTML = '<p role="status">Abrindo seus dados de preparo…</p>';
    target.replaceChildren(shell);
    const active = () => ticket === opening && shell.isConnected;
    let data, busy = false;
    let editId = null, removing = null;
    const rehearsal = new Set();
    const q = selector => shell.querySelector(selector);
    const all = selector => [...shell.querySelectorAll(selector)];
    const text = value => esc(value ?? '');
    const dateText = value => /^\d{4}-\d{2}-\d{2}$/.test(value || '') ? value.split('-').reverse().join('/') : value;
    function field(name, label, value = '', {required = false, type = 'text', max = 300, attrs = ''} = {}) {
      return `<label class="preparo-campo" for="prep-${name}">${text(label)}<input id="prep-${name}" name="${name}" type="${type}" value="${text(value)}" maxlength="${max}" ${required ? 'required' : ''} ${attrs}></label>`;
    }
    function area(name, label, value = '', max = 2000) {
      return `<label class="preparo-campo" for="prep-${name}">${text(label)}<textarea id="prep-${name}" name="${name}" maxlength="${max}">${text(value)}</textarea></label>`;
    }
    const empty = message => `<p class="preparo-vazio">${message}</p>`;
    function heading(title, intro) {
      return `<p class="tag">Minha preparação · neste computador</p><h1>${title}</h1><p class="intro">${intro}</p>`;
    }
    function actions(section, item) {
      const id = text(item.id);
      return `<div class="acoes"><button type="button" class="secundario" data-edit="${id}">Editar</button><button type="button" class="secundario" data-remove="${id}">Remover</button></div>${removing === item.id ? `<div class="aviso" role="alert"><p>Remover “${text(item.nome || item.descricao)}”${section === 'recuperacao' ? ' e suas fotos' : ''}? Esta ação não pode ser desfeita.</p><div class="acoes"><button type="button" data-confirm-remove="${id}">Sim, remover</button><button type="button" class="secundario" data-cancel-remove>Manter registro</button></div></div>` : ''}`;
    }
    async function run(button, operation, message) {
      if (busy) return;
      busy = true;
      all('button, input, textarea, select').forEach(el => { el.dataset.prepDisabled = el.disabled ? '1' : '0'; el.disabled = true; });
      try {
        const result = await operation();
        if (!active()) return;
        if (result && !result.cancelado && !result.cancelled) {
          data = result.dados || result;
          editId = null;
          removing = null;
          render();
          if (message) notice(message);
        }
      } catch (error) { if (active()) failure(error); }
      finally {
        busy = false;
        if (active()) all('[data-prep-disabled]').forEach(el => { el.disabled = el.dataset.prepDisabled === '1'; delete el.dataset.prepDisabled; });
      }
    }
    function save(section, value, button) {
      return run(button, () => api('preparo', {secao:section, dados:value}), 'Dados salvos neste computador.');
    }
    function formValues(form) {
      return Object.fromEntries([...new FormData(form).entries()].map(([key, value]) => [key, String(value).trim()]));
    }
    function editor(section, fields, label) {
      return `<form id="preparo-form" class="painel"><h2>${editId ? 'Editar ' : 'Adicionar '}${label}</h2>${fields}<div class="acoes"><button type="submit">${editId ? 'Salvar alterações' : 'Adicionar'}</button>${editId ? '<button type="button" class="secundario" id="preparo-cancelar">Cancelar edição</button>' : ''}</div></form>`;
    }
    function bindList(section, build) {
      all('[data-edit]').forEach(button => button.onclick = () => {
        editId = button.dataset.edit; removing = null; render(); q('#preparo-form').scrollIntoView({block:'start'}); q('#preparo-form input').focus();
      });
      all('[data-remove]').forEach(button => button.onclick = () => { removing = button.dataset.remove; render(); q('[data-confirm-remove]')?.focus(); });
      all('[data-cancel-remove]').forEach(button => button.onclick = () => { removing = null; render(); });
      all('[data-confirm-remove]').forEach(button => button.onclick = () => save(section, (data[section] || []).filter(item => item.id !== button.dataset.confirmRemove), button));
      const cancel = q('#preparo-cancelar');
      if (cancel) cancel.onclick = () => { editId = null; render(); };
      q('#preparo-form').onsubmit = event => {
        event.preventDefault();
        const form = event.currentTarget;
        if (!form.reportValidity()) return;
        const values = formValues(form);
        const existing = (data[section] || []).find(item => item.id === editId);
        const item = build(values, existing);
        if (!item) return;
        item.id = existing?.id || uid();
        const items = existing ? data[section].map(old => old.id === existing.id ? item : old) : [...(data[section] || []), item];
        save(section, items, form.querySelector('[type=submit]'));
      };
    }
    function quick() {
      const plan = data.plano || {};
      shell.innerHTML = heading('Preciso agir agora', 'Quatro caminhos diretos. Consulte os arquivos locais e combine os próximos passos com as pessoas próximas.') + `
        <div class="preparo-quatro">
          <article><span class="tag">1 · Pessoas</span><h2>Reunir e avisar</h2><dl><dt>Primeiro encontro</dt><dd>${text(plan.encontro1) || 'Ainda não definido.'}</dd><dt>Contato de referência</dt><dd>${text(plan.contato) || 'Ainda não definido.'}</dd></dl><a class="botao" href="#plano-familiar">Ver plano familiar</a></article>
          <article><span class="tag">2 · Orientação</span><h2>Consultar o mapa</h2><p>Veja os mapas instalados e seus pontos de encontro. As condições do caminho precisam ser verificadas no local.</p><div class="acoes"><a class="botao" href="#mapas">Abrir mapa</a><a href="#lugares-salvos">Lugares salvos</a></div></article>
          <article><span class="tag">3 · Informação</span><h2>Abrir um guia</h2><p>Consulte os guias da biblioteca para a situação que está vivendo.</p><a class="botao" href="#biblioteca">Abrir biblioteca</a></article>
          <article><span class="tag">4 · Contatos</span><h2>Encontrar ajuda</h2><p>Consulte os números de emergência e os canais da Defesa Civil.</p><a class="botao" href="#regiao">Ver contatos oficiais</a></article>
        </div><p class="aviso">Em risco imediato, siga as orientações da Defesa Civil e dos serviços locais. O aplicativo não acompanha alertas nem a segurança das vias em tempo real.</p>
        <section class="painel"><h2>Ensaio prático</h2><p>Quando estiver em segurança, tente encontrar cada informação sem internet. Marque o que conseguiu nesta visita; não é necessário cronometrar.</p>${[['plano','Achei meu plano familiar'],['contato','Achei o contato de referência'],['mapa','Abri meu mapa'],['guia','Encontrei um guia']].map(([id,label]) => `<label class="linha"><input type="checkbox" data-ensaio="${id}"${rehearsal.has(id) ? ' checked' : ''}>${label}</label>`).join('')}<p id="ensaio-status" role="status">${rehearsal.size} de 4 etapas encontradas.</p></section>`;
      all('[data-ensaio]').forEach(input => input.onchange = () => {
        input.checked ? rehearsal.add(input.dataset.ensaio) : rehearsal.delete(input.dataset.ensaio);
        q('#ensaio-status').textContent = `${rehearsal.size} de 4 etapas encontradas.`;
      });
    }
    function plan() {
      shell.innerHTML = heading('Plano familiar', 'Combine pontos de encontro, contato e apoio antes de precisar sair. Revise o plano com as pessoas envolvidas.') + `
        <form id="preparo-form" class="painel">${planFields.map(([name,label]) => area(name,label,data.plano?.[name])).join('')}<button type="submit">Salvar plano familiar</button></form>
        <div class="acoes"><a href="#lugares-salvos">Organizar lugares salvos</a><a href="#rapido">Testar acesso rápido</a><a href="#regiao">Contatos oficiais e região</a></div>
        <section class="painel"><h2>Levar uma cópia</h2><p>Escolha quais campos do plano familiar incluir no arquivo HTML. Ele abre sem internet e pode ser impresso pelo navegador. Guarde a cópia em um local de confiança.</p>
        <form id="preparo-exportar"><fieldset><legend>Campos do plano para incluir na cópia</legend>${planFields.map(([key,label]) => `<label class="linha"><input type="checkbox" name="campos" value="${key}">${label}</label>`).join('')}</fieldset><button type="submit" class="secundario">Salvar cópia HTML offline</button></form></section>`;
      q('#preparo-form').onsubmit = event => {
        event.preventDefault(); save('plano', formValues(event.currentTarget), event.currentTarget.querySelector('button'));
      };
      q('#preparo-exportar').onsubmit = async event => {
        event.preventDefault();
        const campos = [...new FormData(event.currentTarget).getAll('campos')];
        if (!campos.length) { notice('Escolha pelo menos um campo para exportar.'); return; }
        const button = event.currentTarget.querySelector('button');
        if (busy) return;
        busy = true; button.disabled = true;
        try { const result = await api('preparo-exportar', {campos}); if (active()) notice(result.mensagem || (result.cancelado ? 'Exportação cancelada.' : 'Cópia offline salva.')); }
        catch (error) { if (active()) failure(error); }
        finally { busy = false; button.disabled = false; }
      };
    }
    function places() {
      const item = (data.lugares || []).find(item => item.id === editId) || {};
      shell.innerHTML = heading('Lugares salvos', 'Registre pontos úteis e confira os locais pessoalmente. Uma coordenada salva não confirma acesso, funcionamento ou segurança.') + `
        <div class="preparo-lista">${(data.lugares || []).map(place => `<article><h2>${text(place.nome)}</h2><p>${text(place.lat)}, ${text(place.lon)}</p><p class="preparo-texto">${text(place.notas)}</p><p><small>Última revisão: ${text(dateText(place.revisado)) || 'não informada'}</small></p><button type="button" data-place="${text(place.id)}">Ver no mapa</button>${actions('lugares',place)}</article>`).join('') || empty('Nenhum lugar salvo. Adicione um ponto conhecido abaixo.')}</div>` +
        editor('lugares', field('nome','Nome do lugar',item.nome,{required:true,max:160}) + `<div class="preparo-dupla">${field('lat','Latitude',item.lat,{required:true,type:'number',attrs:'min="-90" max="90" step="any"'})}${field('lon','Longitude',item.lon,{required:true,type:'number',attrs:'min="-180" max="180" step="any"'})}</div>` + area('notas','Notas locais (acesso, referência ou combinação)',item.notas) + field('revisado','Data em que conferiu o lugar',item.revisado,{type:'date'}), 'lugar');
      bindList('lugares', values => {
        if (!values.nome) { q('[name=nome]').focus(); notice('Informe o nome do lugar.'); return; }
        return {...values,lat:Number(values.lat),lon:Number(values.lon)};
      });
      all('[data-place]').forEach(button => button.onclick = async () => {
        try { await openPlace(data.lugares.find(place => place.id === button.dataset.place)); }
        catch (error) { if (active()) failure(error); }
      });
    }
    function inventory() {
      const item = (data.itens || []).find(item => item.id === editId) || {};
      shell.innerHTML = heading('Inventário da casa', 'Anote o que existe, quanto há e onde está. Confira validade, estado e necessidades das pessoas na próxima revisão.') + `<p><a href="#compras">Abrir checklist de preparo</a></p>
        <div class="preparo-lista">${(data.itens || []).map(item => `<article><h2>${text(item.nome)}</h2><dl><dt>Quantidade</dt><dd>${text(item.quantidade) || 'Não informada'}</dd><dt>Onde está</dt><dd>${text(item.local) || 'Não informado'}</dd><dt>Revisar em</dt><dd>${text(dateText(item.revisar)) || 'Sem data'}</dd></dl>${actions('itens',item)}</article>`).join('') || empty('Seu inventário ainda está vazio. Comece pelo que já tem.')}</div>` +
        editor('itens', field('nome','Nome do item',item.nome,{required:true,max:160}) + field('quantidade','Quantidade e unidade (ex.: 2 garrafas de 1 L)',item.quantidade,{max:160}) + field('local','Onde está guardado',item.local) + field('revisar','Data para revisar',item.revisar,{type:'date'}), 'item');
      bindList('itens', values => {
        if (!values.nome) { q('[name=nome]').focus(); notice('Informe o nome do item.'); return; }
        return values;
      });
    }
    function recovery() {
      const item = (data.recuperacao || []).find(item => item.id === editId) || {};
      shell.innerHTML = heading('Recuperação após o evento', 'Organize registros e protocolos com calma, quando o local estiver seguro. Os registros e fotos ficam neste computador.') + `
        <section class="painel"><h2>Depois de uma enchente</h2><p>Antes de voltar, acompanhe a liberação e as orientações dos órgãos locais. Evite estruturas danificadas e instalações elétricas atingidas até avaliação de profissionais. Documente perdas somente quando puder fazê-lo em segurança.</p><p>Registre datas, danos e números de atendimento; mantenha cópias dos comprovantes. Para limpeza, descarte e abastecimento, consulte as orientações atualizadas da Defesa Civil e da prefeitura. Este resumo editorial não substitui uma avaliação no local.</p><button type="button" class="secundario" id="preparo-fonte">Consultar fonte oficial · internet</button></section>
        <div class="preparo-lista">${(data.recuperacao || []).map(record => `<article><p class="tag">${text(dateText(record.data))}</p><h2>${text(record.descricao)}</h2><p class="preparo-texto">Protocolo ou referência: ${text(record.protocolo) || 'Não informado'}</p><div class="preparo-fotos">${(record.fotos || []).map(photo => `<figure><a href="/api/brasil/preparo-foto/${encodeURIComponent(photo.id)}" target="_blank" rel="noopener"><img src="/api/brasil/preparo-foto/${encodeURIComponent(photo.id)}" alt="${text(photo.nome)}" loading="lazy"></a><figcaption>${text(photo.nome)}</figcaption></figure>`).join('')}</div><button type="button" class="secundario" data-photo="${text(record.id)}">Adicionar foto local</button>${actions('recuperacao',record)}</article>`).join('') || empty('Nenhum registro de recuperação. Adicione datas e informações que precise acompanhar.')}</div>` +
        editor('recuperacao', field('data','Data do registro',item.data || today(),{required:true,type:'date'}) + field('descricao','Descrição do que aconteceu ou precisa ser acompanhado',item.descricao,{required:true,max:1000}) + area('protocolo','Protocolos, atendimentos e referências',item.protocolo), 'registro');
      bindList('recuperacao', (values, existing) => {
        if (!values.descricao) { q('[name=descricao]').focus(); notice('Descreva o registro.'); return; }
        return {...values,fotos:existing?.fotos || []};
      });
      all('[data-photo]').forEach(button => button.onclick = () => run(button, () => api('preparo-foto',{id:button.dataset.photo}), 'Foto adicionada ao registro local.'));
      q('#preparo-fonte').onclick = async event => {
        const button = event.currentTarget; button.disabled = true;
        try { const result = await api('open-resource',{id:'pos-enchente'}); if (active()) notice(result.mensagem || 'Fonte aberta no navegador.'); }
        catch (error) { if (active()) failure(error); }
        finally { button.disabled = false; }
      };
    }
    function render() {
      if (!active()) return;
      ({rapido:quick,'plano-familiar':plan,'lugares-salvos':places,inventario:inventory,recuperacao:recovery}[page] || quick)();
    }
    try { data = await api('preparo'); if (active()) render(); }
    catch (error) {
      if (!active()) return;
      shell.innerHTML = '<h1>Minha preparação</h1><p>Não foi possível abrir os dados locais.</p><button type="button">Tentar novamente</button>';
      q('button').onclick = () => open(page,{api,esc,notice,failure,openPlace,container:target});
      failure(error);
    }
  }
  window.ULPreparo = {open};
})();
