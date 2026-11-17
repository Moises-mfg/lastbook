"""Mapa vetorial local ULMP: SQLite/RTree e geometrias delta, sem rede ou dependências GIS."""
from array import array
import json
import math
from pathlib import Path
import sqlite3
import sys
import zlib
from .sqlite_local import Connection

APP_ID=0x554c4d50
SCHEMA=1
EXTENT=512
MAX_GEOMETRY=2*1024*1024


def connect(path):
    db=sqlite3.connect(Path(path).resolve().as_uri()+'?mode=ro',uri=True,factory=Connection)
    db.execute('PRAGMA query_only=ON')
    db.execute('PRAGMA cache_size=-4096')
    return db


def encode(parts):
    data=array('i',[len(parts)])
    for part in parts:
        data.append(len(part));x=y=0
        for lon,lat in part:
            nx,ny=round(lon*1e6),round(lat*1e6)
            data.extend((nx-x,ny-y));x,y=nx,ny
    if sys.byteorder!='little':data.byteswap()
    return zlib.compress(data.tobytes(),6)


def decode(blob):
    decoder=zlib.decompressobj()
    raw=decoder.decompress(blob,MAX_GEOMETRY+1)
    if len(raw)>MAX_GEOMETRY or decoder.unconsumed_tail or not decoder.eof:
        raise ValueError('Geometria de mapa grande demais ou incompleta.')
    if len(raw)%4:raise ValueError('Geometria inválida.')
    data=array('i');data.frombytes(raw)
    if sys.byteorder!='little':data.byteswap()
    if not data or not 0<=data[0]<=10000:raise ValueError('Geometria inválida.')
    parts=[];pos=1
    for _ in range(data[0]):
        if pos>=len(data):raise ValueError('Geometria truncada.')
        count=data[pos];pos+=1
        if count<1 or count>200000 or pos+count*2>len(data):raise ValueError('Geometria inválida.')
        part=[];x=y=0
        for _ in range(count):
            x+=data[pos];y+=data[pos+1];pos+=2
            if not -180e6<=x<=180e6 or not -90e6<=y<=90e6:raise ValueError('Coordenada inválida.')
            part.append((x/1e6,y/1e6))
        parts.append(part)
    if pos!=len(data):raise ValueError('Geometria inválida.')
    return parts


def create(db):
    db.executescript(f'''PRAGMA application_id={APP_ID}; PRAGMA user_version={SCHEMA};
      CREATE TABLE feat(id INTEGER PRIMARY KEY,layer TEXT NOT NULL,cls TEXT NOT NULL,name TEXT,minz INTEGER NOT NULL,geom BLOB NOT NULL);
      CREATE VIRTUAL TABLE feat_idx USING rtree(id,minx,maxx,miny,maxy,minz,maxz);
      CREATE TABLE meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);
      CREATE VIRTUAL TABLE names USING fts5(name,feature_id UNINDEXED,tokenize='unicode61 remove_diacritics 2');''')


def add_feature(db,ident,layer,cls,name,minz,parts):
    flat=[point for part in parts for point in part]
    if not flat:return
    xs,ys=zip(*flat);bounds=(min(xs),max(xs),min(ys),max(ys))
    db.execute('INSERT INTO feat VALUES (?,?,?,?,?,?)',(ident,layer,cls,(name or '')[:250],minz,encode(parts)))
    db.execute('INSERT INTO feat_idx VALUES (?,?,?,?,?,?,?)',(ident,*bounds,minz,30))


def finish(db,metadata):
    db.execute("INSERT INTO names(name,feature_id) SELECT name,id FROM feat WHERE name!='' AND layer IN ('place','poi','road')")
    db.executemany('INSERT INTO meta VALUES (?,?)',[(key,str(value) if not isinstance(value,(list,dict)) else json.dumps(value,ensure_ascii=False)) for key,value in metadata.items()])
    db.commit()
    db.execute('ANALYZE');db.commit()


