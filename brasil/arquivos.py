"""Leitores locais limitados: ZIM em texto e mapas MBTiles raster."""
from html.parser import HTMLParser
from pathlib import Path
import sqlite3
import math
import re
from .sqlite_local import Connection

class TextOnly(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.skip=0
        self.parts=[]
    def handle_starttag(self, tag, attrs):
        if tag in ('head','script','style'): self.skip+=1
        if tag in ('p','div','br','h1','h2','h3','li','tr'): self.parts.append('\n')
        if tag in ('td','th'): self.parts.append(' ')
    def handle_endtag(self,tag):
        if tag in ('head','script','style') and self.skip: self.skip-=1
    def handle_data(self,data):
        if not self.skip: self.parts.append(data)


def read_zim(path, query=None, entry=None):
    try:
        from libzim.reader import Archive
        from libzim.search import Searcher,Query
    except ImportError:
        raise ValueError('O leitor ZIM não está instalado nesta cópia. Instale o pacote completo da edição brasileira.')
    try:
        arc=Archive(Path(path))
        if entry is not None:
            item=arc.get_entry_by_path(entry).get_item()
            if not item.mimetype.startswith('text/html'):
                raise ValueError('Esta versão abre apenas artigos HTML em texto.')
            if item.size>2*1024*1024: raise ValueError('Artigo grande demais para esta versão.')
            raw=bytes(item.content)
            if len(raw)>2*1024*1024: raise ValueError('Artigo grande demais para esta versão.')
            parser=TextOnly();parser.feed(raw.decode('utf-8','replace'))
            text = '\n'.join(clean for line in ''.join(parser.parts).splitlines() if (clean := re.sub(r'\s+', ' ', line).strip()))
            return {'titulo':arc.get_entry_by_path(entry).title, 'texto':text[:120000]}
        if not query:
            return {'titulo':Path(path).name,'busca':bool(arc.has_fulltext_index)}
        if not arc.has_fulltext_index:
            raise ValueError('Este arquivo ZIM não contém índice de busca.')
        matches = []
        seen = set()
        # Correspondência exata deve anteceder a pontuação textual de termos
        # frequentes, que pode favorecer listas e desambiguações em arquivos mini.
        for term in query.split(' OR ')[:6]:
            for title in dict.fromkeys((term, term[:1].upper() + term[1:], term.title())):
                try:
                    entry = arc.get_entry_by_title(title)
                    if entry.path not in seen:
                        seen.add(entry.path)
                        matches.append({'titulo':entry.title,'entrada':entry.path})
                except (KeyError, RuntimeError):
                    pass
        results = Searcher(arc).search(Query().set_query(query))
        for path in results.getResults(0,12):
            if path not in seen:
                seen.add(path)
                matches.append({'titulo':arc.get_entry_by_path(path).title,'entrada':path})
        return matches[:12]
    except (RuntimeError, KeyError, OSError) as e:
        raise ValueError('Não foi possível ler esta enciclopédia. Verifique o arquivo ZIM.') from e


def map_info(path):
    try:
        with sqlite3.connect(Path(path).resolve().as_uri()+'?mode=ro',uri=True,factory=Connection) as db:
            metadata=dict(db.execute('SELECT name,value FROM metadata'))
            if metadata.get('format','').lower() not in ('png','jpg','jpeg','webp'):
                raise ValueError('Escolha MBTiles com imagens PNG, JPEG ou WebP. MBTiles vetorial não é suportado; use os mapas .ulmap do catálogo.')
            row=db.execute('SELECT zoom_level,tile_column,tile_row FROM tiles ORDER BY zoom_level LIMIT 1').fetchone()
            if row is None: raise ValueError('Este mapa não contém imagens.')
            z,x,tms_y=map(int,row)
            if not 0<=z<=22: raise ValueError('Nível de mapa inválido.')
            y=2**z-1-tms_y
            bounds = None
            if 'bounds' in metadata:
                try:
                    left, bottom, right, top = map(float, metadata['bounds'].split(','))
                    if -180 <= left < right <= 180 and -90 <= bottom < top <= 90:
                        bounds = [left, bottom, right, top]
                except (AttributeError, TypeError, ValueError):
                    pass
            if 'center' in metadata:
                lon,lat,z0=map(float,metadata['center'].split(','))
                z=int(z0)
                if not 0<=z<=22: raise ValueError('Nível de mapa inválido.')
                n=2**z
                x=int((lon+180)/360*n)
                lat=max(-85,min(85,lat))
                y=int((1-math.asinh(math.tan(math.radians(lat)))/math.pi)/2*n)
            return {'nome':metadata.get('name',Path(path).name),'atribuicao':metadata.get('attribution','Verifique as atribuições do fornecedor do mapa.'),
                    'z':z,'x':x,'y':y,'minzoom':int(metadata.get('minzoom',0)),'maxzoom':int(metadata.get('maxzoom',18)),
                    'formato':metadata['format'].lower(),'bounds':bounds}
    except (sqlite3.Error, OverflowError, TypeError) as e:
        raise ValueError('Não foi possível abrir o mapa MBTiles.') from e


def map_tile(path,z,x,y):
    if not all(type(n) is int for n in (z,x,y)) or not 0<=z<=22 or not 0<=x<2**z or not 0<=y<2**z:
        raise ValueError('Coordenada de mapa inválida.')
    with sqlite3.connect(Path(path).resolve().as_uri()+'?mode=ro',uri=True,factory=Connection) as db:
        row=db.execute('SELECT tile_data FROM tiles WHERE zoom_level=? AND tile_column=? AND tile_row=?',(z,x,2**z-1-y)).fetchone()
    if not row: return None
    data=bytes(row[0])
    if len(data)>4*1024*1024: raise ValueError('Imagem de mapa grande demais.')
    if data.startswith(b'\x89PNG'): return data,'image/png'
    if data.startswith(b'\xff\xd8'): return data,'image/jpeg'
    if data.startswith(b'RIFF') and data[8:12]==b'WEBP': return data,'image/webp'
    raise ValueError('Formato de imagem de mapa inválido.')
