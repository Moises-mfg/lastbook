import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
import zlib

from brasil import mapa_vetor as mv
from tools import construir_mapas_br as builder

class VectorMap(unittest.TestCase):
    def test_geometry_roundtrip_and_corruption_limits(self):
        parts=[[(-48.1,-16.4),(-48.10001,-16.40002)],[(-48,-16)]]
        self.assertEqual(mv.decode(mv.encode(parts)),parts)
        for bad in (b'broken',zlib.compress(b'123'),zlib.compress(b'x'*(mv.MAX_GEOMETRY+1))):
            with self.subTest(size=len(bad)),self.assertRaises((ValueError,zlib.error)):mv.decode(bad)

    def test_real_sqlite_tiles_search_and_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'local.ulmap';db=sqlite3.connect(path);mv.create(db)
            mv.add_feature(db,1,'road','primary','Avenida Brasil',7,[[(-48.01,-16.01),(-47.99,-15.99)]])
            mv.add_feature(db,2,'poi','hospital','Hospital de Teste',12,[[(-48,-16)]])
            mv.finish(db,{'name':'Teste','bounds':[-48.1,-16.1,-47.9,-15.9],'attribution':'OpenStreetMap contributors','license':'ODbL-1.0'});db.close()
            meta=mv.info(path);self.assertEqual(meta['formato'],'ulmap')
            hits=mv.search(path,'Avenida Bras');self.assertEqual(hits[0]['nome'],'Avenida Brasil')
            z=13;n=2**z;x=int((-48+180)/360*n)
            import math
            y=int((1-math.asinh(math.tan(math.radians(-16)))/math.pi)/2*n)
            tile=mv.tile(path,z,x,y)
            self.assertEqual(tile['layers']['road'][0][1],'Avenida Brasil')
            self.assertEqual(tile['layers']['poi'][0][0],'hospital')
            with self.assertRaises(ValueError):mv.tile(path,40,0,0)

try:
    import osmium
    OSMIUM=True
except ImportError:OSMIUM=False

@unittest.skipUnless(OSMIUM,'dependência de construção osmium não instalada')
class Builder(unittest.TestCase):
    def test_osm_stream_to_database_and_region_cut(self):
        source='''<osm version="0.6"><node id="1" lon="-48.01" lat="-16.01" version="1"/>
<node id="2" lon="-47.99" lat="-15.99" version="1"/>
<node id="3" lon="-48" lat="-16" version="1"><tag k="amenity" v="hospital"/><tag k="name" v="Hospital Local"/></node>
<node id="4" lon="-48.001" lat="-16.001" version="1"><tag k="place" v="city"/><tag k="name" v="Cidade"/></node>
<way id="10" version="1"><nd ref="1"/><nd ref="2"/><tag k="highway" v="primary"/><tag k="name" v="Rua Principal"/></way></osm>'''
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);src=root/'source.osm';src.write_text(source);dest=root/'map.ulmap'
            with patch.object(builder,'provenance',return_value={'teste':True}),patch.object(builder,'region_shapes',return_value=[]):
                builder.build_master(src,dest,root/'nodes.index')
                city=root/'city.ulmap';builder.cut(dest,city,'Recorte',[-48.1,-16.1,-47.9,-15.9],'municipio')
            self.assertEqual(mv.search(city,'Hospital')[0]['nome'],'Hospital Local')
            self.assertEqual(mv.search(city,'Rua')[0]['nome'],'Rua Principal')
            self.assertEqual(mv.info(city)['nome'],'Recorte')

if __name__=='__main__':unittest.main()
