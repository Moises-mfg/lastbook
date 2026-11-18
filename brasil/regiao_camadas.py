"""Importação local de GeoJSON; a procedência é informada pelo usuário.

As coordenadas seguem a ordem GeoJSON longitude/latitude em WGS84. Uma camada
não comprova cobertura do município, segurança, disponibilidade ou atualização.
Nenhum endereço de fonte é consultado por este módulo.
"""
import datetime
import json
import math
import os
from pathlib import Path
import re
import stat
from urllib.parse import urlsplit

MAX_BYTES = 2 * 1024 * 1024
MAX_FEATURES = 500
MAX_VERTICES = 12000
TIPOS = ('saude', 'abrigos', 'risco')


def _texto(value, label, limit):
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ValueError(f'{label} inválido ou acima do limite de {limit} caracteres.')
    if any(ord(char) < 32 or 0xD800 <= ord(char) <= 0xDFFF for char in value):
        raise ValueError(f'{label} contém caracteres inválidos.')
    return value.strip()


def _municipio(value):
    if not isinstance(value, str) or not re.fullmatch(r'[0-9]{7}', value):
        raise ValueError('Informe o código IBGE do município com sete dígitos.')
    return value


def _tipo(value):
    if not isinstance(value, str) or value not in TIPOS:
        raise ValueError('Tipo de camada inválido: use saude, abrigos ou risco.')
    return value


def _metadados(body):
    if not isinstance(body, dict):
        raise ValueError('Dados da camada inválidos.')
    ibge = _municipio(body.get('ibge'))
    kind = _tipo(body.get('tipo'))
    title = _texto(body.get('titulo'), 'Título', 160)
    source = _texto(body.get('fonte'), 'Fonte HTTPS', 1500)
    try:
        parsed = urlsplit(source)
        valid = (parsed.scheme == 'https' and parsed.hostname and not parsed.username
                 and not parsed.password and not any(char.isspace() for char in source)
                 and '\\' not in source)
        parsed.port  # Valida também portas malformadas.
    except ValueError:
        valid = False
    if not valid:
        raise ValueError('Informe uma fonte HTTPS válida, sem credenciais.')
    date = _texto(body.get('data'), 'Data de referência', 10)
    try:
        if datetime.date.fromisoformat(date).isoformat() != date:
            raise ValueError
    except ValueError:
        raise ValueError('Informe a data de referência no formato AAAA-MM-DD.') from None
    return ibge, {'tipo': kind, 'titulo': title, 'fonte': source, 'data': date}


def _tabela(db):
    db.execute('''CREATE TABLE IF NOT EXISTS regiao_camadas (
        ibge TEXT NOT NULL, tipo TEXT NOT NULL, dados TEXT NOT NULL,
        PRIMARY KEY (ibge, tipo))''')


def _geometria(geometry, kind, budget):
    if not isinstance(geometry, dict):
        raise ValueError('Cada feição deve conter uma geometria.')
    geo_type = geometry.get('type')
    allowed = ('Polygon', 'MultiPolygon') if kind == 'risco' else ('Point',)
    if geo_type not in allowed:
        raise ValueError('Use apenas pontos para saúde/abrigos e polígonos para risco; não misture os tipos.')
    if 'crs' in geometry:
        raise ValueError('Informe o sistema de coordenadas somente na coleção GeoJSON.')

    def position(point):
        if not isinstance(point, list) or len(point) != 2:
            raise ValueError('Cada posição deve conter somente longitude e latitude WGS84.')
        for value, limit in zip(point, (180, 90)):
            if type(value) not in (int, float) or not -limit <= value <= limit or not math.isfinite(value):
                raise ValueError('Coordenadas WGS84 devem ser finitas: longitude entre -180 e 180 e latitude entre -90 e 90.')
        budget[0] += 1
        if budget[0] > MAX_VERTICES:
            raise ValueError(f'A camada excede o limite de {MAX_VERTICES} vértices.')
        return list(point)

    def polygon(rings):
        if not isinstance(rings, list) or not rings:
            raise ValueError('Polígono sem anéis de coordenadas.')
        result = []
        for ring in rings:
            if not isinstance(ring, list) or len(ring) < 4:
                raise ValueError('Cada anel precisa de ao menos quatro posições, incluindo o fechamento.')
            clean = [position(point) for point in ring]
            if clean[0] != clean[-1] or len({tuple(point) for point in clean[:-1]}) < 3:
                raise ValueError('Cada anel deve estar fechado e ter ao menos três vértices distintos.')
            result.append(clean)
        return result

    coords = geometry.get('coordinates')
    if geo_type == 'Point':
        clean = position(coords)
    elif geo_type == 'Polygon':
        clean = polygon(coords)
    else:
        if not isinstance(coords, list) or not coords:
            raise ValueError('Multipolígono sem polígonos.')
        clean = [polygon(part) for part in coords]
    return {'type': geo_type, 'coordinates': clean}


