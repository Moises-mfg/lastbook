"""Planejamento, ativação e consulta de recortes offline com dados descartáveis."""
import hashlib
from pathlib import Path
import shutil
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from brasil import mapa_vetor,pacotes
from brasil.core import Store
from brasil.tests.test_pacotes import wait

class Maps(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.source=self.root/'sample.ulmap';db=sqlite3.connect(self.source);mapa_vetor.create(db)
        mapa_vetor.add_feature(db,1,'poi','hospital','Hospital de Teste',12,[[(-48,-16)]])
        mapa_vetor.finish(db,{'name':'Mapa de teste','bounds':[-48.1,-16.1,-47.9,-15.9],'attribution':'Teste'});db.close()
        content=self.source.read_bytes();self.items={}
        for ident,scope,extras in [('map-br-base','base',{}),('map-br-full','brasil',{}),('map-uf-SP','estado',{'uf':'SP'}),('map-city-3509502','municipio',{'uf':'SP','code':'3509502'})]:
            self.items[ident]={'id':ident,'kind':'map','scope':scope,'file':ident+'.ulmap','name':'Campinas / SP' if scope=='municipio' else ident,'size':len(content),'sha256':hashlib.sha256(content).hexdigest(),**extras}
        self.patch=patch('brasil.pacotes.MAP_PACKAGES',self.items);self.patch.start();self.store=Store(self.root/'data')
    def tearDown(self):self.patch.stop();self.tmp.cleanup()

    def test_profiles_choose_only_requested_regions_and_real_bytes(self):
        for profile,body,expected in [
            ('leve',{'municipios':['3509502']},['map-br-base','map-city-3509502']),
            ('moderada',{'estados':['SP']},['map-br-base','map-uf-SP']),
            ('parruda',{},['map-br-full']),
            ('personalizada',{'modelo':'sem-ia','wikis':[],'mapa':'municipio','municipios':['3509502']},['map-br-base','map-city-3509502'])]:
            self.store.save_choices({'perfil':profile,**body});plan=self.store.install_plan()
            maps=[p['id'] for p in plan['pacotes'] if p['kind']=='map']
            self.assertEqual(maps,expected);self.assertEqual(plan['download_bytes'],sum(p['size'] for p in plan['pacotes']))
            visible=[k for k,v in self.store.package_state().items() if v['kind']=='map'];self.assertEqual(set(visible),set(expected))
        for invalid in ({'municipios':['9999999']},{'municipios':'3509502'}):
            with self.assertRaises(ValueError):self.store.save_choices(invalid)

    def test_search_catalog_activation_and_persistence_never_need_network(self):
        result=self.store.map_catalog_search({'busca':'CAMP','uf':'SP','selecionados':['3509502']})
        self.assertEqual(result['total'],1);self.assertEqual(result['resultados'][0]['code'],'3509502')
        def obtain(item,target,*args):
            target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(self.source,target);return target
        with patch('brasil.pacotes.obtain',obtain):
            self.store.install_packages(['map-city-3509502']);self.assertEqual(wait(self.store)['estado'],'concluido')
        reloaded=Store(self.root/'data');self.assertEqual(reloaded.active_map_id(),'map-city-3509502')
        self.assertEqual(reloaded.search_map({'busca':'Hospital'})[0]['nome'],'Hospital de Teste')
        self.assertEqual(reloaded.map_metadata()['formato'],'ulmap')
        with self.assertRaises(ValueError):reloaded.select_map({'id':'inexistente'})
        with self.assertRaises(ValueError):reloaded.map_catalog_search({'selecionados':'incorreto'})

if __name__=='__main__':unittest.main()
