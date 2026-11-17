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
        if ident != item['id'] or item['kind'] not in ('zim', 'model'):
            raise ValueError('Tipo de pacote inválido.')
        if Path(item['file']).name != item['file'] or not re.fullmatch(r'[A-Za-z0-9_.-]+', item['file']):
            raise ValueError('Nome de arquivo inválido.')
        if type(item['size']) is not int or item['size'] <= 0 or not re.fullmatch('[0-9a-f]{64}', item['sha256']):
            raise ValueError('Verificação de pacote inválida.')
        uri = urlsplit(item['url'])
        if not download.url_allowed(item['url']) or uri.port not in (None, 443):
            raise ValueError('Origem de pacote não autorizada.')
    return packages


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
    download.Download(item['url'], target, item['size'], item['sha256'], control, progress).run()
    # The downloader hashes bytes while writing and atomically renames only
    # when the pinned size and digest match.
    return target
