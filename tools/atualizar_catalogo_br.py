#!/usr/bin/env python3
"""Atualiza pins oficiais por ação explícita do mantenedor. Não é executado pelo app."""
import json
from pathlib import Path
import re
import urllib.request
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
NS = {'m': 'urn:ietf:params:xml:ns:metalink'}

def get(url):
    with urllib.request.urlopen(url, timeout=60) as response:
        return response.read()


def main():
    catalog = {}
    for lang, variants in {'pt': ('mini', 'nopic', 'maxi'), 'en': ('mini',), 'es': ('mini',)}.items():
        listing = get('https://download.kiwix.org/zim/wikipedia/').decode()
        for variant in variants:
            matches = sorted(set(re.findall(rf'wikipedia_{lang}_all_{variant}_\d{{4}}-\d{{2}}\.zim', listing)))
            if not matches:
                raise RuntimeError(f'Coleção indisponível: {lang}-{variant}')
            name = matches[-1]
            origin = 'https://download.kiwix.org/zim/wikipedia/' + name
            tree = ET.fromstring(get(origin + '.meta4'))
            file = tree.find('m:file', NS)
            sha = next(h.text for h in file.findall('m:hash', NS) if h.get('type') == 'sha-256')
            # Espelho HTTPS listado pelo Kiwix e conferido no metalink;
            # nenhuma escolha dinâmica de domínio pelo aplicativo.
            direct = 'https://ftpmirror.your.org/pub/kiwix/zim/wikipedia/' + name
            mirrors = [node.text for node in file.findall('m:url', NS)]
            if direct not in mirrors:
                raise RuntimeError('Espelho não confirmado nos metadados oficiais.')
            catalog[f'{lang}-{variant}'] = {'id': f'{lang}-{variant}', 'kind': 'zim', 'file': name,
                'size': int(file.find('m:size', NS).text), 'sha256': sha, 'url': direct,
                'metadata_url': origin + '.meta4', 'language': lang, 'variant': variant,
                'edition': re.search(r'(\d{4}-\d{2})\.zim$', name).group(1),
                'license': 'CC BY-SA; consulte os créditos e avisos da edição Wikipedia/Kiwix.',
                'source': 'Wikipedia / Wikimedia; arquivo produzido pelo Kiwix'}
            print(f'{lang}-{variant}: {catalog[f"{lang}-{variant}"]["size"]} bytes')
    for ident, repo, filename, ram, available, context in (
        ('qwen3-0.6b', 'Qwen3-0.6B-GGUF', 'Qwen3-0.6B-Q8_0.gguf', 8, 3, 2048),
        ('qwen3-4b', 'Qwen3-4B-GGUF', 'Qwen3-4B-Q4_K_M.gguf', 16, 6, 4096),
        ('qwen3-14b', 'Qwen3-14B-GGUF', 'Qwen3-14B-Q4_K_M.gguf', 32, 16, 8192),
    ):
        data = json.loads(get('https://huggingface.co/api/models/Qwen/' + repo + '?blobs=true'))
        f = next(x for x in data['siblings'] if x['rfilename'] == filename)
        catalog[ident] = {'id': ident, 'kind': 'model', 'file': filename, 'size': f['size'],
            'sha256': f['lfs']['sha256'], 'revision': data['sha'],
            'url': f'https://huggingface.co/Qwen/{repo}/resolve/{data["sha"]}/{filename}',
            'license': 'Apache-2.0', 'source': 'Qwen oficial', 'ram_gib': ram,
            'available_gib': available, 'context': context}
        print(f'{ident}: {f["size"]} bytes')
    (ROOT / 'brasil' / 'pacotes.json').write_text(json.dumps({'schema': 1, 'packages': catalog}, ensure_ascii=False, indent=2) + '\n')

if __name__ == '__main__':
    main()
