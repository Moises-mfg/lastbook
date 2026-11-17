'use strict';
(() => {
  const $ = s => document.querySelector(s);
  const profiles = {leve:{nome:'Leve',modelo:'Qwen3 0.6B experimental',wiki:'Português mini',ram:8},moderada:{nome:'Moderada',modelo:'Qwen3 4B planejado',wiki:'Português sem imagens',ram:16},parruda:{nome:'Parruda',modelo:'Qwen3 14B planejado',wiki:'Português completo',ram:32},personalizada:{nome:'Personalizada',modelo:'Você escolhe',wiki:'Você escolhe',ram:0}};
  let selected='leve';
  const estados={AC:'Acre',AL:'Alagoas',AP:'Amapá',AM:'Amazonas',BA:'Bahia',CE:'Ceará',DF:'Distrito Federal',ES:'Espírito Santo',GO:'Goiás',MA:'Maranhão',MT:'Mato Grosso',MS:'Mato Grosso do Sul',MG:'Minas Gerais',PA:'Pará',PB:'Paraíba',PR:'Paraná',PE:'Pernambuco',PI:'Piauí',RJ:'Rio de Janeiro',RN:'Rio Grande do Norte',RS:'Rio Grande do Sul',RO:'Rondônia',RR:'Roraima',SC:'Santa Catarina',SP:'São Paulo',SE:'Sergipe',TO:'Tocantins'};
  $('#estado').innerHTML='<option value="">Escolha um estado</option>'+Object.entries(estados).map(([id,name])=>`<option value="${id}">${name}</option>`).join('');
  $('#perfis').innerHTML=Object.entries(profiles).map(([id,p])=>`<label><input type="radio" name="perfil" value="${id}"${id==='leve'?' checked':''}> ${p.nome}</label>`).join('');
  function render(){const p=profiles[selected];$('#resumo').textContent=`${p.nome}: ${p.modelo}; Wikipedia ${p.wiki}. ${p.ram>Number($('#ram').value)?'Este perfil excede a memória alvo informada. Escolha uma opção menor.':'A compatibilidade real depende de testes no computador.'}`;}
  document.querySelectorAll('[name=perfil]').forEach(r=>r.onchange=()=>{selected=r.value;render();});
  $('#ram').onchange=()=>{selected=Number($('#ram').value)>=32?'parruda':Number($('#ram').value)>=16?'moderada':'leve';document.querySelector(`[name=perfil][value=${selected}]`).checked=true;render();};render();
  $('#exportar').onclick=()=>{const data={versao:1,perfil:selected,ram_gb:Number($('#ram').value),estado:$('#estado').value,idiomas:[...document.querySelectorAll('[name=idioma]:checked')].map(x=>x.value),status:'planejamento; pacotes ainda nao publicados'};const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='meu-plano-ultimo-livro.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
  const items=['Água potável e recipientes adequados','Alimentos habituais e abridor manual','Lanterna e pilhas ou recarga','Power bank e cabos compatíveis','Curativos e medicamentos de uso contínuo','Documentos, contatos e itens de higiene'];
  let saved=[];try{const v=JSON.parse(localStorage.getItem('ul-checklist')||'[]');if(Array.isArray(v))saved=v.filter(x=>Number.isInteger(x)&&x>=0&&x<items.length);}catch{}
  function checks(){ $('#checklist').innerHTML=items.map((name,i)=>`<label class="linha"><input type="checkbox" value="${i}"${saved.includes(i)?' checked':''}>${name}</label>`).join('');document.querySelectorAll('#checklist input').forEach(c=>c.onchange=()=>{saved=[...document.querySelectorAll('#checklist input:checked')].map(x=>Number(x.value));try{localStorage.setItem('ul-checklist',JSON.stringify(saved));}catch{}});}
  $('#limpar').onclick=()=>{saved=[];try{localStorage.removeItem('ul-checklist');}catch{}checks();};checks();
})();
