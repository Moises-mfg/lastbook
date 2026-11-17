import tempfile
import unittest
from unittest.mock import patch
from brasil.core import Store
from brasil.fontes import RECURSOS,resource_url

class References(unittest.TestCase):
    def test_directory_is_available_without_network_and_external_targets_are_fixed(self):
        with tempfile.TemporaryDirectory() as folder,patch('socket.socket',side_effect=AssertionError('rede')):
            state=Store(folder).state()
            self.assertEqual(len(state['recursos']),11)
            for resource in RECURSOS:self.assertEqual(resource_url(resource['id']),resource['url'])
            for invalid in ('https://example.com','javascript:alert(1)','../fontes',None,{}):
                with self.subTest(value=invalid),self.assertRaises(ValueError):resource_url(invalid)
