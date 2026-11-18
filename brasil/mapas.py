"""Seleção, catálogo e leitura dos mapas locais. Nenhuma chamada de rede."""
import json
from pathlib import Path
import unicodedata

from . import mapa_vetor,pacotes
from .arquivos import map_info,map_tile


def fold(text):
    return ''.join(c for c in unicodedata.normalize('NFD',text.casefold()) if not unicodedata.combining(c))


class MapSupport:
    def map_catalog_search(self,body):
        uf=body.get('uf','');query=body.get('busca','');offset=body.get('offset',0)
        if not isinstance(uf,str) or not isinstance(query,str) or len(query)>100 or type(offset) is not int or not 0<=offset<=10000:
            raise ValueError('Busca de mapas inválida.')
        selected=body.get('selecionados',[])
        if not isinstance(selected,list) or len(selected)>6000 or any(not isinstance(c,str) for c in selected):raise ValueError('Seleção de municípios inválida.')
        target=fold(query)
        items=[p for p in pacotes.maps_catalog().values() if p['scope']=='municipio' and (not uf or p.get('uf')==uf) and target in fold(p['name'])]
        items.sort(key=lambda p:fold(p['name']))
        return {'resultados':items[offset:offset+50],'total':len(items),'offset':offset,
                'estados':[p for p in pacotes.maps_catalog().values() if p['scope']=='estado'],
                'nacionais':[p for p in pacotes.maps_catalog().values() if p['scope'] in ('base','brasil')],
                'selecionados':[pacotes.maps_catalog()['map-city-'+c] for c in selected if isinstance(c,str) and 'map-city-'+c in pacotes.maps_catalog()][:6000],
                'disponivel':bool(pacotes.maps_catalog())}

    def chosen_map_ids(self,choices=None):
        choices=choices or self.choices() or {'mapa':'municipio','estados':[],'municipios':[]}
        known=pacotes.maps_catalog()
        if not known or choices['mapa']=='sem-mapas':return []
        if choices['mapa']=='brasil':return ['map-br-full']
        ids=['map-br-base']
        ids+=['map-uf-'+uf for uf in choices.get('estados',[])] if choices['mapa']=='estado' else ['map-city-'+code for code in choices.get('municipios',[])]
        return [i for i in ids if i in known]

    def installed_maps(self):
        with self.db() as db:rows=db.execute('SELECT id,path,name FROM maps ORDER BY name').fetchall()
        maps=[{'id':ident,'nome':name,'disponivel':Path(path).is_file()} for ident,path,name in rows]
        if 'mapa' in self.files():
            try:
                path=self.file_path('mapa')
                if not any(Path(row[1])==path for row in rows):maps.insert(0,{'id':'importado','nome':path.name,'disponivel':True})
            except ValueError:pass
        return maps

    def active_map_id(self):
        with self.db() as db:row=db.execute("SELECT value FROM settings WHERE key='active-map'").fetchone()
        known=self.installed_maps()
        if row and any(item['id']==row[0] for item in known):return row[0]
        return known[0]['id'] if known else None

    def map_path(self,ident=None):
        ident=ident or self.active_map_id()
        if not isinstance(ident,str):raise ValueError('Baixe ou importe um mapa primeiro.')
        if ident=='importado':return self.file_path('mapa')
        with self.db() as db:row=db.execute('SELECT path FROM maps WHERE id=?',(ident,)).fetchone()
        if not row or not Path(row[0]).is_file():raise ValueError('Mapa não encontrado. Reconecte o disco ou instale novamente.')
        return Path(row[0])

    def select_map(self,body):
        ident=body.get('id')
        if not isinstance(ident,str):raise ValueError('Selecione um mapa válido.')
        self.map_path(ident)
        with self.db() as db:db.execute('INSERT OR REPLACE INTO settings VALUES (?,?)',('active-map',ident))
        return {'mensagem':'Mapa selecionado.'}

    def map_metadata(self):
        return self._map_metadata(self.map_path())

    def _map_metadata(self, path):
        return mapa_vetor.info(path) if path.suffix.lower()=='.ulmap' else map_info(path)

    def map_at(self, body):
        lat, lon = body.get('lat'), body.get('lon')
        if type(lat) not in (int,float) or type(lon) not in (int,float) or not (-85 <= lat <= 85 and -180 <= lon <= 180):
            raise ValueError('Coordenadas fora da área que o visualizador pode mostrar.')
        active = self.active_map_id()
        best = None
        active_without_bounds = False
        for item in self.installed_maps():
            if not item['disponivel']:
                continue
            ident = item['id']
            try:
                bounds = self._map_metadata(self.map_path(ident)).get('bounds')
            except (ValueError, OSError):
                continue
            if bounds is None:
                active_without_bounds = active_without_bounds or ident == active
                continue
            left, bottom, right, top = bounds
            if left <= lon <= right and bottom <= lat <= top:
                size = (right-left) * (top-bottom)
                if best is None or size < best[0]:
                    best = (size, ident)
        if best is None:
            if active_without_bounds:
                return {'mensagem': 'Este mapa raster não declara seus limites. Confira a cobertura na tela.'}
            raise ValueError('Nenhum mapa instalado cobre este lugar. Instale o mapa da região.')
        return self.select_map({'id': best[1]})

    def vector_tile(self,z,x,y):return mapa_vetor.tile(self.map_path(),z,x,y)
    def raster_tile(self,z,x,y):return map_tile(self.map_path(),z,x,y)
    def search_map(self,body):
        path=self.map_path()
        if path.suffix.lower()!='.ulmap':raise ValueError('A busca de lugares requer um mapa vetorial da edição brasileira.')
        return mapa_vetor.search(path,body.get('busca',''))
