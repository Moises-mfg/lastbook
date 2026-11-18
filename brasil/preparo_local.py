"""Preparo pessoal offline, guardado por seção no mesmo banco dos demais dados.

Fotos originais ficam no SQLite: referências e conteúdo são transacionais e o
backup pode transportá-los sem depender de caminhos da máquina de origem.
"""
import base64
import datetime
import html
import json
import math
import os
from pathlib import Path
import re
import stat
import tempfile
import uuid

SECOES = ('plano', 'lugares', 'itens', 'recuperacao')
CAMPOS_PLANO = {'encontro1': 'Primeiro ponto de encontro', 'encontro2': 'Segundo ponto de encontro',
                'contato': 'Contato de referência', 'apoio': 'Pessoas que precisam de apoio',
                'levar': 'O que levar'}
MAX_FOTO = 20 * 1024 * 1024
FOTO_ID = re.compile(r'[a-f0-9]{32}')


def _schema(db):
    db.execute('CREATE TABLE IF NOT EXISTS preparo_secoes (secao TEXT PRIMARY KEY, dados TEXT NOT NULL)')
    db.execute('CREATE TABLE IF NOT EXISTS preparo_fotos (id TEXT PRIMARY KEY, nome TEXT NOT NULL, conteudo BLOB NOT NULL)')


def _texto(value):
    if not isinstance(value, str) or len(value) > 20000 or '\x00' in value:
        raise ValueError('Texto inválido no preparo local.')
    try:
        value.encode('utf-8')
    except UnicodeError as error:
        raise ValueError('Texto inválido no preparo local.') from error
    return value


def _data(value):
    _texto(value)
    if value:
        try:
            if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
                raise ValueError()
            datetime.date.fromisoformat(value)
        except ValueError as error:
            raise ValueError('Use uma data válida no formato AAAA-MM-DD.') from error
    return value


def _objeto(value, required, optional=()):
    if not isinstance(value, dict) or not set(required) <= value.keys() or value.keys() - set(required) - set(optional):
        raise ValueError('Campos inválidos no preparo local.')


def _id(value):
    if not _texto(value).strip() or len(value) > 120:
        raise ValueError('Identificador inválido no preparo local.')
    return value


def validar_secao(secao, value):
    """Retorna uma cópia normalizada, sem alterar dados recebidos."""
    if not isinstance(secao, str) or secao not in SECOES:
        raise ValueError('Seção de preparo inválida.')
    if secao == 'plano':
        _objeto(value, CAMPOS_PLANO)
        return {key: _texto(value[key]) for key in CAMPOS_PLANO}
    if not isinstance(value, list) or len(value) > 1000:
        raise ValueError('Lista inválida no preparo local.')
    result, seen, photos_seen = [], set(), set()
    for item in value:
        if secao == 'lugares':
            _objeto(item, ('id', 'nome', 'lat', 'lon', 'notas'), ('revisado',))
        elif secao == 'itens':
            _objeto(item, ('id', 'nome', 'quantidade', 'local', 'revisar'))
        else:
            _objeto(item, ('id', 'data', 'descricao', 'protocolo'), ('fotos',))
        identifier = _id(item['id'])
        if identifier in seen:
            raise ValueError('Identificador repetido no preparo local.')
        seen.add(identifier)
        row = dict(item)
        if secao == 'lugares':
            for key, maximum in (('lat', 90), ('lon', 180)):
                coordinate = row[key]
                if type(coordinate) not in (int, float) or not -maximum <= coordinate <= maximum or not math.isfinite(coordinate):
                    raise ValueError('Coordenadas inválidas no lugar salvo.')
            for key in ('nome', 'notas'):
                _texto(row[key])
            row['revisado'] = _data(row.get('revisado', ''))
        elif secao == 'itens':
            for key in ('nome', 'quantidade', 'local'):
                _texto(row[key])
            _data(row['revisar'])
        else:
            _data(row['data'])
            _texto(row['descricao'])
            _texto(row['protocolo'])
            photos = row.get('fotos', [])
            if not isinstance(photos, list) or len(photos) > 100:
                raise ValueError('Lista de fotos inválida.')
            row['fotos'] = []
            for photo in photos:
                _objeto(photo, ('id', 'nome'))
                if not isinstance(photo['id'], str) or not FOTO_ID.fullmatch(photo['id']) or photo['id'] in photos_seen:
                    raise ValueError('Identificador de foto inválido ou repetido.')
                photos_seen.add(photo['id'])
                row['fotos'].append({'id': photo['id'], 'nome': _texto(photo['nome'])})
        result.append(row)
    return result


