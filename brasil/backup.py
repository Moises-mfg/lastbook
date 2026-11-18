"""Backup portátil dos dados pessoais; arquivos grandes são importados à parte.

O campo opcional ``conversas`` substitui o histórico inteiro quando presente.
Sua ausência preserva o histórico do destino. Nenhum caminho do arquivo é usado.
"""
import json
import os
from pathlib import Path
import stat
import tempfile

from .catalogo import COMPRAS

FORMAT = 'o-ultimo-livro-backup'
VERSION = 1


def _text(value):
    if not isinstance(value, str):
        raise ValueError('Texto inválido no backup.')
    # JSON aceita escapes de substitutos Unicode isolados; SQLite não os aceita.
    value.encode('utf-8')
    return value


def _validate(body):
    # Importação tardia permite que Store exponha esta API sem dependência circular.
    from .core import validate_choices

    required = {'formato', 'versao', 'escolhas', 'checklist'}
    if not isinstance(body, dict) or not required <= body.keys() or body.keys() - required - {'conversas'}:
        raise ValueError('Estrutura de backup inválida.')
    if body['formato'] != FORMAT or type(body['versao']) is not int or body['versao'] != VERSION:
        raise ValueError('Formato ou versão de backup não suportados.')
    choices = body['escolhas']
    if choices is not None:
        fields = {'versao', 'perfil', 'modelo', 'wikis', 'estados', 'mapa', 'municipios'}
        if not isinstance(choices, dict) or choices.keys() != fields or type(choices['versao']) is not int or choices['versao'] != 1:
            raise ValueError('Escolhas inválidas no backup.')
        choices = validate_choices(choices)
    checklist = body['checklist']
    known = {item['id'] for item in COMPRAS}
    seen = set()
    if not isinstance(checklist, list):
        raise ValueError('Checklist inválido no backup.')
    for item in checklist:
        if (not isinstance(item, dict) or item.keys() != {'id', 'feito'}
                or not isinstance(item['id'], str) or item['id'] not in known
                or item['id'] in seen or type(item['feito']) is not bool):
            raise ValueError('Item de checklist inválido ou repetido no backup.')
        seen.add(item['id'])
    conversations = body.get('conversas')
    if 'conversas' in body:
        if not isinstance(conversations, list):
            raise ValueError('Histórico inválido no backup.')
        for turn in conversations:
            if not isinstance(turn, dict) or turn.keys() != {'pergunta', 'resposta', 'fontes', 'criado_em'}:
                raise ValueError('Conversa inválida no backup.')
            for field in ('pergunta', 'resposta', 'criado_em'):
                _text(turn[field])
            if not isinstance(turn['fontes'], list):
                raise ValueError('Fontes inválidas no backup.')
            for source in turn['fontes']:
                if not isinstance(source, dict) or 'titulo' not in source:
                    raise ValueError('Fonte inválida no backup.')
                for key, value in source.items():
                    _text(key)
                    _text(value)
    return dict(body, escolhas=choices)


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Campo repetido no backup.')
        result[key] = value
    return result


def _invalid_constant(value):
    raise ValueError('Número inválido no backup.')


def _destination(store, path):
    destination = Path(path).absolute()
    # Não substituir o banco aberto, seus auxiliares, nem um hard link para ele.
    database = store.folder / 'dados.sqlite'
    for suffix in ('', '-wal', '-shm', '-journal'):
        protected = Path(str(database) + suffix)
        if destination.resolve() == protected.resolve() or (
                destination.exists() and protected.exists() and destination.samefile(protected)):
            raise ValueError('Escolha um arquivo de backup separado do banco de dados.')
    if destination.is_symlink() or (destination.exists() and not destination.is_file()):
        raise ValueError('Escolha um arquivo regular para o backup.')
    return destination


