import base64
from pathlib import Path
import sqlite3
import tempfile
import unittest
from brasil.arquivos import map_info,map_tile,TextOnly,read_zim
from brasil.core import Store

class Maps(unittest.TestCase):
    def test_raster_map_reads_tms_and_refuses_invalid_coordinates(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'mapa.mbtiles'
            image=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a5l8AAAAASUVORK5CYII=')
            with sqlite3.connect(path) as db:
                db.execute('CREATE TABLE metadata(name TEXT,value TEXT)')
                db.executemany('INSERT INTO metadata VALUES (?,?)',[('format','png'),('name','Mapa de teste'),('attribution','OpenStreetMap contributors')])
                db.execute('CREATE TABLE tiles(zoom_level INTEGER,tile_column INTEGER,tile_row INTEGER,tile_data BLOB)')
                db.execute('INSERT INTO tiles VALUES (1,0,0,?)',(image,))
            db.close()
            info=map_info(path)
            self.assertEqual((info['z'],info['x'],info['y']),(1,0,1))
            self.assertEqual(map_tile(path,1,0,1),(image,'image/png'))
            self.assertIsNone(map_tile(path,1,1,1))
            with self.assertRaises(ValueError): map_tile(path,1,-1,1)
            s=Store(Path(tmp)/'data');s.import_file('mapa',path)
            self.assertEqual(s.files()['mapa'],'mapa.mbtiles')
            path.unlink()
            with self.assertRaises(ValueError):s.file_path('mapa')

    def test_article_strips_scripts_from_plain_text(self):
        p=TextOnly();p.feed('<h1>Água</h1><script>alert(1)</script><p>Texto <b>útil</b></p>')
        self.assertNotIn('alert',''.join(p.parts))
        self.assertIn('Texto útil',''.join(p.parts))

try:
    from libzim.writer import Creator,Item,StringProvider,Hint
    ZIM=True
except ImportError: ZIM=False

@unittest.skipUnless(ZIM,'leitor libzim opcional não instalado neste interpretador')
class Encyclopedia(unittest.TestCase):
    def test_real_zim_search_and_article(self):
        class Article(Item):
            def get_path(self):return 'A/Energia'
            def get_title(self):return 'Energia doméstica'
            def get_mimetype(self):return 'text/html'
            def get_contentprovider(self):return StringProvider('<html><title>Energia doméstica</title><p>Iluminação com lanternas e cópias de documentos.</p><script>nunca executar</script></html>')
            def get_hints(self):return {Hint.FRONT_ARTICLE:1}
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'enciclopedia.zim'
            creator=Creator(path).config_indexing(True,'por')
            with creator as c:
                c.add_item(Article());c.set_mainpath('A/Energia')
            found=read_zim(path,query='lanternas')
            self.assertEqual(found[0]['entrada'],'A/Energia')
            article=read_zim(path,entry=found[0]['entrada'])
            self.assertIn('Iluminação',article['texto'])
            self.assertNotIn('nunca executar',article['texto'])
            s=Store(Path(tmp)/'data');s.import_file('zim',path)
            self.assertTrue(s.search_zim({'busca':'lanternas'})['resultados'])
            self.assertEqual(read_zim(path,query='energia doméstica')[0]['titulo'],'Energia doméstica')
            second=Path(tmp)/'segunda.zim'
            with Creator(second).config_indexing(True,'por') as c:
                c.add_item(Article());c.set_mainpath('A/Energia')
            s.import_file('zim',second)
            hits=s.search_zim({'busca':'lanternas'})['resultados']
            self.assertEqual(len({hit['colecao'] for hit in hits}),2)
            refs=s.sources_for('lanternas')
            self.assertEqual(len([ref for ref in refs if ref['tipo']=='zim']),2)
            for ref in refs:
                if ref['tipo']=='zim':self.assertIn('Iluminação',s.article_zim(ref)['texto'])

if __name__=='__main__':unittest.main()