def _dados(db):
    result = {'plano': dict.fromkeys(CAMPOS_PLANO, ''), 'lugares': [], 'itens': [], 'recuperacao': []}
    for section, contents in db.execute('SELECT secao,dados FROM preparo_secoes'):
        if section in SECOES:
            result[section] = validar_secao(section, json.loads(contents))
    return result


def dados(store):
    with store.db() as db:
        _schema(db)
        return _dados(db)


def _gravar(db, section, contents):
    db.execute('INSERT OR REPLACE INTO preparo_secoes (secao,dados) VALUES (?,?)',
               (section, json.dumps(contents, ensure_ascii=False, allow_nan=False)))


def _referencias(contents):
    return {photo['id']: photo['nome'] for record in contents['recuperacao'] for photo in record['fotos']}


def salvar(store, body):
    _objeto(body, ('secao', 'dados'))
    section = body['secao']
    contents = validar_secao(section, body['dados'])
    with store.db() as db:
        _schema(db)
        db.execute('BEGIN IMMEDIATE')
        if section == 'recuperacao':
            current = _referencias(_dados(db))
            updated = _referencias({'recuperacao': contents})
            for identifier, name in updated.items():
                found = db.execute('SELECT nome FROM preparo_fotos WHERE id=?', (identifier,)).fetchone()
                if not found or found[0] != name:
                    raise ValueError('Foto não importada ou referência inválida.')
            db.executemany('DELETE FROM preparo_fotos WHERE id=?', ((ident,) for ident in current.keys() - updated.keys()))
        _gravar(db, section, contents)
        return _dados(db)


def _extensao(contents):
    if not contents or len(contents) > MAX_FOTO:
        raise ValueError('A foto deve ter até 20 MB.')
    if contents.startswith(b'\x89PNG\r\n\x1a\n'):
        return '.png'
    if contents.startswith(b'\xff\xd8\xff'):
        return '.jpg'
    raise ValueError('Escolha uma foto JPEG ou PNG válida.')


def adicionar_foto(store, registro_id, path):
    _id(registro_id)
    source = Path(path)
    if not source.is_file():
        raise ValueError('Escolha um arquivo regular de foto.')
    with source.open('rb') as photo:
        if not stat.S_ISREG(os.fstat(photo.fileno()).st_mode):
            raise ValueError('Escolha um arquivo regular de foto.')
        contents = photo.read(MAX_FOTO + 1)
    _extensao(contents)
    name = _texto(source.name)
    identifier = uuid.uuid4().hex
    with store.db() as db:
        _schema(db)
        db.execute('BEGIN IMMEDIATE')
        current = _dados(db)
        record = next((item for item in current['recuperacao'] if item['id'] == registro_id), None)
        if record is None:
            raise ValueError('Registro de recuperação não encontrado.')
        if len(record['fotos']) >= 100:
            raise ValueError('Este registro já contém 100 fotos.')
        item = {'id': identifier, 'nome': name}
        record['fotos'].append(item)
        db.execute('INSERT INTO preparo_fotos (id,nome,conteudo) VALUES (?,?,?)', (identifier, name, contents))
        _gravar(db, 'recuperacao', current['recuperacao'])
    return {'item': item, 'dados': current}


def foto_bytes(store, identifier):
    if not isinstance(identifier, str) or not FOTO_ID.fullmatch(identifier):
        raise ValueError('Foto inválida.')
    with store.db() as db:
        _schema(db)
        db.execute('BEGIN')
        if identifier not in _referencias(_dados(db)):
            raise ValueError('Foto não encontrada.')
        row = db.execute('SELECT conteudo FROM preparo_fotos WHERE id=?', (identifier,)).fetchone()
        if row is None:
            raise ValueError('Foto não encontrada.')
        contents = row[0]
    extension = _extensao(contents)
    return contents, 'image/png' if extension == '.png' else 'image/jpeg'


