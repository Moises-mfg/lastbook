"""Exportação local do recorte que está visível no mapa."""
import base64
import binascii
from html import escape
from pathlib import Path

from .backup import _destination
from .preparo_local import _escrever_atomico


def exportar_recorte(store, body, path):
    image = body.get('imagem')
    if not isinstance(image, str) or not 20 <= len(image) <= 1_950_000:
        raise ValueError('Recorte inválido ou muito grande.')
    try:
        data = base64.b64decode(image, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise ValueError('Recorte inválido.') from exc
    if not (data.startswith(b'\xff\xd8\xff') and data.endswith(b'\xff\xd9')):
        raise ValueError('Formato de imagem inválido.')
    partial = body.get('cobertura_parcial', False)
    if type(partial) is not bool:
        raise ValueError('Informação de cobertura inválida.')
    sources = body.get('fontes', [])
    if not isinstance(sources, list) or len(sources) > 4 or any(
            not isinstance(source, str) or len(source) > 1400 for source in sources):
        raise ValueError('Fonte do recorte inválida.')
    destination = _destination(store, path)
    if destination.suffix.lower() not in ('.html', '.htm') or (store.folder / 'preparo-fotos').resolve() in destination.parents:
        raise ValueError('Escolha um arquivo HTML fora da pasta de fotos.')
    coverage = '<p><strong>Cobertura parcial.</strong> Há trechos sem dados locais neste recorte.</p>' if partial else ''
    references = ''.join(f'<li>{escape(source)}</li>' for source in sources)
    document = (
        '<!doctype html><html lang="pt-BR"><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; img-src data:; style-src \'unsafe-inline\'">'
        '<title>Recorte do mapa — O Último Livro</title><style>body{font:16px sans-serif;max-width:960px;'
        'margin:1rem auto;padding:1rem;color:#111}img{width:100%;height:auto}li{overflow-wrap:anywhere}'
        '@media print{body{margin:0;padding:0;font-size:10pt}h1{font-size:16pt}img{max-height:65vh;object-fit:contain}}</style>'
        '<body><h1>Recorte do mapa offline</h1>'
        '<p>O recorte representa uma cópia local do mapa. Confirme as condições das vias e os locais em funcionamento.</p>'
        f'{coverage}<img alt="Recorte do mapa exibido" src="data:image/jpeg;base64,{image}">'
        f'<h2>Fontes</h2><ul>{references}</ul></body></html>'
    )
    _escrever_atomico(destination, document.encode('utf-8'), lambda: _destination(store, destination))
    return {'mensagem': 'Recorte salvo. Abra o arquivo HTML para imprimir ou levar no celular.'}
