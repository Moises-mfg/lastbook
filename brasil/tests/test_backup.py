import copy
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from brasil.backup import export_backup, restore_backup
from brasil.core import Store


class BackupTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.folder = Path(self.temporary.name)
        self.source = Store(self.folder / 'origem')
        self.target = Store(self.folder / 'destino')
        self.path = self.folder / 'backup.json'
        self.source.save_choices({'perfil': 'personalizada', 'modelo': 'sem-ia', 'estados': ['SP']})
        self.source.check({'id': 'luz', 'feito': True})
        self.source.remember_chat('Água?', 'Conserve água.', [{'titulo': 'Água', 'tipo': 'guia', 'id': 'agua'}])
        self.target.save_choices({'perfil': 'leve'})
        self.target.remember_chat('Conversa atual', 'Resposta atual', [])

    def read(self):
        return json.loads(self.path.read_text(encoding='utf-8'))

    def write(self, body):
        self.path.write_text(json.dumps(body), encoding='utf-8')

    def snapshot(self, store):
        with store.db() as db:
            return {table: db.execute('SELECT * FROM ' + table).fetchall()
                    for table in ('settings', 'checklist', 'chat_turns', 'maps', 'encyclopedias')}

    def test_roundtrip_preserves_personal_data_and_external_references(self):
        with self.target.db() as db:
            db.execute('INSERT INTO maps VALUES (?,?,?)', ('mapa-local', '/destino/mapa.ulmap', 'Meu mapa'))
            db.execute('INSERT INTO encyclopedias VALUES (?,?,?)', ('zim-local', '/destino/wiki.zim', 'Minha wiki'))
            db.execute('INSERT INTO settings VALUES (?,?)', ('active-map', 'mapa-local'))
        export_backup(self.source, self.path, True)
        result = restore_backup(self.target, self.path)
        self.assertTrue(result['chat_incluido'])
        self.assertEqual(self.source.choices(), self.target.choices())
        self.assertEqual(self.source.checklist(), self.target.checklist())
        source_turn = self.source.chat_history()[0]
        target_turn = self.target.chat_history()[0]
        for field in ('pergunta', 'resposta', 'fontes', 'criado_em'):
            self.assertEqual(source_turn[field], target_turn[field])
        snapshot = self.snapshot(self.target)
        self.assertEqual(snapshot['maps'][0][1], '/destino/mapa.ulmap')
        self.assertEqual(snapshot['encyclopedias'][0][1], '/destino/wiki.zim')
        self.assertIn(('active-map', 'mapa-local'), snapshot['settings'])

    def test_chat_is_opt_in_and_absence_preserves_existing_history(self):
        before = self.target.chat_history()
        export_backup(self.source, self.path)
        self.assertNotIn('conversas', self.read())
        result = restore_backup(self.target, self.path)
        self.assertFalse(result['chat_incluido'])
        self.assertEqual(before, self.target.chat_history())

    def test_explicit_empty_history_clears_history_and_stale_answer(self):
        self.source.clear_chat()
        self.target.job = {'estado': 'concluido', 'resposta': 'Resposta anterior'}
        export_backup(self.source, self.path, True)
        restore_backup(self.target, self.path)
        self.assertEqual(self.target.chat_history(), [])
        self.assertEqual(self.target.job, {'estado': 'parado'})

    def test_export_contains_all_history_beyond_display_limit(self):
        for index in range(105):
            self.source.remember_chat(str(index), 'Resposta', [])
        self.assertEqual(len(self.source.chat_history()), 100)
        export_backup(self.source, self.path, True)
        self.assertEqual(len(self.read()['conversas']), 106)
        restore_backup(self.target, self.path)
        with self.target.db() as db:
            self.assertEqual(db.execute('SELECT count(*) FROM chat_turns').fetchone()[0], 106)

    def test_empty_store_can_roundtrip_and_reset_choices(self):
        empty = Store(self.folder / 'vazio')
        export_backup(empty, self.path)
        restore_backup(self.target, self.path)
        self.assertIsNone(self.target.choices())

    def test_malformed_content_never_changes_database(self):
        export_backup(self.source, self.path, True)
        valid = self.read()
        invalid = [None, [], {}, dict(valid, versao=True), dict(valid, versao=2),
                   dict(valid, formato='outro'), dict(valid, escolhas=[]),
                   dict(valid, escolhas=dict(valid['escolhas'], modelo='../../modelo')),
                   dict(valid, checklist=[{'id': 'luz', 'feito': 1}]),
                   dict(valid, checklist=[{'id': '../../fora', 'feito': True}]),
                   dict(valid, checklist=[{'id': 'luz', 'feito': True}] * 2),
                   dict(valid, conversas=None), dict(valid, conversas=[{}]),
                   dict(valid, conversas=[dict(valid['conversas'][0], fontes=[{'titulo': []}])]),
                   dict(valid, conversas=[dict(valid['conversas'][0], pergunta='\ud800')]),
                   dict(valid, caminho='/tmp/nao-usar'),
                   dict(valid, escolhas=dict(valid['escolhas'], caminho='/tmp/nao-usar'))]
        before = self.snapshot(self.target)
        for body in invalid:
            with self.subTest(body=body):
                self.write(body)
                with self.assertRaises(ValueError):
                    restore_backup(self.target, self.path)
                self.assertEqual(before, self.snapshot(self.target))

    def test_rejects_duplicate_keys_nonfinite_values_and_broken_json(self):
        before = self.snapshot(self.target)
        for contents in ('{"versao":1,"versao":2}', '{"x":NaN}', '{', '\xff'):
            with self.subTest(contents=contents):
                self.path.write_bytes(contents.encode('latin-1'))
                with self.assertRaises(ValueError):
                    restore_backup(self.target, self.path)
                self.assertEqual(before, self.snapshot(self.target))

    def test_database_failure_rolls_back_all_restore_fields(self):
        export_backup(self.source, self.path, True)
        with self.target.db() as db:
            db.execute("CREATE TRIGGER fail_chat BEFORE INSERT ON chat_turns BEGIN SELECT RAISE(ABORT, 'falha de prova'); END")
        before = self.snapshot(self.target)
        with self.assertRaises(sqlite3.IntegrityError):
            restore_backup(self.target, self.path)
        self.assertEqual(before, self.snapshot(self.target))

    def test_active_job_and_closing_block_restore(self):
        export_backup(self.source, self.path, True)
        before = self.snapshot(self.target)
        for state in ('executando', 'baixando'):
            self.target.job = {'estado': state}
            with self.assertRaises(ValueError):
                restore_backup(self.target, self.path)
            self.assertEqual(before, self.snapshot(self.target))
        self.target.job = {'estado': 'parado'}
        self.target.closing.set()
        with self.assertRaises(ValueError):
            restore_backup(self.target, self.path)

    def test_export_failure_keeps_old_file_and_cleans_temporary(self):
        self.path.write_text('backup anterior', encoding='utf-8')
        with patch('brasil.backup.os.replace', side_effect=OSError('disco de prova')):
            with self.assertRaises(OSError):
                export_backup(self.source, self.path, True)
        self.assertEqual(self.path.read_text(encoding='utf-8'), 'backup anterior')
        self.assertEqual(list(self.folder.glob('.ultimo-livro-backup-*')), [])

    def test_export_does_not_truncate_database_or_follow_output_symlink(self):
        database = self.source.folder / 'dados.sqlite'
        before = self.snapshot(self.source)
        for path in (database, Path(str(database) + '-wal')):
            with self.assertRaises(ValueError):
                export_backup(self.source, path)
        link = self.folder / 'link.json'
        try:
            link.symlink_to(database)
        except (OSError, NotImplementedError):
            pass  # Windows pode não permitir criar links neste ambiente.
        else:
            with self.assertRaises(ValueError):
                export_backup(self.source, link)
        self.assertEqual(before, self.snapshot(self.source))

    def test_export_rejects_hardlink_to_database(self):
        try:
            os.link(self.source.folder / 'dados.sqlite', self.path)
        except (OSError, NotImplementedError):
            self.skipTest('Sistema de arquivos sem suporte a hard links.')
        with self.assertRaises(ValueError):
            export_backup(self.source, self.path)

    def test_source_references_are_text_and_never_imported_as_paths(self):
        export_backup(self.source, self.path, True)
        body = copy.deepcopy(self.read())
        body['conversas'][0]['fontes'][0]['caminho'] = '../../arquivo.zim'
        self.write(body)
        restore_backup(self.target, self.path)
        self.assertEqual(self.target.files(), {})
        self.assertEqual(self.snapshot(self.target)['encyclopedias'], [])


if __name__ == '__main__':
    unittest.main()
