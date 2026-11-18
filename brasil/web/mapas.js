'use strict';
/* Desenho local: tiles vetoriais JSON ou imagens MBTiles. Nenhum recurso externo. */
window.ULMapas=(()=>{
  let current=null;
  const C={background:'#d8e7e9',land:'#edf0df',water:'#b7dbe4',road:'#fffdf2',edge:'#c2b8a2',label:'#233c33'};
  function close(){if(current){current.alive=false;current.abort.abort();if(current.raf)cancelAnimationFrame(current.raf);current=null;}}
  function open(meta,{api,notice,focus,places=[],layers=[]}){
    close();const canvas=document.querySelector('#mapaCanvas');if(!canvas)return;
    const s=current={alive:true,abort:new AbortController(),z:meta.z,cx:meta.x+.5,cy:meta.y+.5,cache:new Map(),pending:new Set(),labels:[],hits:[],raf:0,mask:new Set(['road','water','place','poi'])};
    const $=id=>document.querySelector(id),ctx=canvas.getContext('2d'),vector=meta.formato==='ulmap';
    function schedule(){if(!s.alive||s.raf)return;s.raf=requestAnimationFrame(()=>{s.raf=0;draw();});}
    function load(z,x,y){
      const n=2**z;if(y<0||y>=n)return null;x=((x%n)+n)%n;const key=z+'/'+x+'/'+y;
      if(s.cache.has(key))return s.cache.get(key);
      if(s.pending.has(key))return null;s.pending.add(key);
      if(vector){
        api('vector-tile?z='+z+'&x='+x+'&y='+y).then(data=>{if(!s.alive)return;s.cache.set(key,render(data,z));finish(key);}).catch(()=>{s.cache.set(key,{failed:true});finish(key);});
      }else{
        const image=new Image();image.onload=()=>{if(s.alive)s.cache.set(key,{image,labels:[],pois:[]});finish(key);};image.onerror=()=>{s.cache.set(key,{failed:true});finish(key);};image.src='/api/brasil/tile?z='+z+'&x='+x+'&y='+y;
      }
      return null;
    }
    function finish(key){s.pending.delete(key);if(s.cache.size>100)s.cache.delete(s.cache.keys().next().value);schedule();}
    function render(data,z){
      const tile=document.createElement('canvas');tile.width=tile.height=256;const g=tile.getContext('2d'),k=256/(data.extent||512),labels=[],pois=[];
      g.fillStyle=C.background;g.fillRect(0,0,256,256);const layers=data.layers||{};
      const path=part=>{g.moveTo(part[0]*k,part[1]*k);for(let i=2;i<part.length;i+=2)g.lineTo(part[i]*k,part[i+1]*k);};
      for(const layer of ['land','water'])if(layer==='land'||s.mask.has('water'))for(const [,name,parts] of layers[layer]||[]){g.beginPath();parts.forEach(p=>{path(p);g.closePath();});g.fillStyle=C[layer];g.fill('evenodd');if(layer==='land'){g.strokeStyle='#a9baa2';g.lineWidth=.6;g.stroke();}}
      if(s.mask.has('water'))for(const [cls,,parts] of layers.waterway||[]){g.strokeStyle='#83bdce';g.lineWidth=cls==='river'?2:1;for(const p of parts){g.beginPath();path(p);g.stroke();}}
      if(s.mask.has('road')){
        const roads=layers.road||[];g.lineCap='round';g.lineJoin='round';
        for(const pass of [0,1])for(const [cls,name,parts] of roads){
          const major=/motorway|trunk|primary/.test(cls),minor=/path|footway|track|cycleway|steps/.test(cls),width=major?3:minor?1:1.7;
          g.strokeStyle=pass?(major?'#e8c98b':C.road):C.edge;g.lineWidth=width+(pass?0:1.2);
          g.setLineDash(minor?[2,3]:[]);
          for(const p of parts){g.beginPath();path(p);g.stroke();}
          if(pass&&name&&z>=13){const p=parts[0],at=Math.floor((p.length/2)/2)*2;labels.push({name,x:p[at]*k,y:p[at+1]*k,priority:2});}
        }g.setLineDash([]);
        for(const [,,parts] of layers.rail||[]){g.strokeStyle='#838983';g.lineWidth=1;g.setLineDash([3,3]);for(const p of parts){g.beginPath();path(p);g.stroke();}}g.setLineDash([]);
      }
      if(s.mask.has('place'))for(const [cls,name,parts] of layers.place||[]){const p=parts[0];if(name)labels.push({name,x:p[0]*k,y:p[1]*k,priority:0});}
      if(s.mask.has('poi'))for(const [cls,name,parts] of layers.poi||[]){const p=parts[0],x=p[0]*k,y=p[1]*k;g.fillStyle=/hospital|clinic|pharmacy/.test(cls)?'#ae5c49':'#436b60';g.strokeStyle='#fff';g.lineWidth=1;g.beginPath();g.arc(x,y,4,0,Math.PI*2);g.fill();g.stroke();pois.push({name,cls,x,y});}
      return {image:tile,labels,pois,truncated:data.truncado};
    }
    function draw(){
      if(!s.alive)return;
      const ratio=Math.min(2,devicePixelRatio||1),width=canvas.clientWidth,height=canvas.clientHeight;
      if(canvas.width!==Math.round(width*ratio)||canvas.height!==Math.round(height*ratio)){canvas.width=Math.round(width*ratio);canvas.height=Math.round(height*ratio);}
      ctx.setTransform(ratio,0,0,ratio,0,0);ctx.fillStyle=C.background;ctx.fillRect(0,0,width,height);
      const left=s.cx-width/512,top=s.cy-height/512,right=s.cx+width/512,bottom=s.cy+height/512;
      const labels=[];s.hits=[];let truncated=false;
      s.drawnTiles = 0;
      s.missingTiles = 0;
      const limits = meta.bounds && [
        project(meta.bounds[0],meta.bounds[3],0,0).map(value => value/256),
        project(meta.bounds[2],meta.bounds[1],0,0).map(value => value/256),
      ];
      for(let y=Math.floor(top);y<Math.ceil(bottom);y++)for(let x=Math.floor(left);x<Math.ceil(right);x++){
        const outside = limits && (x+1 <= limits[0][0] || x >= limits[1][0] || y+1 <= limits[0][1] || y >= limits[1][1]);
        const tile=outside ? null : load(s.z,x,y),px=(x-left)*256,py=(y-top)*256;
        if (!tile || tile.failed) {
          if (outside || tile?.failed || y < 0 || y >= 2**s.z) {
            s.missingTiles++;
            ctx.fillStyle = '#eeeae2';
            ctx.fillRect(px,py,256,256);
            ctx.fillStyle = '#604a3c';
            ctx.font = '13px system-ui';
            ctx.textAlign = 'center';
            ctx.fillText('Sem dados locais',px+128,py+128);
          }
          continue;
        }
        ctx.drawImage(tile.image,px,py,256,256);s.drawnTiles++;
        labels.push(...tile.labels.map(l=>({...l,x:l.x+px,y:l.y+py})));s.hits.push(...tile.pois.map(p=>({...p,x:p.x+px,y:p.y+py})));truncated||=tile.truncated;
      }
      const boxes=[],seen=new Set();ctx.font='12px system-ui';ctx.textAlign='center';ctx.textBaseline='middle';
      for(const l of labels.sort((a,b)=>a.priority-b.priority).slice(0,800)){
        if(seen.has(l.name)||l.x<0||l.x>width||l.y<0||l.y>height)continue;
        const w=Math.min(240,ctx.measureText(l.name).width+8),b=[l.x-w/2,l.y-9,l.x+w/2,l.y+9];
        if(boxes.some(a=>!(b[0]>a[2]||b[2]<a[0]||b[1]>a[3]||b[3]<a[1])))continue;
        seen.add(l.name);boxes.push(b);ctx.lineWidth=3;ctx.strokeStyle='#fafbf3';ctx.strokeText(l.name,l.x,l.y,230);ctx.fillStyle=C.label;ctx.fillText(l.name,l.x,l.y,230);
      }
      drawReferences(left,top,width,height);
      if($('#mapaEstado'))$('#mapaEstado').textContent='Nível '+s.z+(s.pending.size?' · carregando dados locais…':' · consulta local')+(s.missingTiles?' · áreas sem dados locais':'')+(truncated?' · aproxime para ver mais detalhes':'');
    }

    const referenceColors = {saude:'#883145',abrigos:'#233d83',risco:'#9c490b',pessoal:'#075b46'};
    function project(lon,lat,left,top) {
      const n = 2**s.z;
      lat = Math.max(-85,Math.min(85,lat));
      const x = (lon+180)/360*n;
      const y = (1-Math.asinh(Math.tan(lat*Math.PI/180))/Math.PI)/2*n;
      return [(x-left)*256,(y-top)*256];
    }
    function drawReferences(left,top,width,height) {
      for (const layer of layers) {
        if (layer.tipo !== 'risco' || !$('#mapaRisco')?.checked) continue;
        ctx.fillStyle = '#e9832180';
        ctx.strokeStyle = referenceColors.risco;
        ctx.lineWidth = 2;
        for (const {geometry} of layer.features) {
          const polygons = geometry.type === 'Polygon' ? [geometry.coordinates] : geometry.coordinates;
          ctx.beginPath();
          for (const polygon of polygons) for (const ring of polygon) {
            ctx.moveTo(...project(...ring[0],left,top));
            for (let i = 1; i < ring.length; i++) ctx.lineTo(...project(...ring[i],left,top));
            ctx.closePath();
          }
          ctx.fill('evenodd');
          ctx.stroke();
        }
      }
      const points = places.map(place => ({name:place.nome,lng:place.lon,lat:place.lat,cls:'pessoal'}));
      for (const layer of layers) {
        if (layer.tipo === 'risco' || !$('#mapaReferencias')?.checked) continue;
        for (const {nome,geometry} of layer.features) {
          const [lng,lat] = geometry.coordinates;
          points.push({name:nome,lng,lat,cls:layer.tipo});
        }
      }
      if (focus && !points.some(point => point.name === focus.nome && point.lng === focus.lon && point.lat === focus.lat)) {
        points.push({name:focus.nome,lng:focus.lon,lat:focus.lat,cls:'selecionado'});
      }
      for (const point of points) {
        const [x,y] = project(point.lng,point.lat,left,top);
        if (x < 0 || x > width || y < 0 || y > height) continue;
        ctx.fillStyle = referenceColors[point.cls] || '#222';
        ctx.strokeStyle = '#fff';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(x,y,7,0,2*Math.PI);
        ctx.fill();
        ctx.stroke();
        if (s.z >= 12 || point.name === focus?.nome) {
          ctx.font='bold 12px system-ui';
          ctx.strokeText(point.name,x,y-15,200);
          ctx.fillText(point.name,x,y-15,200);
        }
        s.hits.unshift({...point,x,y});
      }
    }
    $('#mapaRisco')?.addEventListener('change',schedule);
    $('#mapaReferencias')?.addEventListener('change',schedule);
    $('#mapaExportar').onclick = async event => {
      if (s.pending.size || !s.drawnTiles || s.raf) {
        notice('Aguarde o mapa carregar ou escolha uma área com dados locais.');
        return;
      }
      const button = event.currentTarget;
      button.disabled = true;
      try {
        const copy = document.createElement('canvas');
        const scale = Math.min(1,1280/canvas.width,900/canvas.height);
        copy.width = Math.round(canvas.width*scale);
        copy.height = Math.round(canvas.height*scale);
        copy.getContext('2d').drawImage(canvas,0,0,copy.width,copy.height);
        const fontes = [[meta.nome,meta.data,meta.atribuicao,meta.licenca].filter(Boolean).join(' · ').slice(0,1400)];
        for (const layer of layers) {
          if (layer.tipo === 'risco' ? $('#mapaRisco')?.checked : $('#mapaReferencias')?.checked) {
            fontes.push([layer.titulo,layer.data,'Fonte informada: '+layer.fonte].join(' · '));
          }
        }
        const result = await api('preparo-exportar-mapa',{imagem:copy.toDataURL('image/jpeg',.82).split(',')[1],fontes,cobertura_parcial:s.missingTiles > 0});
        if (result.mensagem) notice(result.mensagem);
      } catch(error) { notice(error.message); }
      finally { button.disabled = false; }
    };
    function zoom(delta,px=canvas.clientWidth/2,py=canvas.clientHeight/2){
      const z=Math.max(meta.minzoom,Math.min(meta.maxzoom,s.z+delta));if(z===s.z)return;
      const scale=2**(z-s.z),dx=(px-canvas.clientWidth/2)/256,dy=(py-canvas.clientHeight/2)/256;
      s.cx=(s.cx+dx)*scale-dx;s.cy=(s.cy+dy)*scale-dy;s.z=z;bound();schedule();
    }
    function center(hit) {
      s.z = Math.max(meta.minzoom, Math.min(meta.maxzoom, hit.tipo === 'place' ? 12 : 15));
      const n = 2**s.z;
      s.cx = (hit.lon + 180) / 360 * n;
      s.cy = (1 - Math.asinh(Math.tan(hit.lat * Math.PI / 180)) / Math.PI) / 2 * n;
      bound();
      schedule();
    }
    function bound(){const n=2**s.z;s.cx=((s.cx%n)+n)%n;s.cy=Math.max(0,Math.min(n,s.cy));}
    for(const b of document.querySelectorAll('[data-map-move]'))b.onclick=()=>{const [x,y]=b.dataset.mapMove.split(',').map(Number);s.cx+=x;s.cy+=y;bound();schedule();};
    $('#mapaMais').onclick=()=>zoom(1);$('#mapaMenos').onclick=()=>zoom(-1);
    canvas.addEventListener('wheel',e=>{e.preventDefault();const b=canvas.getBoundingClientRect();zoom(e.deltaY<0?1:-1,e.clientX-b.left,e.clientY-b.top);},{passive:false,signal:s.abort.signal});
    let drag=null;
    canvas.addEventListener('pointerdown',e=>{drag={x:e.clientX,y:e.clientY,moved:false};canvas.setPointerCapture(e.pointerId);},{signal:s.abort.signal});
    canvas.addEventListener('pointermove',e=>{if(!drag)return;const dx=e.clientX-drag.x,dy=e.clientY-drag.y;s.cx-=dx/256;s.cy-=dy/256;drag.moved||=Math.abs(dx)+Math.abs(dy)>3;drag.x=e.clientX;drag.y=e.clientY;bound();schedule();},{signal:s.abort.signal});
    canvas.addEventListener('pointerup',e=>{if(drag&&!drag.moved){const b=canvas.getBoundingClientRect(),x=e.clientX-b.left,y=e.clientY-b.top;const hit=s.hits.find(p=>Math.hypot(p.x-x,p.y-y)<12);if(hit){const names={saude:'Unidade de saúde cadastrada',abrigos:'Abrigo cadastrado',pessoal:'Lugar salvo',selecionado:'Lugar selecionado',hospital:'Hospital',clinic:'Clínica',pharmacy:'Farmácia',fire_station:'Bombeiros',drinking_water:'Água potável',shelter:'Abrigo',school:'Escola',fuel:'Combustível',police:'Polícia',supermarket:'Supermercado',veterinary:'Veterinário'};$('#mapaDetalhe').textContent=(hit.name||'Ponto sem nome')+' · '+(names[hit.cls]||hit.cls)+(hit.cls==='pessoal'?'':'. Confirme o funcionamento e as condições no local.');}}drag=null;},{signal:s.abort.signal});
    canvas.addEventListener('keydown',e=>{const keys={ArrowLeft:[-.5,0],ArrowRight:[.5,0],ArrowUp:[0,-.5],ArrowDown:[0,.5]};if(keys[e.key]){e.preventDefault();s.cx+=keys[e.key][0];s.cy+=keys[e.key][1];bound();schedule();}else if(e.key==='+'||e.key==='='){e.preventDefault();zoom(1);}else if(e.key==='-'){e.preventDefault();zoom(-1);}},{signal:s.abort.signal});
    document.querySelectorAll('[data-map-layer]').forEach(box=>box.onchange=()=>{box.checked?s.mask.add(box.dataset.mapLayer):s.mask.delete(box.dataset.mapLayer);s.cache.clear();schedule();});
    if($('#mapaBusca'))$('#mapaBusca').onsubmit=async e=>{e.preventDefault();try{const hits=await api('map-search',{busca:$('#mapaTermo').value});const out=$('#mapaResultados');out.replaceChildren();if(!hits.length)out.textContent='Nenhum lugar encontrado neste mapa.';for(const hit of hits){const b=document.createElement('button');b.type='button';b.className='secundario';b.textContent=hit.nome;b.onclick=()=>center(hit);out.append(b);}}catch(e){notice(e.message);}};
    if (focus) center(focus);
    window.addEventListener('resize',schedule,{signal:s.abort.signal});schedule();
  }
  return {open,close};
})();
