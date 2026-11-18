'use strict';
window.ULRegiao = (() => {
  let city = null;
  let mapLayers = [];
  let services = {};
  const kinds = {saude:'Unidades de saúde', abrigos:'Abrigos cadastrados', risco:'Áreas mapeadas de risco'};
  async function open({api,esc,notice,failure,container,openPlace}) {
    container.innerHTML = `<div id="regiao-page"><h1>Minha região e contatos</h1>
      <section class="painel"><h2>Contatos de emergência</h2><ul><li>Defesa Civil — <b>199</b></li>
      <li>Bombeiros — <b>193</b></li><li>SAMU — <b>192</b></li></ul>
      <p>Guarde também os contatos da Defesa Civil municipal, da unidade de saúde de referência e dos serviços de água e energia.</p>
      <h2>Prepare os alertas no celular</h2><ol><li>Abra o aplicativo de SMS e digite o número <b>40199</b>.</li>
      <li>Envie o <b>CEP da área de interesse</b> (oito dígitos). Confira a confirmação no celular.</li>
      <li>Repita com outros CEPs que desejar acompanhar.</li></ol>
      <p>O Defesa Civil Alerta usa a rede 4G ou 5G em aparelhos compatíveis, sem cadastro. Esta tela fica disponível offline. A chegada de novos avisos depende da rede móvel e do canal usado.</p>
      <button class="secundario" data-region-source="alertas-cadastro">Cadastro oficial · internet</button>
      <button class="secundario" data-region-source="defesa-civil-alerta">Defesa Civil Alerta · internet</button></section>
      <section><h2>Histórico e guias por município</h2>
      <form id="regiao-busca"><label for="regiao-termo">Município</label>
      <input id="regiao-termo" type="search" minlength="2" maxlength="100" required>
      <button>Buscar município</button></form>
      <div class="acoes" id="regiao-resultados" aria-live="polite"></div>
      <div id="regiao-detalhe"></div></section>
      <section><h2>Guias offline</h2><div class="cards" id="regiao-guias"></div></section>
      <section><h2>Locais e mapas de referência</h2>
      <p>Os arquivos públicos do CNES, da prefeitura e do Serviço Geológico do Brasil podem ser preparados em GeoJSON. Confira a origem, a cobertura e a data antes de importar. Confirme atendimento e abrigos ativos com os serviços locais.</p>
      <button class="secundario" data-region-source="cnes-estabelecimentos">Dados de saúde · internet</button>
      <button class="secundario" data-region-source="sgb-riscos">Cartografia do SGB · internet</button>
      <details><summary>Como preparar uma camada do SGB</summary><p>Abra a consulta oficial, use o código IBGE de sete dígitos no filtro <code>cd_geocmu='código'</code>, selecione <code>GeoJSON</code> e informe <code>4326</code> como sistema de coordenadas de saída. Confira as datas de levantamento na fonte e salve o arquivo localmente.</p>
      <button class="secundario" data-region-source="sgb-setores">Abrir consulta do SGB · internet</button></details>
      <div id="regiao-camadas"></div></section></div>`;
    const root = container.querySelector('#regiao-page');
    const find = selector => root.querySelector(selector);
    const ref = id => api('open-resource',{id}).then(result => notice(result.mensagem)).catch(failure);
    root.onclick = event => {
      const button = event.target.closest('[data-region-source]');
      if (button) ref(button.dataset.regionSource);
    };
    let guides = [];
    let request = 0;
    function paintGuides(highlights = []) {
      const order = new Map(highlights.map((id,index) => [id,index]));
      const sorted = [...guides].sort((a,b) => (order.get(a[0]) ?? 99) - (order.get(b[0]) ?? 99));
      find('#regiao-guias').innerHTML = sorted.map(([id,title,summary,source]) =>
        `<article><h3>${esc(title)}</h3><p>${esc(summary)}</p><button class="secundario" data-region-source="${esc(source)}">Consultar fonte oficial · internet</button></article>`).join('');
    }
    function paintLayers() {
      const layerBox = find('#regiao-camadas');
      layerBox.innerHTML = `<h3>${esc(city.name)}</h3>
        ${['saude','abrigos'].map(kind => (services[kind] || []).length ? `<article><h4>${esc(kinds[kind])} · amostra</h4>
          <p class="fonte">${esc(services['data_'+kind])} · ${esc(services['fonte_'+kind])}</p><ul>
          ${services[kind].map((item,index) => `<li>${esc(item.nome)} · ${esc(item.endereco)} ${Number.isFinite(item.lat) ? `<button class="secundario" data-service="${kind}" data-service-index="${index}">Ver no mapa</button>` : ''}</li>`).join('')}</ul></article>` : '').join('')}
        <p>Mostre os arquivos importados no <a href="#mapas">mapa offline</a>. As camadas são cópias de referência e não indicam rotas de evacuação.</p>
        ${mapLayers.map(layer => `<article><h4>${esc(layer.titulo)}</h4>
          <p>${esc(kinds[layer.tipo])} · ${esc(layer.data)} · ${layer.features.length} registros</p>
          <p class="fonte">Fonte informada: ${esc(layer.fonte)}</p>
          ${layer.tipo === 'risco' ? '' : `<details><summary>Locais desta camada</summary><ul>${layer.features.map((feature,index) => `<li><button class="secundario" data-region-kind="${esc(layer.tipo)}" data-region-point="${index}">${esc(feature.nome)}</button></li>`).join('')}</ul></details>`}
          <button class="secundario" data-remove-layer="${esc(layer.tipo)}">Remover camada</button></article>`).join('')}
        <details><summary>Importar camada GeoJSON</summary><form id="regiao-importar">
        <label for="regiao-tipo">Tipo de camada</label><select id="regiao-tipo" name="tipo">${Object.entries(kinds).map(([id,label]) => `<option value="${id}">${esc(label)}</option>`).join('')}</select>
        <label for="regiao-titulo">Título da camada</label><input id="regiao-titulo" name="titulo" maxlength="120" required>
        <label for="regiao-fonte">Endereço HTTPS da fonte</label><input id="regiao-fonte" name="fonte" type="url" maxlength="600" required>
        <label for="regiao-data">Data de referência</label><input id="regiao-data" name="data" type="date" required>
        <p>Use pontos individuais para locais e polígonos para áreas de risco. Uma importação substitui a camada do mesmo tipo neste município.</p><button>Escolher arquivo</button></form></details>`;
      layerBox.querySelectorAll('[data-service]').forEach(button => button.onclick = () => {
        const item = services[button.dataset.service][Number(button.dataset.serviceIndex)];
        openPlace({...item,nome_mapa:kinds[button.dataset.service]}).catch(failure);
      });
      layerBox.querySelectorAll('[data-region-point]').forEach(button => button.onclick = () => {
        const layer = mapLayers.find(item => item.tipo === button.dataset.regionKind);
        const feature = layer.features[Number(button.dataset.regionPoint)];
        const [lon,lat] = feature.geometry.coordinates;
        openPlace({nome:feature.nome,lat,lon,nome_mapa:layer.titulo}).catch(failure);
      });
      layerBox.querySelectorAll('[data-remove-layer]').forEach(button => button.onclick = () => {
        if (confirm('Remover esta camada local?')) changeLayers('regiao-excluir', {tipo:button.dataset.removeLayer},button);
      });
      find('#regiao-importar').onsubmit = event => {
        event.preventDefault();
        changeLayers('regiao-importar',Object.fromEntries(new FormData(event.currentTarget)),event.currentTarget.querySelector('button'));
      };
    }
    async function changeLayers(path, body, button) {
      const ibge = city.ibge;
      button.disabled = true;
      try {
        const result = await api(path,{...body,ibge});
        if (result.cancelado || !root.isConnected || city.ibge !== ibge) return;
        mapLayers = result.camadas;
        paintLayers();
        notice(result.mensagem);
      } catch (error) { failure(error); }
      finally { button.disabled = false; }
    }
    async function selectCity(selected) {
      const ticket = ++request;
      const details = find('#regiao-detalhe');
      details.textContent = 'Consultando dados locais…';
      try {
        const result = await api('regiao-municipio',{ibge:selected.ibge});
        if (!root.isConnected || request !== ticket) return;
        city = result.municipio;
        services = result.servicos || {};
        mapLayers = result.camadas;
        const history = result.historico;
        const categories = history.categorias.filter(item => item.registros > 0);
        details.innerHTML = `<h3>${esc(city.name)}</h3><p>${esc(history.aviso)}</p>
          ${categories.length ? `<ul>${categories.map(item => `<li>${esc(item.nome)} · ${item.registros} registros · ${item.primeiro_ano} a ${item.ultimo_ano}</li>`).join('')}</ul>` :
            '<p>Sem registros para os temas mostrados nesta cópia.</p>'}
          <button class="secundario" data-region-source="atlas-desastres">Fonte: Atlas Digital de Desastres · ${esc(history.versao || 'internet')}</button>`;
        paintGuides(categories.sort((a,b) => b.registros - a.registros).map(item => item.id));
        paintLayers();
      } catch (error) { if (request === ticket && root.isConnected) details.textContent = error.message; }
    }
    find('#regiao-busca').onsubmit = async event => {
      event.preventDefault();
      const out = find('#regiao-resultados');
      const ticket = ++request;
      out.textContent = 'Buscando municípios…';
      try {
        const data = await api('map-catalog',{busca:find('#regiao-termo').value.trim()});
        if (!root.isConnected || request !== ticket) return;
        out.textContent = data.total ? '' : 'Município não encontrado.';
        for (const item of data.resultados) {
          const button = document.createElement('button');
          button.className = 'secundario';
          button.textContent = item.name;
          button.onclick = () => selectCity({ibge:item.id.slice('map-city-'.length),name:button.textContent});
          out.append(button);
        }
      } catch (error) { if (request === ticket && root.isConnected) out.textContent = error.message; }
    };
    try {
      const result = await api('regiao');
      if (!root.isConnected) return;
      guides = result.guias;
      paintGuides();
      if (result.ibge && request === 0) selectCity({ibge:result.ibge});
    } catch(error) { if (root.isConnected) failure(error); }
  }
  return {open};
})();
