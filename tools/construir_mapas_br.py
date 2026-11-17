#!/usr/bin/env python3
"""Constrói mapas do Brasil de fontes OSM/IBGE. Ferramenta de mantenedor, não instalada.

Dependências isoladas: osmium==4.3.2, pyshp==3.1.9. A base resultante é ODbL-1.0.
O formato delta se inspira no construtor MIT original do LastBook.
"""
import argparse
import hashlib
import json
import math
import os
import shutil
import tempfile
from pathlib import Path
import sqlite3
import sys
import time
import zipfile

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from brasil.mapa_vetor import create,add_feature,finish,decode

SOURCES=ROOT/'derived/mapas-br/fontes'
OUT=ROOT/'derived/mapas-br'
ATTRIBUTION='© contribuidores do OpenStreetMap · ODbL 1.0; extrato Geofabrik. Recortes IBGE 2025.'
ROAD_Z={'motorway':5,'trunk':5,'primary':7,'secondary':9,'tertiary':10,'residential':12,'unclassified':12,'living_street':13,'pedestrian':13,'service':14,'track':13,'path':14,'footway':14,'cycleway':14,'steps':16}
POIS={'hospital','clinic','pharmacy','doctors','fire_station','police','drinking_water','shelter','community_centre','townhall','school','library','supermarket','convenience','fuel','veterinary','camp_site','hardware','doityourself'}
PLACE_Z={'city':5,'town':8,'village':11,'hamlet':13,'suburb':13,'locality':15}


def provenance():
    data=json.loads((SOURCES/'proveniencia.json').read_text())
    extra=SOURCES/'proveniencia-municipios2025.json'
    if 'municipios2025' not in data and extra.exists():data['municipios2025']=json.loads(extra.read_text())
    return data


def metadata(name,bounds,scope):
    return {'name':name,'bounds':bounds,'scope':scope,'source':'OpenStreetMap/Geofabrik e IBGE',
            'attribution':ATTRIBUTION,'license':'ODbL-1.0','data_as_of':'OSM 2026-11-16; recortes IBGE 2025',
            'sources':provenance(),'notice':'Mapa para consulta offline. Não informa vias bloqueadas, atendimento ou riscos em tempo real.'}


def region_shapes():
    data=json.loads((SOURCES/'estados.geojson').read_text())
    for f in data['features']:
        g=f['geometry'];polygons=[g['coordinates']] if g['type']=='Polygon' else g['coordinates']
        yield str(f['properties']['codarea']), [[tuple(p) for p in ring] for polygon in polygons for ring in polygon]


def build_master(source,dest,index):
    import osmium
    if dest.exists():raise ValueError('A base já existe. Use outro destino para não sobrescrever um mapa pronto.')
    partial=Path(str(dest)+'.building')
    if partial.exists():raise ValueError('Há uma construção parcial neste destino. Confira antes de retomar.')
    db=sqlite3.connect(partial);db.executescript('PRAGMA journal_mode=OFF;PRAGMA synchronous=OFF;PRAGMA cache_size=-32768;PRAGMA temp_store=FILE;')
    create(db);started=time.monotonic()
    class Handler(osmium.SimpleHandler):
        def __init__(self):super().__init__();self.ident=0;self.nodes=0;self.ways=0;self.skipped=0
        def emit(self,layer,cls,name,minz,parts):
            self.ident+=1;add_feature(db,self.ident,layer,cls,name,minz,parts)
            if self.ident%50000==0:db.commit();print('Feições',self.ident,'tempo',round(time.monotonic()-started),'s',flush=True)
        def node(self,n):
            self.nodes+=1
            place=n.tags.get('place');amenity=n.tags.get('amenity') or n.tags.get('shop') or n.tags.get('tourism')
            if not (place in PLACE_Z or amenity in POIS):return
            if not n.location.valid():return
            layer,cls,z=('place',place,PLACE_Z[place]) if place in PLACE_Z else ('poi',amenity,12 if amenity in ('hospital','fire_station') else 14)
            self.emit(layer,cls,n.tags.get('name',''),z,[[(n.location.lon,n.location.lat)]])
        def way(self,w):
            self.ways+=1
            road=w.tags.get('highway');water=w.tags.get('waterway');natural=w.tags.get('natural');land=w.tags.get('landuse')
            if road and (road in ROAD_Z or road.endswith('_link')):
                layer,cls,z='road',road,ROAD_Z.get(road,ROAD_Z.get(road.removesuffix('_link'),13)+2)
            elif water in ('river','stream','canal','drain'):
                layer,cls,z='waterway',water,8 if water=='river' else 13
            elif natural=='water' or land=='reservoir':layer,cls,z='water',w.tags.get('water','lake'),9
            elif w.tags.get('railway') in ('rail','light_rail'):layer,cls,z='rail',w.tags.get('railway'),11
            else:return
            try:coords=[(n.lon,n.lat) for n in w.nodes]
            except osmium.InvalidLocationError:self.skipped+=1;return
            if len(coords)<2:return
            self.emit(layer,cls,w.tags.get('name') or w.tags.get('ref',''),z,[coords])
    h=Handler()
    # Índice em arquivo: não exigir que todos os nós do Brasil caibam na RAM.
    h.apply_file(str(source),locations=True,idx='sparse_file_array,'+str(index),
                 filters=[osmium.filter.KeyFilter('highway','waterway','natural','landuse','railway','place','amenity','shop','tourism')])
    for code,parts in region_shapes():h.emit('land',code,'',2,parts)
    finish(db,metadata('Brasil · ruas, água e localidades',[-74,-35,-28,6],'brasil'))
    db.close();partial.replace(dest)
    print(json.dumps({'features':h.ident,'filtered_nodes_read':h.nodes,'filtered_ways_read':h.ways,'ways_missing_locations':h.skipped,'seconds':round(time.monotonic()-started)}),flush=True)


