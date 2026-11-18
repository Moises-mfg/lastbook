"""Busca unificada em conteúdo local; não consulta catálogos remotos nem a IA."""
import sqlite3

from . import guias_pdf, mapa_vetor
from .arquivos import read_zim
from .catalogo import GUIAS
from .guias_pdf_indice import PDF_TEXT
from .mapas import fold


LIMIT = 20
MAX_QUERY = 160


def search(store, body):
    """Retorna grupos limitados com referências aceitas pelos leitores locais.

    PDF inclui a primeira página correspondente (numeração iniciada em 1).
    Mapas incluem mapa_id para selecionar o arquivo antes de centralizar lon/lat.
    Falhas de arquivos individuais ficam em indisponiveis, sem ocultar os demais.
    MBTiles raster não têm índice de lugares e ficam fora desta consulta.
    """
    query = body.get('busca', '') if isinstance(body, dict) else None
    if not isinstance(query, str) or not 1 <= len(query.strip()) <= MAX_QUERY:
        raise ValueError('Escreva uma busca de até 160 caracteres.')
    query = query.strip()
    terms = fold(query).split()
    if not terms:
        raise ValueError('Escreva uma busca de até 160 caracteres.')

    def matches(text):
        normalized = fold(text)
        return all(term in normalized for term in terms)

    result = {'guias': [], 'pdfs': [], 'zim': [], 'mapas': [],
              'indisponiveis': [], 'limite_por_grupo': LIMIT}
    for guide in GUIAS:
        if matches(' '.join(guide.get(key, '') for key in ('titulo', 'categoria', 'texto'))):
            result['guias'].append({key: guide[key] for key in ('id', 'titulo')})
        if len(result['guias']) == LIMIT:
            break
    for guide in guias_pdf.catalog():
        for page, text in enumerate(PDF_TEXT.get(guide['id'], ()), 1):
            if matches(guide['titulo'] + ' ' + guide['descricao'] + ' ' + text):
                result['pdfs'].append({'id': guide['id'], 'titulo': guide['titulo'], 'pagina': page})
                break
        if len(result['pdfs']) == LIMIT:
            break

    def unavailable(kind, item):
        result['indisponiveis'].append({'tipo': kind, 'id': item['id'], 'nome': item['nome']})

    for book in store.encyclopedias():
        if not book['disponivel']:
            unavailable('zim', book)
            continue
        try:
            hits = read_zim(store.zim_path(book['id']), query=query)
            result['zim'].extend(dict(hit, colecao=book['id'], nome_colecao=book['nome'])
                                 for hit in hits[:LIMIT - len(result['zim'])])
        except (ValueError, OSError):
            unavailable('zim', book)
        if len(result['zim']) == LIMIT:
            break
    for item in store.installed_maps():
        if not item['disponivel']:
            unavailable('mapa', item)
            continue
        try:
            path = store.map_path(item['id'])
            if path.suffix.lower() != '.ulmap':
                continue
            hits = mapa_vetor.search(path, query)
            result['mapas'].extend(dict(hit, mapa_id=item['id'], nome_mapa=item['nome'])
                                   for hit in hits[:LIMIT - len(result['mapas'])])
        except (ValueError, OSError, sqlite3.Error):
            unavailable('mapa', item)
        if len(result['mapas']) == LIMIT:
            break
    return result
