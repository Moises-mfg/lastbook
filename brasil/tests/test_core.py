import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from brasil.core import Store, recommend, validate_choices, GiB

class CoreTests(unittest.TestCase):
    def test_hardware_conservative_without_gpu_or_known_ram(self):
        self.assertEqual(recommend(None), 'leve')
        self.assertEqual(recommend(int(7.6*GiB)), 'leve')
        self.assertEqual(recommend(16*GiB), 'moderada')
        self.assertEqual(recommend(32*GiB), 'parruda')

    def test_choices_and_checklist_survive_restart(self):
        with tempfile.TemporaryDirectory() as path:
            first = Store(path)
            config = first.save_choices({'perfil':'personalizada','modelo':'sem-ia','wikis':['pt-mini','es-mini'], 'estados':['AM','SP']})
            first.check({'id':'luz','feito':True})
            second = Store(path)
            self.assertEqual(config, second.choices())
            self.assertTrue(next(x for x in second.checklist() if x['id']=='luz')['feito'])
            second.check({'id':'luz','feito':False})
            self.assertFalse(next(x for x in second.checklist() if x['id']=='luz')['feito'])

    def test_reject_unknown_content_and_malformed_requests(self):
        for body in ({'perfil':'desconhecido'},{'wikis':'pt-mini'}, {'estados':['../SP']},{'modelo':'gemma-26b'}, {'wikis':[{}]}):
            with self.subTest(body=body), self.assertRaises(ValueError):
                validate_choices(body)

    def test_state_never_downloads(self):
        with tempfile.TemporaryDirectory() as path, patch('brasil.core.download.Download', side_effect=AssertionError('network')):
            store = Store(path)
            state = store.state()
            self.assertEqual(len(state['estados']),27)
            self.assertEqual(len(state['perfis']),4)
            self.assertFalse(state['ia']['modelo'])

    def test_checkbox_requires_boolean_and_known_id(self):
        with tempfile.TemporaryDirectory() as path:
            for body in ({'id':'luz','feito':'false'}, {'id':'inexistente','feito':True}):
                with self.assertRaises(ValueError): Store(path).check(body)

    def test_model_choice_never_silently_falls_back(self):
        with tempfile.TemporaryDirectory() as path:
            s=Store(path)
            s.save_choices({'perfil':'personalizada','modelo':'sem-ia'})
            with self.assertRaisesRegex(ValueError,'desativada'):s.ask({'pergunta':'Como começar?'})
            s.save_choices({'perfil':'moderada'})
            self.assertEqual(s.model_spec()['id'], 'qwen3-4b')
            self.assertEqual(s.model_path().name, 'Qwen3-4B-Q4_K_M.gguf')
            self.assertNotEqual(s.model_path().name, 'Qwen3-0.6B-Q8_0.gguf')

    def test_question_validation(self):
        with tempfile.TemporaryDirectory() as path:
            for q in ('', 'x'*1501, [], None):
                with self.assertRaises(ValueError): Store(path).ask({'pergunta':q})

if __name__=='__main__': unittest.main()
