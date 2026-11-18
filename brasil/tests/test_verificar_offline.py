import hashlib
from pathlib import Path
import sqlite3
import subprocess
import tempfile
import sys
import types
import unittest
from unittest.mock import Mock, patch

from brasil.core import Store
from brasil import mapa_vetor, verificar_offline as offline


class OfflineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store = Store(self.tmp.name)

    def test_library_without_ai_is_useful_and_does_not_start_process(self):
        self.store.save_choices({'perfil': 'personalizada', 'modelo': 'sem-ia'})
        with patch.object(offline.subprocess, 'Popen') as launch:
            results = {r['id']: r for r in offline.check(self.store)['resultados']}
        self.assertEqual(results['pdf']['estado'], 'ok')
        self.assertEqual(results['zim']['estado'], 'pendente')
        self.assertEqual(results['mapa']['estado'], 'pendente')
        self.assertEqual(results['ia']['estado'], 'ignorado')
        launch.assert_not_called()

    def test_missing_model_is_pending(self):
        with self.assertRaises(offline.Pending):
            offline._ia(self.store)

    def test_corrupt_pdf_is_error_and_does_not_block_other_checks(self):
        Path(self.tmp.name, 'offline.pdf').write_bytes(b'%PDF-1.4 truncated')
        with patch.object(offline.guias_pdf, 'GUIDES_PATH', Path(self.tmp.name)):
            result = offline.check(self.store)['resultados']
        self.assertEqual(result[0]['estado'], 'erro')
        self.assertEqual(len(result), 4)

    def test_raster_reads_existing_tile_even_when_center_is_empty(self):
        path = Path(self.tmp.name) / 'teste.mbtiles'
        with sqlite3.connect(path) as db:
            db.execute('CREATE TABLE metadata(name TEXT,value TEXT)')
            db.executemany('INSERT INTO metadata VALUES (?,?)', [('format', 'png'), ('center', '120,0,5')])
            db.execute('CREATE TABLE tiles(zoom_level INTEGER,tile_column INTEGER,tile_row INTEGER,tile_data BLOB)')
            db.execute('INSERT INTO tiles VALUES (1,0,0,?)', (b'\x89PNG\r\n\x1a\nlocal',))
        self.store.import_file('mapa', path)
        self.assertIn('lidos localmente', offline._map(self.store))
        with sqlite3.connect(path) as db:
            db.execute('UPDATE tiles SET tile_data=?', (b'corrupt',))
        with self.assertRaisesRegex(ValueError, 'inválido'):
            offline._map(self.store)

    def test_vector_map_decodes_real_feature(self):
        path = Path(self.tmp.name) / 'teste.ulmap'
        with sqlite3.connect(path) as db:
            mapa_vetor.create(db)
            mapa_vetor.add_feature(db, 1, 'place', 'city', 'Cidade', 3, [[(-48, -15)]])
            mapa_vetor.finish(db, {'name': 'Teste', 'attribution': 'Teste', 'bounds': [-49,-16,-47,-14]})
        self.store.import_file('mapa', path)
        self.assertIn('Teste', offline._map(self.store))
        with sqlite3.connect(path) as db:
            db.execute('UPDATE feat SET geom=?', (b'corrupt',))
        # Corrupt compressed data must become an isolated result, not abort the job.
        result = {r['id']: r for r in offline.check(self.store)['resultados']}
        self.assertEqual(result['mapa']['estado'], 'erro')

    def test_zim_search_opens_article_in_each_collection(self):
        self.store.encyclopedias = Mock(return_value=[{'id': 'primeiro'}, {'id': 'segundo'}])
        self.store.zim_path = Mock(side_effect=lambda ident: Path(ident + '.zim'))
        def read(path, query=None, entry=None):
            if entry:
                return {'texto': 'Conteúdo real lido', 'titulo': 'Brasil'}
            return [{'entrada': 'A/Brasil'}] if query else {'busca': True}
        with patch.object(offline, 'read_zim', side_effect=read) as reader:
            self.assertIn('2 coleção', offline._zim(self.store))
        self.assertEqual(sum(call.kwargs.get('entry') == 'A/Brasil' for call in reader.call_args_list), 2)

    def test_zim_without_index_opens_main_entry(self):
        self.store.encyclopedias = Mock(return_value=[{'id': 'sem-indice'}])
        self.store.zim_path = Mock(return_value=Path('local.zim'))
        entry = types.SimpleNamespace(is_redirect=False, path='A/Inicio')
        archive = Mock(return_value=types.SimpleNamespace(main_entry=entry))
        module = types.ModuleType('libzim.reader')
        module.Archive = archive
        with patch.dict(sys.modules, {'libzim.reader': module}), patch.object(offline, 'read_zim', side_effect=[{'busca': False}, {'texto': 'Índice local'}]) as read:
            self.assertIn('ZIM', offline._zim(self.store))
        self.assertEqual(read.call_args.kwargs, {'entry': 'A/Inicio'})

    def prepared_model(self):
        path = Path(self.tmp.name) / 'model.gguf'
        path.write_bytes(b'test model')
        spec = {'size': path.stat().st_size, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'available_gib': 1}
        self.store.model_spec = Mock(return_value=spec)
        self.store.package_path = Mock(return_value=path)
        self.store.runner = Mock(return_value='/local/llama-completion')
        self.store.ready_model = Mock(return_value=(path, '/local/llama-completion'))
        self.store.chat_history = Mock(side_effect=AssertionError('history must not be read'))
        self.store.remember_chat = Mock(side_effect=AssertionError('history must not be written'))
        return path

    def test_inference_is_short_and_isolated_and_releases_process(self):
        path = self.prepared_model()
        process = Mock(returncode=0)
        process.communicate.return_value = ('OK', '')
        with patch.object(offline.subprocess, 'Popen', return_value=process) as launch:
            self.assertEqual(offline._ia(self.store)[0], 'ok')
        command = launch.call_args.args[0]
        self.assertEqual(command[command.index('-m') + 1], str(path))
        self.assertEqual(command[command.index('-n') + 1], '8')
        self.assertIsNone(self.store.proc)
        self.store.ready_model.assert_called_once_with(self.store.model_spec())

    def test_failed_preflight_never_launches_runner(self):
        self.prepared_model()
        self.store.ready_model.side_effect = ValueError('Memória insuficiente')
        with patch.object(offline.subprocess, 'Popen') as launch, self.assertRaisesRegex(ValueError, 'Memória'):
            offline._ia(self.store)
        launch.assert_not_called()

    def test_inference_timeout_kills_reaps_and_clears_process(self):
        self.prepared_model()
        process = Mock()
        process.communicate.side_effect = [subprocess.TimeoutExpired('llama', 90), ('', '')]
        with patch.object(offline.subprocess, 'Popen', return_value=process), self.assertRaisesRegex(ValueError, '90 segundos'):
            offline._ia(self.store)
        process.kill.assert_called_once()
        self.assertEqual(process.communicate.call_count, 2)
        self.assertIsNone(self.store.proc)

    def test_closing_app_does_not_spawn_process(self):
        self.prepared_model()
        self.store.closing.set()
        with patch.object(offline.subprocess, 'Popen') as launch, self.assertRaisesRegex(ValueError, 'fechando'):
            offline._ia(self.store)
        launch.assert_not_called()


if __name__ == '__main__':
    unittest.main()
