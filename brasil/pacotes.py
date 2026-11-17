"""Catálogo fixado na versão do aplicativo e verificação antes de ativar conteúdo."""
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

from engine.setup import download

CATALOG_PATH = Path(__file__).with_name('pacotes.json')


def load_catalog():
    data = json.loads(CATALOG_PATH.read_text(encoding='utf-8'))
    if data.get('schema') != 1:
        raise ValueError('Versão de catálogo não suportada.')
    packages = data['packages']
    for ident, item in packages.items():
        if ident != item['id'] or item['kind'] not in ('zim', 'model', 'map'):
            raise ValueError('Tipo de pacote inválido.')
        if Path(item['file']).name != item['file'] or not re.fullmatch(r'[A-Za-z0-9_.-]+', item['file']):
            raise ValueError('Nome de arquivo inválido.')
        if type(item['size']) is not int or item['size'] <= 0 or not re.fullmatch('[0-9a-f]{64}', item['sha256']):
            raise ValueError('Verificação de pacote inválida.')
        uri = urlsplit(item['url'])
        if not download.url_allowed(item['url']) or uri.port not in (None, 443):
            raise ValueError('Origem de pacote não autorizada.')
    return packages


MAP_PACKAGES = None


def maps_catalog():
    global MAP_PACKAGES
    if MAP_PACKAGES is None:
        path=Path(__file__).with_name('mapas_catalogo.json')
        if not path.exists():return {}
        data=json.loads(path.read_text(encoding='utf-8'))
        if data.get('schema')!=1:raise ValueError('Catálogo de mapas incompatível.')
        items=data['packages']
        for ident,p in items.items():
            if ident!=p['id'] or p['kind']!='map' or not re.fullmatch(r'[A-Za-z0-9_.-]+',p['file']):raise ValueError('Mapa inválido.')
            if not re.fullmatch('[0-9a-f]{64}',p['sha256']) or type(p['size']) is not int or p['size']<=0:raise ValueError('Mapa sem verificação.')
            parts=p.get('parts',[p])
            if not isinstance(parts,list) or not parts or len(parts)>100:raise ValueError('Partes de mapa inválidas.')
            if sum(part['size'] for part in parts)!=p['size']:raise ValueError('Tamanho das partes inválido.')
            for part in parts:
                if type(part['size']) is not int or part['size']<=0 or not re.fullmatch('[0-9a-f]{64}',part['sha256']):raise ValueError('Parte sem verificação.')
                if type(part['offset']) is not int or part['offset']<0 or type(part['container_size']) is not int or part['container_size']<part['offset']+part['size']:raise ValueError('Recorte de mapa inválido.')
                if not download.url_allowed(part['url']) or urlsplit(part['url']).port not in (None,443):raise ValueError('Origem de mapa não autorizada.')
        MAP_PACKAGES=items
    return MAP_PACKAGES


def all_catalog():
    return {**catalog(),**maps_catalog()}


PACKAGES = None


def catalog():
    global PACKAGES
    if PACKAGES is None:
        PACKAGES = load_catalog()
    return PACKAGES


def verified_file(path, item, control=None, progress=None):
    path = Path(path)
    if not path.is_file() or path.stat().st_size != item['size']:
        return False
    digest = hashlib.sha256()
    done = 0
    with path.open('rb') as file:
        while chunk := file.read(4 * 1024 * 1024):
            if control:
                control.check()
            digest.update(chunk)
            done += len(chunk)
            if progress:
                progress(done, item['size'], 'verifying')
    return digest.hexdigest() == item['sha256']


def obtain(item, target, control, progress):
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    # Download.run trusts an existing destination by size. Imported files or a
    # previous interrupted activation must also pass the hash, not just size.
    if target.exists():
        if verified_file(target, item, control, progress):
            return target
        target.unlink()
    if 'parts' in item:
        return obtain_parts(item,target,control,progress)
    extra = {'offset':item['offset'], 'container_size':item['container_size']} if 'offset' in item else {}
    download.Download(item['url'], target, item['size'], item['sha256'], control, progress, **extra).run()
    # The downloader hashes bytes while writing and atomically renames only
    # when the pinned size and digest match.
    return target


def partial_bytes(path,item):
    path=Path(path)
    if 'parts' not in item:
        partial=Path(str(path)+'.part')
        return min(item['size'],partial.stat().st_size) if partial.is_file() else 0
    total=0
    for i,part in enumerate(item['parts']):
        segment=Path(str(path)+f'.seg-{i:03d}')
        partial=Path(str(segment)+'.part')
        total+=min(part['size'],segment.stat().st_size if segment.is_file() else partial.stat().st_size if partial.is_file() else 0)
    return total


def obtain_parts(item,target,control,progress):
    # Cada parte usa a mesma verificação, retomada e limites do download simples.
    segments=[];completed=0
    for i,part in enumerate(item['parts']):
        segment=Path(str(target)+f'.seg-{i:03d}')
        def report(done,total,phase,base=completed):progress(base+done,item['size'],phase)
        obtain(part,segment,control,report)
        segments.append(segment);completed+=part['size']
    partial=Path(str(target)+'.part');digest=hashlib.sha256();done=0
    try:
        with partial.open('wb') as out:
            for segment in segments:
                with segment.open('rb') as file:
                    while chunk:=file.read(4*1024*1024):
                        control.check();out.write(chunk);digest.update(chunk);done+=len(chunk)
                        progress(done,item['size'],'verifying')
        if done!=item['size'] or digest.hexdigest()!=item['sha256']:raise ValueError('Verificação do mapa completo falhou.')
        partial.replace(target)
    finally:
        if partial.exists():partial.unlink()
    for segment in segments:segment.unlink()
    return target
