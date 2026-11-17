import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from brasil import plataforma

class Platform(unittest.TestCase):
    def test_mac_available_counts_reclaimable_pages(self):
        text='Mach Virtual Memory Statistics: (page size of 16384 bytes)\nPages free: 100.\nPages active: 900.\nPages inactive: 200.\nPages speculative: 50.\n'
        with patch.object(sys,'platform','darwin'),patch('subprocess.check_output',return_value=text):self.assertEqual(plataforma.available_memory(),350*16384)
        with patch.object(sys,'platform','darwin'),patch('subprocess.check_output',side_effect=OSError):self.assertIsNone(plataforma.available_memory())
    def test_data_directory_is_private_to_each_platform_and_override_is_explicit(self):
        with patch.dict(os.environ,{'LOCALAPPDATA':'C:/Dados','XDG_DATA_HOME':'/tmp/xdg'},clear=True):
            with patch.object(sys,'platform','win32'):self.assertEqual(plataforma.data_folder(),Path('C:/Dados/UltimoLivro'))
            with patch.object(sys,'platform','darwin'):self.assertEqual(plataforma.data_folder(),Path.home()/'Library/Application Support/UltimoLivro')
            with patch.object(sys,'platform','linux'):self.assertEqual(plataforma.data_folder(),Path('/tmp/xdg/ultimo-livro'))
            with patch.dict(os.environ,{'ULTIMO_LIVRO_DATA':'/tmp/dados escolhidos'}):self.assertEqual(plataforma.data_folder(),Path('/tmp/dados escolhidos'))
    def test_actual_system_memory_is_known(self):self.assertGreater(plataforma.available_memory() or 0,0)