def export_backup(store, path, include_chat=False):
    """Exporta uma fotografia consistente; substitui o destino só após gravá-la."""
    if type(include_chat) is not bool:
        raise ValueError('A opção de incluir conversas deve ser verdadeira ou falsa.')
    destination = _destination(store, path)
    with store.db() as db:
        db.execute('BEGIN')
        row = db.execute("SELECT value FROM settings WHERE key='choices'").fetchone()
        done = dict(db.execute('SELECT id,done FROM checklist'))
        body = {'formato': FORMAT, 'versao': VERSION,
                'escolhas': json.loads(row[0]) if row else None,
                'checklist': [{'id': item['id'], 'feito': bool(done.get(item['id']))} for item in COMPRAS]}
        if include_chat:
            rows = db.execute('SELECT pergunta,resposta,fontes,criado_em FROM chat_turns ORDER BY id')
            body['conversas'] = [dict(pergunta=q, resposta=a, fontes=json.loads(s), criado_em=t)
                                 for q, a, s, t in rows]
    body = _validate(body)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=destination.parent,
                                         prefix='.ultimo-livro-backup-', suffix='.tmp', delete=False) as output:
            temporary = Path(output.name)
            json.dump(body, output, ensure_ascii=False, allow_nan=False, indent=2)
            output.write('\n')
            output.flush()
            os.fsync(output.fileno())
        # Revalida antes da troca, inclusive se o seletor indicou um link simbólico.
        _destination(store, destination)
        os.replace(temporary, destination)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return {'mensagem': 'Backup exportado.', 'chat_incluido': include_chat,
            'checklist': len(body['checklist']), 'conversas': len(body.get('conversas', []))}


def restore_backup(store, path):
    """Valida antes de escrever e restaura todos os campos numa transação SQLite."""
    source = Path(path)
    if not source.is_file():
        raise ValueError('Escolha um arquivo regular de backup.')
    try:
        with source.open('r', encoding='utf-8') as backup:
            if not stat.S_ISREG(os.fstat(backup.fileno()).st_mode):
                raise ValueError('Escolha um arquivo regular de backup.')
            body = json.load(backup, object_pairs_hook=_object, parse_constant=_invalid_constant)
        body = _validate(body)
    except (ValueError, UnicodeError, RecursionError) as error:
        raise ValueError('Backup inválido: ' + str(error)) from error
    with store.lock:
        if store.closing.is_set() or store.job['estado'] in ('executando', 'baixando'):
            raise ValueError('Aguarde a operação atual terminar antes de restaurar o backup.')
        with store.db() as db:
            db.execute('BEGIN IMMEDIATE')
            if body['escolhas'] is None:
                db.execute("DELETE FROM settings WHERE key='choices'")
            else:
                db.execute('INSERT OR REPLACE INTO settings VALUES (?,?)',
                           ('choices', json.dumps(body['escolhas'], ensure_ascii=False)))
            db.execute('DELETE FROM checklist')
            db.executemany('INSERT INTO checklist (id,done) VALUES (?,?)',
                           [(item['id'], int(item['feito'])) for item in body['checklist']])
            if 'conversas' in body:
                db.execute('DELETE FROM chat_turns')
                db.executemany('INSERT INTO chat_turns (pergunta,resposta,fontes,criado_em) VALUES (?,?,?,?)',
                               [(t['pergunta'], t['resposta'], json.dumps(t['fontes'], ensure_ascii=False), t['criado_em'])
                                for t in body['conversas']])
        # Não deixar a resposta anterior reaparecer na interface após a restauração.
        if 'conversas' in body and 'resposta' in store.job:
            store.job = {'estado': 'parado'}
    return {'mensagem': 'Backup restaurado. Arquivos grandes podem ser importados separadamente.',
            'chat_incluido': 'conversas' in body, 'checklist': len(body['checklist']),
            'conversas': len(body.get('conversas', []))}


def transfer(store, body, choose_path):
    action = body.get('acao')
    include_chat = body.get('incluir_chat', False)
    if action not in ('exportar', 'restaurar') or type(include_chat) is not bool:
        raise ValueError('Operação de backup inválida.')
    saving = action == 'exportar'
    title = 'Salvar backup do O Último Livro' if saving else 'Abrir backup do O Último Livro'
    path = choose_path(title, saving)
    if not path:
        return {'cancelado': True}
    return export_backup(store, path, include_chat) if saving else restore_backup(store, path)
