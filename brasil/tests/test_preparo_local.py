import base64
import copy
from concurrent.futures import ThreadPoolExecutor
import json
import sqlite3
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from brasil import preparo_local as preparo
from brasil.backup import export_backup, restore_backup
from brasil.core import Store

PNG = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jN1kAAAAASUVORK5CYII=')


class PreparoLocalTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.folder = Path(temporary.name)
        self.store = Store(self.folder / 'dados')
        self.plan = {field: '' for field in preparo.CAMPOS_PLANO}
        self.record = {'id': 'registro-1', 'data': '2026-11-18', 'descricao': 'Dano no telhado',
                       'protocolo': 'ABC', 'fotos': []}
        self.photo = self.folder / 'foto.png'
        self.photo.write_bytes(PNG)
        self.backup = self.folder / 'backup.json'

    def save(self, section, contents):
        return preparo.salvar(self.store, {'secao': section, 'dados': contents})

    def add_photo(self):
        self.save('recuperacao', [self.record])
        return preparo.adicionar_foto(self.store, self.record['id'], self.photo)

    def test_sections_survive_reopening_without_changing_existing_data(self):
        self.store.check({'id': 'luz', 'feito': True})
        before = self.store.checklist()
        contents = {
            'plano': dict(self.plan, encontro1='Casa da avó'),
            'lugares': [{'id': 'casa', 'nome': 'Casa', 'lat': -23.5, 'lon': -46.6, 'notas': 'Portão azul', 'revisado': '2026-11-18'}],
            'itens': [{'id': 'luz', 'nome': 'Lanterna', 'quantidade': '2', 'local': 'Mochila', 'revisar': '2027-01-01'}],
            'recuperacao': [self.record],
        }
        for section, value in contents.items():
            self.save(section, value)
        reopened = Store(self.store.folder)
        self.assertEqual(preparo.dados(reopened), contents)
        self.assertEqual(reopened.checklist(), before)
        self.save('itens', [])
        self.assertEqual(preparo.dados(self.store)['plano'], contents['plano'])

    def test_defaults_and_legacy_optional_fields(self):
        self.assertEqual(preparo.dados(self.store), {'plano': self.plan, 'lugares': [], 'itens': [], 'recuperacao': []})
        record = dict(self.record)
        del record['fotos']
        self.assertEqual(self.save('recuperacao', [record])['recuperacao'][0]['fotos'], [])
        place = {'id': 'x', 'nome': 'Casa', 'lat': 0, 'lon': 0, 'notas': ''}
        self.assertEqual(self.save('lugares', [place])['lugares'][0]['revisado'], '')

    def test_invalid_sections_never_modify_saved_data(self):
        self.save('plano', dict(self.plan, contato='Pessoa'))
        place = {'id': 'x', 'nome': 'Casa', 'lat': 0, 'lon': 0, 'notas': ''}
        item = {'id': 'luz', 'nome': 'Luz', 'quantidade': '1', 'local': '', 'revisar': ''}
        invalid = [
            {'secao': 'outro', 'dados': {}}, {'secao': [], 'dados': {}},
            {'secao': 'plano', 'dados': {}}, {'secao': 'plano', 'dados': dict(self.plan, apoio=None)},
            {'secao': 'plano', 'dados': dict(self.plan, apoio='\ud800')},
            {'secao': 'plano', 'dados': dict(self.plan, segredo='x')},
            {'secao': 'itens', 'dados': [dict(item, quantidade=1)]},
            {'secao': 'itens', 'dados': [dict(item, revisar='2026-02-30')]},
            {'secao': 'itens', 'dados': [item, item]},
            {'secao': 'recuperacao', 'dados': [dict(self.record, fotos=[{'id': 'a'*32, 'nome': 'ausente'}])]},
            {'secao': 'recuperacao', 'dados': [dict(self.record, data='amanhã')]},
            {'secao': 'recuperacao', 'dados': [dict(self.record, fotos='imagem')]},
            {'secao': 'recuperacao', 'dados': [dict(self.record, fotos=[{'id': '../x', 'nome': 'x'}])]},
        ]
        for coordinate in (True, '0', float('nan'), float('inf'), 91, 10**1000):
            invalid.append({'secao': 'lugares', 'dados': [dict(place, lat=coordinate)]})
        before = preparo.dados(self.store)
        for body in invalid:
            with self.subTest(body=body), self.assertRaises(ValueError):
                preparo.salvar(self.store, body)
            self.assertEqual(preparo.dados(self.store), before)

    def test_photo_is_copied_and_only_referenced_ids_are_accessible(self):
        result = self.add_photo()
        photo = result['item']
        self.assertEqual(result['dados']['recuperacao'][0]['fotos'], [photo])
        self.photo.unlink()
        self.assertEqual(preparo.foto_bytes(self.store, photo['id']), (PNG, 'image/png'))
        for invalid in ('../dados.sqlite', 'a'*32, None):
            with self.assertRaises(ValueError):
                preparo.foto_bytes(self.store, invalid)
        self.save('recuperacao', [])
        with self.assertRaises(ValueError):
            preparo.foto_bytes(self.store, photo['id'])
        with self.store.db() as db:
            self.assertEqual(db.execute('SELECT count(*) FROM preparo_fotos').fetchone()[0], 0)

    def test_concurrent_photo_imports_keep_both_references(self):
        self.save('recuperacao', [self.record])
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(preparo.adicionar_foto, self.store, self.record['id'], self.photo)
                       for _ in range(2)]
            results = [future.result() for future in futures]
        expected = {result['item']['id'] for result in results}
        self.assertEqual(len(expected), 2)
        self.assertEqual({photo['id'] for photo in preparo.dados(self.store)['recuperacao'][0]['fotos']}, expected)
        for identifier in expected:
            self.assertEqual(preparo.foto_bytes(self.store, identifier)[0], PNG)

    def test_photo_signature_and_record_are_validated(self):
        self.save('recuperacao', [self.record])
        before = preparo.dados(self.store)
        self.photo.write_text('<svg onload="alert(1)"></svg>')
        with self.assertRaises(ValueError):
            preparo.adicionar_foto(self.store, self.record['id'], self.photo)
        self.photo.write_bytes(PNG)
        with self.assertRaises(ValueError):
            preparo.adicionar_foto(self.store, 'ausente', self.photo)
        self.assertEqual(preparo.dados(self.store), before)
        with self.store.db() as db:
            self.assertEqual(db.execute('SELECT count(*) FROM preparo_fotos').fetchone()[0], 0)

    def test_photo_insertion_rolls_back_with_reference_failure(self):
        self.save('recuperacao', [self.record])
        with self.store.db() as db:
            db.execute("CREATE TRIGGER fail_photo BEFORE INSERT ON preparo_secoes BEGIN SELECT RAISE(ABORT, 'falha'); END")
        with self.assertRaises(sqlite3.IntegrityError):
            preparo.adicionar_foto(self.store, self.record['id'], self.photo)
        with self.store.db() as db:
            self.assertEqual(db.execute('SELECT count(*) FROM preparo_fotos').fetchone()[0], 0)
        self.assertEqual(preparo.dados(self.store)['recuperacao'], [self.record])

    def test_export_only_selected_fields_escaped_and_standalone(self):
        self.save('plano', dict(self.plan, encontro1='Praça <script>alert(1)</script> & café', contato='SEGREDO_CONTATO'))
        destination = self.folder / 'plano.html'
        preparo.exportar_plano(self.store, {'campos': ['encontro1']}, destination)
        document = destination.read_text(encoding='utf-8')
        self.assertIn('Praça &lt;script&gt;', document)
        self.assertNotIn('<script>', document)
        self.assertNotIn('SEGREDO_CONTATO', document)
        self.assertNotIn('Contato de referência', document)
        self.assertNotIn('http', document)
        self.assertIn('@media print', document)
        for fields in ([], ['contato', 'contato'], ['recuperacao'], [None], 'contato'):
            with self.assertRaises(ValueError):
                preparo.exportar_plano(self.store, {'campos': fields}, destination)

    def test_export_atomic_and_database_protected(self):
        destination = self.folder / 'plano.html'
        destination.write_text('anterior')
        with patch('brasil.preparo_local.os.replace', side_effect=OSError('disco cheio')):
            with self.assertRaises(OSError):
                preparo.exportar_plano(self.store, {'campos': ['contato']}, destination)
        self.assertEqual(destination.read_text(), 'anterior')
        self.assertFalse(list(self.folder.glob('.preparo-*')))
        with self.assertRaises(ValueError):
            preparo.exportar_plano(self.store, {'campos': ['contato']}, self.store.folder / 'dados.sqlite')

    def test_backup_roundtrip_includes_photos_and_old_backup_preserves_preparo(self):
        photo = self.add_photo()['item']
        self.save('plano', dict(self.plan, encontro1='Escola'))
        export_backup(self.store, self.backup)
        body = json.loads(self.backup.read_text())
        self.assertEqual(base64.b64decode(body['preparo']['fotos'][photo['id']]), PNG)
        target = Store(self.folder / 'restaurado')
        restore_backup(target, self.backup)
        self.assertEqual(preparo.dados(target), preparo.dados(self.store))
        self.assertEqual(preparo.foto_bytes(target, photo['id'])[0], PNG)
        del body['preparo']
        self.backup.write_text(json.dumps(body))
        restore_backup(target, self.backup)
        self.assertEqual(preparo.dados(target), preparo.dados(self.store))

    def test_bad_backup_photo_does_not_change_any_data(self):
        self.add_photo()
        export_backup(self.store, self.backup)
        valid = json.loads(self.backup.read_text())
        target = Store(self.folder / 'restaurado')
        target.check({'id': 'luz', 'feito': True})
        preparo.salvar(target, {'secao': 'plano', 'dados': dict(self.plan, contato='Preservado')})
        before = preparo.dados(target), target.checklist()
        for kind in ('missing', 'extra', 'bad_signature'):
            body = copy.deepcopy(valid)
            photos = body['preparo']['fotos']
            if kind == 'missing':
                photos.clear()
            elif kind == 'extra':
                photos['b'*32] = base64.b64encode(PNG).decode()
            else:
                photos[next(iter(photos))] = base64.b64encode(b'<svg/>').decode()
            self.backup.write_text(json.dumps(body))
            with self.assertRaises(ValueError):
                restore_backup(target, self.backup)
            self.assertEqual((preparo.dados(target), target.checklist()), before)

    def test_restore_failure_rolls_back_photos_and_sections_together(self):
        self.add_photo()
        self.store.remember_chat('Pergunta', 'Resposta', [])
        export_backup(self.store, self.backup, True)
        target = Store(self.folder / 'restaurado')
        before = preparo.dados(target)
        with target.db() as db:
            db.execute("CREATE TRIGGER fail_chat BEFORE INSERT ON chat_turns BEGIN SELECT RAISE(ABORT, 'falha'); END")
        with self.assertRaises(sqlite3.IntegrityError):
            restore_backup(target, self.backup)
        self.assertEqual(preparo.dados(target), before)
        with target.db() as db:
            self.assertEqual(db.execute('SELECT count(*) FROM preparo_fotos').fetchone()[0], 0)


if __name__ == '__main__':
    unittest.main()