def municipality_bounds():
    import shapefile
    names=json.loads((SOURCES/'municipios-nomes.json').read_text());bycode={str(n['id']):n for n in names}
    with zipfile.ZipFile(SOURCES/'BR_Municipios_2025.zip') as z:
        shp=next(p for p in z.namelist() if p.endswith('.shp'));dbf=next(p for p in z.namelist() if p.endswith('.dbf'))
        seen=set()
        # pyshp lê em fluxo; não manter todas as geometrias na memória.
        with z.open(shp) as shapes,z.open(dbf) as records:
            reader=shapefile.Reader(shp=shapes,dbf=records,encoding='utf-8')
            for row in reader.iterShapeRecords():
                attrs=row.record.as_dict();code=str(attrs['CD_MUN'])
                # A malha também inclui áreas estaduais de lagoas, que não
                # são municípios na lista oficial de localidades.
                if code not in bycode:continue
                if code in seen:raise ValueError('Código municipal duplicado: '+code)
                seen.add(code)
                item=bycode[code];uf=((item.get('microrregiao') or {}).get('mesorregiao') or {}).get('UF') or item['regiao-imediata']['regiao-intermediaria']['UF']
                yield {'code':code,'name':item['nome'],'uf':uf['sigla'],'bounds':list(row.shape.bbox)}
        if seen!=set(bycode):raise ValueError('Municípios sem recorte: '+','.join(sorted(set(bycode)-seen)))


def cut(source,dest,name,bounds,scope,base=False):
    if dest.exists():return
    partial=Path(str(dest)+'.building')
    if partial.exists():partial.unlink()
    # Construção temporária sequencial: evitar milhares de escritas aleatórias
    # no disco externo. Só o arquivo concluído é copiado para o destino.
    scratch=Path(tempfile.mkdtemp(prefix='ultimo-livro-recorte-'))
    staging=scratch/'map.ulmap'
    db=sqlite3.connect(staging);db.executescript('PRAGMA journal_mode=OFF;PRAGMA synchronous=OFF;PRAGMA cache_size=-32768;')
    create(db)
    src=sqlite3.connect(source.resolve().as_uri()+'?mode=ro',uri=True)
    left,bottom,right,top=bounds
    rows=src.execute('SELECT f.*,i.minx,i.maxx,i.miny,i.maxy FROM feat_idx i JOIN feat f ON f.id=i.id '
        'WHERE i.maxx>=? AND i.minx<=? AND i.maxy>=? AND i.miny<=?'+(' AND i.minz<=6' if base else ''), (left,right,bottom,top))
    for ident,layer,cls,label,minz,geom,minx,maxx,miny,maxy in rows:
        db.execute('INSERT INTO feat VALUES (?,?,?,?,?,?)',(ident,layer,cls,label,minz,geom))
        db.execute('INSERT INTO feat_idx VALUES (?,?,?,?,?,?,?)',(ident,minx,maxx,miny,maxy,minz,30))
    finish(db,metadata(name,bounds,scope));src.close();db.close()
    shutil.copyfile(staging,partial);partial.replace(dest);shutil.rmtree(scratch)


def export_regions(master,only=None):
    from brasil.catalogo import ESTADOS
    destination=OUT/'recortes';destination.mkdir(exist_ok=True)
    entries=[]
    base=destination/'br-base.ulmap';cut(master,base,'Brasil · visão geral',[-74,-35,-28,6],'base',base=True)
    entries.append({'id':'map-br-base','kind':'map','file':base.name,'name':'Brasil · visão geral','scope':'base','path':str(base)})
    entries.append({'id':'map-br-full','kind':'map','file':master.name,'name':'Brasil · mapa detalhado','scope':'brasil','path':str(master)})
    # Dois primeiros dígitos do código municipal são o código IBGE da UF.
    cities=list(municipality_bounds());states={}
    for city in cities:
        states[city['code'][:2]]=city['uf']
    for code,parts in region_shapes():
        uf=states[code]
        if uf not in ESTADOS:raise ValueError('Estado inválido')
        flat=[p for part in parts for p in part];xs,ys=zip(*flat);bounds=[min(xs),min(ys),max(xs),max(ys)]
        file=destination/f'uf-{uf}.ulmap'
        print('Recorte estadual',uf,flush=True)
        cut(master,file,ESTADOS[uf]+' e entorno',bounds,'estado')
        entries.append({'id':'map-uf-'+uf,'kind':'map','file':file.name,'name':ESTADOS[uf]+' e entorno','scope':'estado','uf':uf,'path':str(file)})
    for number,city in enumerate(cities):
        if only and city['code'] not in only:continue
        file=destination/f'municipio-{city["code"]}.ulmap'
        cut(master,file,city['name']+' / '+city['uf']+' e entorno',city['bounds'],'municipio')
        entries.append({'id':'map-city-'+city['code'],'kind':'map','file':file.name,'name':city['name']+' / '+city['uf'],'scope':'municipio','uf':city['uf'],'code':city['code'],'path':str(file)})
        if number%100==0:print('Recortes municipais',number,'de',len(cities),flush=True)
    (OUT/'recortes.json').write_text(json.dumps(entries,ensure_ascii=False,indent=2)+'\n')
    print('Recortes prontos:',len(entries),flush=True)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=('master','regions'));ap.add_argument('--only',nargs='*')
    args=ap.parse_args();OUT.mkdir(parents=True,exist_ok=True)
    master=OUT/'brasil-2026-11-16.ulmap'
    if args.action=='master':build_master(SOURCES/'brazil-261116.osm.pbf',master,OUT/'nodes.index')
    else:export_regions(master,set(args.only) if args.only else None)

if __name__=='__main__':main()
