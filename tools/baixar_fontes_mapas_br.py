#!/usr/bin/env python3
"""Obtém fontes públicas por ação explícita do mantenedor, nunca pelo aplicativo."""
import hashlib
import json
from pathlib import Path
import time
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'derived/mapas-br/fontes'
OUT.mkdir(parents=True,exist_ok=True)
PBF='https://download.geofabrik.de/south-america/brazil-261116.osm.pbf'


def small(url, filename):
    dest=OUT/filename
    if not dest.exists():
        with urllib.request.urlopen(url,timeout=120) as response:
            if not response.url.startswith('https:'):raise ValueError('Origem sem HTTPS')
            data=response.read()
        part=dest.with_suffix(dest.suffix+'.part');part.write_bytes(data);part.replace(dest)
    data=dest.read_bytes()
    return {'url':url,'file':filename,'size':len(data),'sha256':hashlib.sha256(data).hexdigest()}


def main():
    provenance={}
    print('Baixando recortes e nomes municipais do IBGE',flush=True)
    provenance['municipios2025']=small('https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/malhas_municipais/municipio_2025/Brasil/BR_Municipios_2025.zip','BR_Municipios_2025.zip')
    provenance['municipios']=small('https://servicodados.ibge.gov.br/api/v3/malhas/paises/BR?formato=application/vnd.geo+json&qualidade=minima&intrarregiao=municipio','municipios.geojson')
    provenance['nomes']=small('https://servicodados.ibge.gov.br/api/v1/localidades/municipios','municipios-nomes.json')
    provenance['estados']=small('https://servicodados.ibge.gov.br/api/v3/malhas/paises/BR?formato=application/vnd.geo+json&qualidade=minima&intrarregiao=UF','estados.geojson')
    print('Fontes IBGE salvas. Baixando extrato OpenStreetMap/Geofabrik',flush=True)
    with urllib.request.urlopen(PBF+'.md5',timeout=30) as r:expected=r.read().decode().split()[0]
    dest=OUT/'brazil-261116.osm.pbf';part=Path(str(dest)+'.part')
    if not dest.exists():
        start=part.stat().st_size if part.exists() else 0
        request=urllib.request.Request(PBF,headers={'Range':f'bytes={start}-'} if start else {})
        with urllib.request.urlopen(request,timeout=60) as response:
            if not response.url.startswith('https:'):raise ValueError('Origem sem HTTPS')
            if start and (response.status!=206 or not response.headers.get('Content-Range','').startswith(f'bytes {start}-')):start=0
            total=int(response.headers['Content-Length'])+start
            last=time.monotonic()
            with part.open('ab' if start else 'wb') as file:
                done=start
                while data:=response.read(1024*1024):
                    file.write(data);done+=len(data)
                    if time.monotonic()-last>10:print(f'PBF {done}/{total} bytes ({100*done/total:.1f}%)',flush=True);last=time.monotonic()
            if done!=total:raise ValueError('Fonte incompleta')
        part.replace(dest)
    md5=hashlib.md5(usedforsecurity=False);sha=hashlib.sha256()
    with dest.open('rb') as file:
        while chunk:=file.read(8*1024*1024):md5.update(chunk);sha.update(chunk)
    if md5.hexdigest()!=expected:raise ValueError('Fonte não corresponde ao MD5 publicado por HTTPS pelo Geofabrik')
    provenance['osm']={'url':PBF,'file':dest.name,'size':dest.stat().st_size,'sha256':sha.hexdigest(),'provider_md5':expected,'license':'ODbL-1.0','attribution':'© contribuidores do OpenStreetMap; extrato Geofabrik'}
    (OUT/'proveniencia.json').write_text(json.dumps(provenance,ensure_ascii=False,indent=2)+'\n')
    print('Fontes conferidas e proveniência salva.',flush=True)

if __name__=='__main__':main()