def _features(document, kind):
    if not isinstance(document, dict) or document.get('type') != 'FeatureCollection':
        raise ValueError('O arquivo precisa ser uma coleção GeoJSON FeatureCollection.')
    crs = document.get('crs')
    if crs is not None and crs not in (
        {'type': 'name', 'properties': {'name': 'EPSG:4326'}},
        {'type': 'name', 'properties': {'name': 'urn:ogc:def:crs:OGC:1.3:CRS84'}},
        {'type': 'name', 'properties': {'name': 'urn:ogc:def:crs:EPSG::4326'}},
    ):
        raise ValueError('Reprojete o arquivo para WGS84 (EPSG:4326) antes de importar.')
    features = document.get('features')
    if not isinstance(features, list) or not 1 <= len(features) <= MAX_FEATURES:
        raise ValueError(f'A camada deve ter entre 1 e {MAX_FEATURES} feições.')
    result, budget = [], [0]
    for index, feature in enumerate(features, 1):
        if not isinstance(feature, dict) or feature.get('type') != 'Feature' or 'crs' in feature:
            raise ValueError('Feição GeoJSON inválida.')
        props = feature.get('properties')
        if props is None:
            props = {}
        if not isinstance(props, dict):
            raise ValueError('Propriedades da feição inválidas.')
        name = next((props[key] for key in ('nome', 'name', 'nome_fantasia', 'NO_FANTASIA', 'NM_ESTABELECIMENTO')
                     if key in props and props[key] not in (None, '')), None)
        if name is None:
            name = f'{"Área" if kind == "risco" else "Ponto"} {index}'
        result.append({'nome': _texto(name, 'Nome da feição', 300),
                       'geometry': _geometria(feature.get('geometry'), kind, budget)})
    return result


def listar(store, ibge):
    """Retorna camadas locais; fonte/data são procedência informada pelo usuário."""
    ibge = _municipio(ibge)
    with store.db() as db:
        _tabela(db)
        rows = db.execute('SELECT dados FROM regiao_camadas WHERE ibge=? ORDER BY tipo', (ibge,)).fetchall()
    result = []
    for row in rows:
        try:
            layer = json.loads(row[0])
            _, clean = _metadados(dict(layer, ibge=ibge))
            clean['features'] = _features({'type': 'FeatureCollection', 'features': [
                {'type': 'Feature', 'properties': {'nome': feature['nome']}, 'geometry': feature['geometry']}
                for feature in layer['features']]}, clean['tipo'])
            result.append(clean)
        except (ValueError, TypeError, KeyError, RecursionError):
            raise ValueError('Camada local inválida. Remova a camada e importe novamente.') from None
    return result


def importar(store, body, path):
    """Valida todo o arquivo antes de substituir a camada do mesmo tipo."""
    if not isinstance(body, dict):
        raise ValueError('Dados da camada inválidos.')
    ibge = _municipio(body.get('ibge'))
    if not path:
        return {'cancelado': True, 'mensagem': 'Importação cancelada; camadas preservadas.', 'camadas': listar(store, ibge)}
    ibge, layer = _metadados(body)
    try:
        descriptor = os.open(Path(path), os.O_RDONLY | getattr(os, 'O_NONBLOCK', 0) | getattr(os, 'O_BINARY', 0))
        with os.fdopen(descriptor, 'rb') as file:
            info = os.fstat(file.fileno())
            if not stat.S_ISREG(info.st_mode):
                raise ValueError('Escolha um arquivo GeoJSON local comum.')
            if info.st_size > MAX_BYTES:
                raise ValueError(f'O arquivo excede o limite de {MAX_BYTES // 1024 // 1024} MiB.')
            contents = file.read(MAX_BYTES + 1)
        if len(contents) > MAX_BYTES:
            raise ValueError('O arquivo GeoJSON excede o limite de tamanho.')
        document = json.loads(contents.decode('utf-8-sig'))
        layer['features'] = _features(document, layer['tipo'])
    except (UnicodeError, json.JSONDecodeError, RecursionError):
        raise ValueError('Não foi possível ler um GeoJSON UTF-8 válido.') from None
    with store.db() as db:
        _tabela(db)
        db.execute('INSERT OR REPLACE INTO regiao_camadas (ibge,tipo,dados) VALUES (?,?,?)',
                   (ibge, layer['tipo'], json.dumps(layer, ensure_ascii=False, allow_nan=False)))
    return {'mensagem': 'Camada importada. Fonte e data são informações fornecidas pelo usuário; confira no órgão responsável.',
            'camadas': listar(store, ibge)}


def excluir(store, body):
    if not isinstance(body, dict):
        raise ValueError('Dados da camada inválidos.')
    ibge, kind = _municipio(body.get('ibge')), _tipo(body.get('tipo'))
    with store.db() as db:
        _tabela(db)
        db.execute('DELETE FROM regiao_camadas WHERE ibge=? AND tipo=?', (ibge, kind))
    return {'mensagem': 'Camada local removida.', 'camadas': listar(store, ibge)}
