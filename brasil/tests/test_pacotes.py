import hashlib
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

from app.tests.test_setup import Files, start_server
from brasil.core import Store
from brasil import pacotes
from engine.setup import download


def wait(store):
    deadline=time.monotonic()+15
    while time.monotonic()<deadline:
        with store.lock: job=dict(store.job)
        if job['estado'] not in ('executando','baixando'):
            return job
        time.sleep(.01)
    raise AssertionError('A operação local não terminou')


class Packages(unittest.TestCase):
    def test_manifest_is_pinned_and_real_sizes_drive_all_profiles(self):
        items=pacotes.load_catalog()
        self.assertEqual(items['pt-mini']['size'],1703536110)
        for profile in ('leve','moderada','parruda'):
            with self.subTest(profile=profile),tempfile.TemporaryDirectory() as tmp:
                s=Store(tmp);s.save_choices({'perfil':profile})
                plan=s.install_plan()
                self.assertEqual(sum(p['kind']!='map' for p in plan['pacotes']),2)
                self.assertEqual(plan['download_bytes'],sum(p['size'] for p in plan['pacotes']))
                self.assertEqual(plan['necessario_bytes'],plan['download_bytes']+sum(p['size'] for p in plan['pacotes'] if 'parts' in p)+2**30)
                self.assertIn('Mapas regionais' if pacotes.maps_catalog() else 'Mapas ainda',plan['aviso_mapas'])

    def test_existing_same_size_file_must_pass_digest(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'model.gguf';p.write_bytes(b'fake')
            item={'size':4,'sha256':hashlib.sha256(b'real').hexdigest(),'url':'https://huggingface.co/model'}
            class Rebuild:
                def __init__(self,*args):pass
                def run(self):p.write_bytes(b'real')
            with patch('brasil.pacotes.download.Download',Rebuild):
                pacotes.obtain(item,p,download.Control(),lambda *x:None)
            self.assertEqual(p.read_bytes(),b'real')

    def test_site_plan_import_validates_schema_without_starting_download(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'plan.json';p.write_text(json.dumps({'versao':1,'perfil':'personalizada','modelo':'sem-ia','wikis':['pt-mini','es-mini'],'estados':['SP'],'mapa':'estado'}))
            s=Store(Path(tmp)/'data')
            with patch('brasil.core.download.Download',side_effect=AssertionError('network')):
                s.import_plan(p)
            self.assertEqual(s.choices()['estados'],['SP'])
            self.assertEqual(s.choices()['wikis'],['es-mini','pt-mini'])


class RealDownloads(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.files=Files();self.server,self.ctx,self.base=start_server(self.root,self.files)
        self.original=download.Download
        def local(url,*args,**kwargs):
            return self.original(url,*args,allowed={'127.0.0.1'},context=self.ctx,**kwargs)
        self.patch=patch('brasil.pacotes.download.Download',local);self.patch.start()

    def tearDown(self):
        self.patch.stop();self.server.shutdown();self.server.server_close();self.tmp.cleanup()

    def item(self, content):
        self.files.data['model.gguf']=content
        return {'id':'qwen3-0.6b','kind':'model','file':'model.gguf','size':len(content),'sha256':hashlib.sha256(content).hexdigest(),'url':self.base+'/model.gguf'}

    def test_pause_survives_restart_and_range_resume_verifies_final_bytes(self):
        content=b'Wikipedia local\n'*(400000)
        item=self.item(content);self.files.pace=.002
        with patch('brasil.pacotes.PACKAGES',{'qwen3-0.6b':item}):
            s=Store(self.root/'data')
            original=pacotes.obtain
            def pause_after_first_chunk(item,target,control,progress):
                def on_progress(done,total,phase):
                    progress(done,total,phase)
                    if done and phase=='downloading':control.stop('paused')
                return original(item,target,control,on_progress)
            with patch('brasil.pacotes.obtain',pause_after_first_chunk):
                s.install_packages(['qwen3-0.6b']);self.assertEqual(wait(s)['estado'],'pausado')
            target=s.package_path(item)
            self.assertFalse(target.exists());self.assertGreater(Path(str(target)+'.part').stat().st_size,0)
            restarted=Store(self.root/'data');self.assertEqual(restarted.job['estado'],'pausado')
            restarted.resume_install({});self.assertEqual(wait(restarted)['estado'],'concluido')
            self.assertEqual(target.read_bytes(),content)
            self.assertTrue(any(rng is not None for _,rng,_ in self.files.log))
            self.assertTrue(restarted.package_state()['qwen3-0.6b']['instalado'])

    def test_bad_checksum_never_activates_package(self):
        item=self.item(b'expected content'*1000);self.files.corrupt['model.gguf']=1
        with patch('brasil.pacotes.PACKAGES',{'qwen3-0.6b':item}):
            s=Store(self.root/'data');s.install_packages(['qwen3-0.6b'])
            self.assertEqual(wait(s)['estado'],'erro')
            self.assertFalse(s.package_path(item).exists())
            with s.db() as db:
                self.assertIsNone(db.execute("SELECT value FROM settings WHERE key='verified:qwen3-0.6b'").fetchone())

if __name__=='__main__':unittest.main()
