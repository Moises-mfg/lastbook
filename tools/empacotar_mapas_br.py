#!/usr/bin/env python3
"""Agrupa recortes em arquivos com acesso HTTP Range, sem milhares de uploads.

Cada mapa é um SQLite independente e tem seu próprio SHA-256, offset e tamanho.
O manifesto versionado permite baixar apenas a cidade/UF escolhida. O arquivo de
transporte é limitado a menos de 2 GiB para ser distribuído em GitHub Releases.
"""
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'derived/mapas-br'
LIMIT=1800*1024*1024
VERSION='mapas-br-2026-11-16'
BASE_URL=f'https://github.com/Moises-mfg/o-ultimo-livro/releases/download/{VERSION}/'


def pack(entries,output,limit=LIMIT):
    if limit<=4096:raise ValueError('Limite de volume inválido.')
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    packages={};volumes=[];current=None;number=0
    try:
        for index,item in enumerate(entries):
            if index%500==0:print(f'Empacotando mapa {index+1}/{len(entries)}',flush=True)
            source=Path(item['path']);size=source.stat().st_size
            parts=[];whole=hashlib.sha256();remaining=size
            with source.open('rb') as file:
                while remaining:
                    if current is None or current.tell()>=limit:
                        if current:current.close()
                        number+=1;path=output/f'brasil-mapas-{number:02d}.ulpack'
                        if path.exists():raise ValueError('Pacote já existe. Escolha um diretório novo para preservar os publicados.')
                        volumes.append(path);current=path.open('wb');current.write(b'ULMAPACK1'+b'\0'*(4096-9))
                    # Pequenos mapas ficam inteiros em um volume; só dividir os
                    # maiores que um volume, para preservar o download mínimo.
                    if remaining<=limit-4096 and current.tell()+remaining>limit:
                        current.close();current=None;continue
                    offset=current.tell();count=min(remaining,limit-offset);digest=hashlib.sha256();left=count
                    while left:
                        data=file.read(min(left,1024*1024))
                        if not data:raise ValueError('Fonte truncada: '+source.name)
                        current.write(data);digest.update(data);whole.update(data);left-=len(data)
                    parts.append({'size':count,'sha256':digest.hexdigest(),'url':BASE_URL+volumes[-1].name,
                        'offset':offset,'container_file':volumes[-1].name})
                    remaining-=count
            fields={k:v for k,v in item.items() if k!='path'}
            common={**fields,'size':size,'sha256':whole.hexdigest(),'source':'OpenStreetMap/Geofabrik e IBGE',
                'edition':'2026-11-16','license':'ODbL-1.0','license_url':'https://opendatacommons.org/licenses/odbl/1-0/','attribution':'© contribuidores do OpenStreetMap; Geofabrik; IBGE 2025.'}
            packages[item['id']]={**common,**parts[0]} if len(parts)==1 else {**common,'parts':parts}
    finally:
        if current:current.close()
    containers={}
    for path in volumes:
        print('Verificando volume',path.name,flush=True)
        with path.open('rb') as file:sha=hashlib.file_digest(file,'sha256').hexdigest()
        containers[path.name]={'size':path.stat().st_size,'sha256':sha}
    for item in packages.values():
        for part in item.get('parts',[item]):part['container_size']=containers[part['container_file']]['size']
    manifest={'schema':1,'version':VERSION,'packages':packages,'containers':containers}
    (output/'mapas_catalogo.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    (output/'SHA256SUMS').write_text(''.join(f'{info["sha256"]}  {name}\n' for name,info in containers.items()))
    return manifest


def main():
    entries=json.loads((OUT/'recortes.json').read_text())
    result=pack(entries,OUT/'publicacao')
    (ROOT/'brasil/mapas_catalogo.json').write_text(json.dumps(result,ensure_ascii=False,separators=(',',':'))+'\n')
    print('Mapas:',len(result['packages']),'arquivos de transporte:',len(result['containers']))

if __name__=='__main__':main()
