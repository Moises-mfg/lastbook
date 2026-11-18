"""Busca local com fichas editoriais reais e mapas SQLite descartáveis."""
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from brasil import busca_offline, mapa_vetor
from brasil.core import Store


class Search(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.store = Store(self.root / 'data')

    def add_map(self, ident, name, places):
        path = self.root / (ident + '.ulmap')
        with sqlite3.connect(path) as db:
            mapa_vetor.create(db)
            for i, place in enumerate(places, 1):
                mapa_vetor.add_feature(db, i, 'poi', 'hospital', place, 12, [[(-48, -16)]])
            mapa_vetor.finish(db, {'name': name, 'bounds': [-49, -17, -47, -15], 'attribution': 'Teste'})
        with self.store.db() as db:
            db.execute('INSERT INTO maps VALUES (?,?,?)', (ident, str(path), name))
        return path

    def test_text_and_pdf_page_content_without_network(self):
        with patch('socket.socket', side_effect=AssertionError('A busca não deve usar rede')):
            result = busca_offline.search(self.store, {'busca': 'CONTAMINADA'})
            self.assertEqual([g['id'] for g in result['guias']], ['enchentes'])
            # Texto exclusivo do corpo da primeira página; ausente do catálogo PDF.
            result = busca_offline.search(self.store, {'busca': 'monoxido de carbono'})
            self.assertEqual([(g['id'], g['pagina']) for g in result['pdfs']], [('energia', 1)])
            result = busca_offline.search(self.store, {'busca': 'ofuscamento'})
            self.assertEqual([(g['id'], g['pagina']) for g in result['pdfs']], [('energia', 2)])
            self.assertEqual(result['zim'], [])
            self.assertEqual(result['mapas'], [])

    def test_all_installed_maps_return_openable_references_without_switching_active(self):
        self.add_map('a', 'Mapa A', ['Hospital São José'])
        self.add_map('b', 'Mapa B', ['Hospital São Pedro'])
        self.store.select_map({'id': 'a'})
        result = busca_offline.search(self.store, {'busca': 'hospital sao'})
        self.assertEqual({h['mapa_id'] for h in result['mapas']}, {'a', 'b'})
        self.assertEqual(self.store.active_map_id(), 'a')
        for hit in result['mapas']:
            self.assertAlmostEqual(hit['lon'], -48)
            self.assertAlmostEqual(hit['lat'], -16)
            self.assertTrue(self.store.map_path(hit['mapa_id']).is_file())

    def test_broken_and_disconnected_files_do_not_hide_other_groups(self):
        broken = self.root / 'broken.ulmap'
        broken.write_text('Inválido')
        with self.store.db() as db:
            db.execute('INSERT INTO maps VALUES (?,?,?)', ('bad', str(broken), 'Mapa quebrado'))
            db.execute('INSERT INTO maps VALUES (?,?,?)', ('gone', str(self.root/'gone.ulmap'), 'Mapa ausente'))
        self.add_map('good', 'Mapa válido', ['Hospital'])
        books = [{'id': 'zim', 'nome': 'Enciclopédia', 'disponivel': True}]
        with patch.object(self.store, 'encyclopedias', return_value=books), \
                patch.object(self.store, 'zim_path', side_effect=ValueError('Disco ausente')):
            result = busca_offline.search(self.store, {'busca': 'Hospital'})
        self.assertEqual([h['mapa_id'] for h in result['mapas']], ['good'])
        self.assertEqual({h['id'] for h in result['indisponiveis']}, {'zim', 'bad', 'gone'})

    def test_zim_references_and_result_limits(self):
        self.add_map('many', 'Muitos lugares', ['Hospital %02d' % i for i in range(30)])
        books = [{'id': str(i), 'nome': 'Livro ' + str(i), 'disponivel': True} for i in range(4)]
        hits = [{'titulo': 'Hospital %d' % i, 'entrada': 'A/Hospital_%d' % i} for i in range(12)]
        with patch.object(self.store, 'encyclopedias', return_value=books), \
                patch.object(self.store, 'zim_path', return_value=self.root/'book.zim'), \
                patch('brasil.busca_offline.read_zim', return_value=hits) as reader:
            result = busca_offline.search(self.store, {'busca': 'Hospital'})
        self.assertEqual(len(result['zim']), 20)
        self.assertEqual(len(result['mapas']), 20)
        self.assertEqual(reader.call_count, 2)
        self.assertEqual(result['zim'][0], dict(hits[0], colecao='0', nome_colecao='Livro 0'))

    def test_invalid_queries(self):
        for body in (None, [], {}, {'busca': ''}, {'busca': '  '}, {'busca': []},
                     {'busca': 'a' * 161}, {'busca': '\u0301'}):
            with self.subTest(body=body), self.assertRaises(ValueError):
                busca_offline.search(self.store, body)


if __name__ == '__main__':
    unittest.main()
