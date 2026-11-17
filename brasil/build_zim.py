#!/usr/bin/env python3
"""Empacota wheels oficiais e fixados para os Python de Ubuntu 24.04–26.04.

Executado apenas pelo mantenedor/CI. Nunca é chamado pelo aplicativo.
"""
import hashlib
import json
from pathlib import Path
import shutil
import urllib.request
import zipfile

ROOT=Path(__file__).resolve().parents[1]
VERSION='3.13.1'
WHEELS={
    'cp312':'1f313d5930021efdf1f45ccb4f294a01cfcebcdbba4ae8d1a1aadcea82e8682d',
    'cp313':'03a9ab549d0f14169a64991cab3d26e8923d215af36ae75cc18fb0ae914fa5c0',
    'cp314':'bc29b54e91690de33706d765605d3ca9a63e066ce70175f51bf1169ba63bef70',
}


def main():
    with urllib.request.urlopen(f'https://pypi.org/pypi/libzim/{VERSION}/json',timeout=60) as response:data=json.load(response)
    cache=ROOT/'derived/brasil-wheels';cache.mkdir(parents=True,exist_ok=True)
    for abi,digest in WHEELS.items():
        name=f'libzim-{VERSION}-{abi}-{abi}-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl'
        record=next(r for r in data['urls'] if r['filename']==name)
        if record['digests']['sha256']!=digest or not record['url'].startswith('https://files.pythonhosted.org/'):raise ValueError('Wheel diferente do fixado.')
        path=cache/name
        if not path.exists():
            partial=Path(str(path)+'.part')
            with urllib.request.urlopen(record['url'],timeout=120) as response,partial.open('wb') as out:shutil.copyfileobj(response,out)
            partial.replace(path)
        with path.open('rb') as file:
            if hashlib.file_digest(file,'sha256').hexdigest()!=digest:raise ValueError('Wheel com checksum incorreto: '+name)
        target=ROOT/'brasil/vendor'/abi;target.mkdir(parents=True,exist_ok=True)
        with zipfile.ZipFile(path) as archive:
            for entry in archive.infolist():
                p=Path(entry.filename)
                if p.is_absolute() or '..' in p.parts:raise ValueError('Caminho de wheel inválido.')
            archive.extractall(target)
        print(abi,'leitor ZIM verificado e empacotado.',flush=True)

if __name__=='__main__':main()