def _escrever_atomico(destination, contents, validate=None):
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=destination.parent, prefix='.preparo-', suffix='.tmp', delete=False) as output:
            temporary = Path(output.name)
            output.write(contents)
            output.flush()
            os.fsync(output.fileno())
        if validate:
            validate()
        os.replace(temporary, destination)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def exportar_plano(store, body, path):
    from .backup import _destination
    _objeto(body, ('campos',))
    fields = body['campos']
    if (not isinstance(fields, list) or not fields or any(not isinstance(field, str) or field not in CAMPOS_PLANO for field in fields)
            or len(set(fields)) != len(fields)):
        raise ValueError('Selecione os campos do plano que deseja exportar.')
    destination = _destination(store, path)
    if (store.folder / 'preparo-fotos').resolve() in destination.resolve().parents:
        raise ValueError('Escolha um arquivo fora da pasta de fotos.')
    plan = dados(store)['plano']
    sections = ''.join('<section><h2>' + html.escape(CAMPOS_PLANO[field]) + '</h2><p>' +
                       html.escape(plan[field]) + '</p></section>' for field in fields)
    document = ('<!doctype html><html lang="pt-BR"><meta charset="utf-8">'
                '<meta name="viewport" content="width=device-width,initial-scale=1">'
                '<title>Plano familiar — O Último Livro</title><style>'
                'body{font:18px sans-serif;max-width:800px;margin:2em auto;padding:1em;color:#111;background:#fff}'
                'section{break-inside:avoid}h2{font-size:1.1em}p{white-space:pre-wrap;overflow-wrap:anywhere}'
                '@media print{body{margin:0;padding:0;font-size:12pt}}</style>'
                '<body><h1>Plano familiar</h1>' + sections + '</body></html>')
    _escrever_atomico(destination, document.encode('utf-8'), lambda: _destination(store, destination))
    return {'mensagem': 'Plano exportado para impressão.', 'campos': list(fields)}


def exportar_backup(db):
    """Chamado dentro da transação de leitura do backup principal."""
    if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='preparo_secoes'").fetchone():
        return None
    contents = _dados(db)
    photos = {}
    for identifier in _referencias(contents):
        row = db.execute('SELECT conteudo FROM preparo_fotos WHERE id=?', (identifier,)).fetchone()
        if not row:
            raise ValueError('Foto referenciada ausente; backup não exportado.')
        _extensao(row[0])
        photos[identifier] = base64.b64encode(row[0]).decode('ascii')
    return {'dados': contents, 'fotos': photos}


def validar_backup(value):
    _objeto(value, ('dados', 'fotos'))
    _objeto(value['dados'], SECOES)
    contents = {section: validar_secao(section, value['dados'][section]) for section in SECOES}
    photos = value['fotos']
    if not isinstance(photos, dict) or photos.keys() != _referencias(contents).keys():
        raise ValueError('Fotos e referências do backup não correspondem.')
    for encoded in photos.values():
        if not isinstance(encoded, str) or len(encoded) > ((MAX_FOTO + 2) // 3) * 4:
            raise ValueError('Foto inválida no backup.')
        try:
            _extensao(base64.b64decode(encoded, validate=True))
        except (ValueError, UnicodeError) as error:
            raise ValueError('Foto inválida no backup.') from error
    return {'dados': contents, 'fotos': dict(photos)}


def restaurar_backup(db, value):
    """O chamador valida antes e mantém esta escrita na transação principal."""
    _schema(db)
    for section, contents in value['dados'].items():
        _gravar(db, section, contents)
    db.execute('DELETE FROM preparo_fotos')
    references = _referencias(value['dados'])
    db.executemany('INSERT INTO preparo_fotos (id,nome,conteudo) VALUES (?,?,?)',
                   [(identifier, references[identifier], base64.b64decode(encoded, validate=True))
                    for identifier, encoded in value['fotos'].items()])
