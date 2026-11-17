'use strict';
(() => {
  const $ = s => document.querySelector(s);
  const profiles = {leve:{nome:'Leve',modelo:'Qwen3 0.6B experimental',wiki:'Português mini',ram:8},moderada:{nome:'Moderada',modelo:'Qwen3 4B',wiki:'Português sem imagens',ram:16},parruda:{nome:'Parruda',modelo:'Qwen3 14B',wiki:'Português completo',ram:32},personalizada:{nome:'Personalizada',modelo:'Você escolhe',wiki:'Você escolhe',ram:0}};
  let selected='leve';
  const estados={AC:'Acre',AL:'Alagoas',AP:'Amapá',AM:'Amazonas',BA:'Bahia',CE:'Ceará',DF:'Distrito Federal',ES:'Espírito Santo',GO:'Goiás',MA:'Maranhão',MT:'Mato Grosso',MS:'Mato Grosso do Sul',MG:'Minas Gerais',PA:'Pará',PB:'Paraíba',PR:'Paraná',PE:'Pernambuco',PI:'Piauí',RJ:'Rio de Janeiro',RN:'Rio Grande do Norte',RS:'Rio Grande do Sul',RO:'Rondônia',RR:'Roraima',SC:'Santa Catarina',SP:'São Paulo',SE:'Sergipe',TO:'Tocantins'};
  $('#estado').innerHTML='<option value="">Escolha um estado</option>'+Object.entries(estados).map(([id,name])=>`<option value="${id}">${name}</option>`).join('');
  $('#perfis').innerHTML=Object.entries(profiles).map(([id,p])=>`<label><input type="radio" name="perfil" value="${id}"${id==='leve'?' checked':''}> ${p.nome}</label>`).join('');
  const catalog=window.ULTIMO_LIVRO_CATALOGO,maps=window.ULTIMO_LIVRO_MAPAS||{};
  const defaults={leve:['qwen3-0.6b','pt-mini','municipio'],moderada:['qwen3-4b','pt-nopic','estado'],parruda:['qwen3-14b','pt-maxi','brasil']};
  function config(){const idiomas=[...document.querySelectorAll('[name=idioma]:checked')].map(x=>x.value);return {versao:1,perfil:selected,modelo:$('#modelo-site').value,wikis:idiomas.map(lang=>lang==='pt'?$('#variante-pt').value:lang+'-mini'),estados:$('#estado').value?[$('#estado').value]:[],mapa:$('#mapa-site').value,municipios:$('#municipio-site').value?[$('#municipio-site').value]:[],ram_gb:Number($('#ram').value),idiomas,estado:$('#estado').value};}
  function render(){
    const c=config(),ids=[...c.wikis,...(c.modelo==='sem-ia'?[]:[c.modelo])];
    const mapIds=c.mapa==='brasil'?['map-br-full']:['map-br-base',...(c.mapa==='estado'?c.estados.map(uf=>'map-uf-'+uf):c.municipios.map(code=>'map-city-'+code))];
    const available=Object.keys(maps).length>0,bytes=ids.reduce((sum,id)=>sum+catalog[id].size,0)+(available?mapIds.reduce((sum,id)=>sum+(maps[id]?.size||0),0):0),need=c.modelo==='sem-ia'?0:catalog[c.modelo].ram_gib;
    $('#escolha-municipio').hidden=c.mapa!=='municipio';
    $('#resumo').textContent=`${profiles[selected].nome}: ${c.modelo==='sem-ia'?'biblioteca sem IA':c.modelo}. Arquivos selecionados: ${(bytes/1e9).toLocaleString('pt-BR',{maximumFractionDigits:2})} GB. ${need>Number($('#ram').value)?'Este modelo excede a memória alvo informada. Escolha uma opção menor.':'A compatibilidade real depende de testes no computador.'} O leitor atual apresenta artigos em texto. ${available?'Tamanhos incluem os mapas escolhidos; reserve espaço adicional para instalação.':'Mapas em preparação, ainda fora deste total.'}`;
  }
  function cities(){
    const select=$('#municipio-site');select.replaceChildren();const first=document.createElement('option');first.value='';first.textContent=$('#estado').value?'Escolha um município (opcional)':'Escolha primeiro o estado';select.append(first);
    const found=Object.values(maps).filter(p=>p.scope==='municipio'&&p.uf===$('#estado').value).sort((a,b)=>a.name.localeCompare(b.name,'pt-BR'));
    for(const p of found){const o=document.createElement('option');o.value=p.code;o.textContent=p.name+' · '+(p.size/1e6).toLocaleString('pt-BR',{maximumFractionDigits:1})+' MB';select.append(o);}
  }
  $('#estado').onchange=()=>{cities();render();};$('#municipio-site').onchange=render;$('#mapa-site').onchange=render;cities();
  function applyProfile(){const values=defaults[selected];if(values){$('#modelo-site').value=values[0];$('#variante-pt').value=values[1];$('#mapa-site').value=values[2];}render();}
  document.querySelectorAll('[name=perfil]').forEach(r=>r.onchange=()=>{selected=r.value;applyProfile();});
  $('#ram').onchange=()=>{selected=Number($('#ram').value)>=32?'parruda':Number($('#ram').value)>=16?'moderada':'leve';document.querySelector(`[name=perfil][value=${selected}]`).checked=true;applyProfile();};
  ['#modelo-site','#variante-pt'].forEach(id=>$(id).onchange=()=>{selected='personalizada';document.querySelector('[name=perfil][value=personalizada]').checked=true;render();});
  document.querySelectorAll('[name=idioma]').forEach(x=>x.onchange=render);render();
  $('#exportar').onclick=()=>{const url=URL.createObjectURL(new Blob([JSON.stringify(config(),null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='meu-plano-ultimo-livro.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
  const items=['Água potável e recipientes adequados','Alimentos habituais e abridor manual','Lanterna e pilhas ou recarga','Power bank e cabos compatíveis','Curativos e medicamentos de uso contínuo','Documentos, contatos e itens de higiene'];
  let saved=[];try{const v=JSON.parse(localStorage.getItem('ul-checklist')||'[]');if(Array.isArray(v))saved=v.filter(x=>Number.isInteger(x)&&x>=0&&x<items.length);}catch{}
  function checks(){ $('#checklist').innerHTML=items.map((name,i)=>`<label class="linha"><input type="checkbox" value="${i}"${saved.includes(i)?' checked':''}>${name}</label>`).join('');document.querySelectorAll('#checklist input').forEach(c=>c.onchange=()=>{saved=[...document.querySelectorAll('#checklist input:checked')].map(x=>Number(x.value));try{localStorage.setItem('ul-checklist',JSON.stringify(saved));}catch{}});}
  $('#limpar').onclick=()=>{saved=[];try{localStorage.removeItem('ul-checklist');}catch{}checks();};checks();
  const resources=window.ULTIMO_LIVRO_FONTES||[],theme=$('#tema-fonte');
  for(const category of [...new Set(resources.map(r=>r.categoria))]){const option=document.createElement('option');option.value=option.textContent=category;theme.append(option);}
  function drawSources(){
    const list=$('#fontes-lista');list.replaceChildren();
    for(const item of resources.filter(r=>!theme.value||r.categoria===theme.value)){
      const article=document.createElement('article');article.dataset.resource=item.id;
      for(const [tag,value] of [['small',item.tipo],['h3',item.nome],['p',item.resumo],['p',item.observacao],['small','Verificado em '+item.revisado]]){const e=document.createElement(tag);e.textContent=value;article.append(e);}
      const a=document.createElement('a');a.href=item.url;a.textContent='Consultar fonte externa ↗';a.rel='noopener noreferrer';article.append(document.createElement('br'),a);list.append(article);
    }
  }
  theme.onchange=drawSources;drawSources();
})();