def info(path):
    try:
        with connect(path) as db:
            if db.execute('PRAGMA application_id').fetchone()[0]!=APP_ID or db.execute('PRAGMA user_version').fetchone()[0]!=SCHEMA:
                raise ValueError('Formato de mapa vetorial não reconhecido.')
            meta=dict(db.execute('SELECT key,value FROM meta'))
            bounds=json.loads(meta['bounds'])
            if len(bounds)!=4 or not all(type(x) in (int,float) and math.isfinite(x) for x in bounds):raise ValueError('Cobertura inválida.')
            left,bottom,right,top=bounds
            if not -180<=left<right<=180 or not -85<=bottom<top<=85:raise ValueError('Cobertura inválida.')
            lon,lat=(left+right)/2,(bottom+top)/2
            zoom=max(2,min(15,int(math.log2(360/max(right-left,top-bottom)*1.3))))
            return {'nome':meta['name'],'formato':'ulmap','bounds':bounds,'atribuicao':meta['attribution'],
                    'licenca':meta.get('license','ODbL-1.0'),'licenca_url':meta.get('license_url',''),'data':meta.get('data_as_of',''),
                    'fonte':meta.get('source',''),'z':zoom,'x':int((lon+180)/360*2**zoom),
                    'y':int((1-math.asinh(math.tan(math.radians(lat)))/math.pi)/2*2**zoom),'minzoom':2,'maxzoom':18}
    except (sqlite3.Error,KeyError,TypeError,json.JSONDecodeError) as error:
        raise ValueError('Não foi possível ler este mapa vetorial.') from error


def tile(path,z,x,y):
    if not all(type(v) is int for v in (z,x,y)) or not 0<=z<=18 or not 0<=x<2**z or not 0<=y<2**z:raise ValueError('Coordenada de mapa inválida.')
    n=2**z
    left,right=x/n*360-180,(x+1)/n*360-180
    bottom=math.degrees(math.atan(math.sinh(math.pi*(1-2*(y+1)/n))))
    top=math.degrees(math.atan(math.sinh(math.pi*(1-2*y/n))))
    pad=(right-left)*.03
    layers={};points=0;truncated=False
    with connect(path) as db:
        rows=db.execute('SELECT f.layer,f.cls,f.name,f.geom FROM feat_idx i JOIN feat f ON f.id=i.id '
            'WHERE i.maxx>=? AND i.minx<=? AND i.maxy>=? AND i.miny<=? AND i.minz<=? ORDER BY f.minz,f.id LIMIT 4001',
            (left-pad,right+pad,bottom-pad,top+pad,z))
        for index,(layer,cls,name,geom) in enumerate(rows):
            if index==4000 or points>100000:truncated=True;break
            output=[]
            for part in decode(geom):
                coords=[];last=None
                for lon,lat in part:
                    px=((lon+180)/360*n-x)*EXTENT
                    py=((1-math.asinh(math.tan(math.radians(max(-85,min(85,lat)))))/math.pi)/2*n-y)*EXTENT
                    if last is None or abs(px-last[0])+abs(py-last[1])>.7:
                        coords.extend((round(px,1),round(py,1)));last=(px,py)
                if coords:
                    output.append(coords);points+=len(coords)//2
            if output:layers.setdefault(layer,[]).append([cls,name,output])
    return {'layers':layers,'extent':EXTENT,'truncado':truncated}


def search(path,query):
    if not isinstance(query,str) or not 1<=len(query.strip())<=160:raise ValueError('Digite um lugar ou rua de até 160 caracteres.')
    terms=[part for part in query.replace('"',' ').split() if part]
    if not terms:return []
    match=' AND '.join('"'+part+'"*' for part in terms[:8])
    with connect(path) as db:
        rows=db.execute('SELECT f.id,f.name,f.layer,f.cls,(i.minx+i.maxx)/2,(i.miny+i.maxy)/2 FROM names '
            'JOIN feat f ON f.id=CAST(names.feature_id AS INTEGER) JOIN feat_idx i ON i.id=f.id '
            "WHERE names MATCH ? GROUP BY f.name,f.layer ORDER BY CASE f.layer WHEN 'place' THEN 0 WHEN 'poi' THEN 1 ELSE 2 END LIMIT 25",(match,))
        return [{'id':ident,'nome':name,'tipo':layer,'classe':cls,'lon':lon,'lat':lat} for ident,name,layer,cls,lon,lat in rows]
