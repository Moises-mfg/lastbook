import tempfile
import unittest
from unittest.mock import patch
from brasil.core import Store
from brasil.fontes import RECURSOS,resource_url
from brasil.guias_pdf import catalog
from brasil.situacoes import GUIDE_SITE_ID, GUIDE_SITE_URL

class References(unittest.TestCase):
    def test_directory_is_available_without_network_and_external_targets_are_fixed(self):
        with tempfile.TemporaryDirectory() as folder,patch('socket.socket',side_effect=AssertionError('rede')):
            state=Store(folder).state()
            self.assertEqual(len(state['recursos']),11)
            for resource in RECURSOS:self.assertEqual(resource_url(resource['id']),resource['url'])
            for invalid in ('https://example.com','javascript:alert(1)','../fontes',None,{}):
                with self.subTest(value=invalid),self.assertRaises(ValueError):resource_url(invalid)

    def test_situacoes_abrem_referencias_cadastradas_e_paginas_locais(self):
        self.assertEqual(resource_url(GUIDE_SITE_ID), GUIDE_SITE_URL)
        with tempfile.TemporaryDirectory() as folder, patch('socket.socket', side_effect=AssertionError('rede')):
            guides = {guide['id']: guide for guide in catalog()}
            self.assertEqual(len(guides), 3)
            for guide in guides.values():
                self.assertEqual(len(guide['paginas']), len(guide['texto_paginas']))
                self.assertTrue(all('\n\n' in page for page in guide['texto_paginas']))
            situations = Store(folder).state()['situacoes']
            self.assertEqual({item['id'] for item in situations}, {'apagao', 'enchente', 'agua', 'calor', 'alimentos'})
            for situation in situations:
                for source in situation['fontes']:
                    self.assertTrue(resource_url(source['id']).startswith('https://'))
                for reference in situation['leituras']:
                    self.assertIn(reference['pagina'], range(1, len(guides[reference['id']]['paginas']) + 1))
