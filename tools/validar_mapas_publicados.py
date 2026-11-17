#!/usr/bin/env python3
"""Teste explícito de mantenedor: downloads reais de três mapas da release."""
import json
from pathlib import Path
import sys
import time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from brasil.core import Store
from brasil import pacotes
from engine.setup.download import Control,Stopped


def main():
    root=ROOT/'derived/mapas-br/validacao-remota';store=Store(root)
    store.save_choices({'perfil':'personalizada','modelo':'sem-ia','wikis':[],'mapa':'municipio','municipios':['3509502','5101837']})
    item=pacotes.maps_catalog()['map-city-3509502'];control=Control()
    def pause(done,total,phase):
        if done>=1024*1024 and phase=='downloading':control.stop('paused')
    try:pacotes.obtain(item,store.package_path(item),control,pause)
    except Stopped:print('Download real de Campinas pausado; bytes preservados:',pacotes.partial_bytes(store.package_path(item),item),flush=True)
    store.install_selected({});last=None;deadline=time.monotonic()+600
    while time.monotonic()<deadline:
        with store.lock:job=dict(store.job)
        marker=(job.get('pacote'),job.get('estado'),job.get('fase'))
        if marker!=last:print(json.dumps(job,ensure_ascii=False),flush=True);last=marker
        if job['estado'] not in ('executando','baixando'):break
        time.sleep(.25)
    if job['estado']!='concluido':raise RuntimeError(job)
    store.select_map({'id':'map-city-3509502'})
    if not any(r['nome']=='Campinas' for r in store.search_map({'busca':'Campinas'})):raise ValueError('Busca local não encontrou Campinas.')
    if len(store.installed_maps())!=3:raise ValueError('Mapas não ativados.')
    result={'mapas':store.installed_maps(),'metadados':store.map_metadata(),'consulta':store.search_map({'busca':'Campinas'})[:2],'retomada_e_sha256':'aprovados'}
    (root/'resultado.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print('Downloads reais de visão geral, Campinas e Boa Esperança do Norte: hashes, ativação e busca aprovados.',flush=True)

if __name__=='__main__':main()
