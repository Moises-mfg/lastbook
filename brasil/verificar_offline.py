"""Provas locais de leitura e inferência; não baixa arquivos nem usa a conversa.

``check(store)`` é síncrono e deve ser admitido por ``Store.start_job``.
Os estados são ``ok``, ``pendente``, ``ignorado`` e ``erro``. Um resultado
positivo comprova a operação descrita na mensagem, não o funcionamento da UI
ou a ausência de conexão de rede do computador.
"""
import sqlite3
import subprocess
import zlib

from . import guias_pdf, mapa_vetor, plataforma
from .arquivos import map_tile, read_zim
from .sqlite_local import Connection


class Pending(ValueError):
    """Conteúdo opcional ainda não instalado."""


def _pdf(store):
    path = guias_pdf.GUIDES_PATH / 'offline.pdf'
    with path.open('rb') as file:
        if path.stat().st_size > 16 * 1024 * 1024:
            raise ValueError('O guia PDF incluído excede o tamanho esperado.')
        content = file.read()
    if not content.startswith(b'%PDF-') or b'%%EOF' not in content[-1024:] or b'/Type /Page' not in content:
        raise ValueError('O guia PDF incluído está incompleto ou inválido.')
    return 'Guia offline.pdf aberto e lido neste computador. Confira a exibição das páginas na Biblioteca.'


def _zim(store):
    books = store.encyclopedias()
    if not books:
        raise Pending('Instale ou importe uma enciclopédia para testar a consulta local.')
    # Ler cada coleção evita declarar a biblioteca pronta quando um disco sumiu.
    for book in books:
        path = store.zim_path(book['id'])
        metadata = read_zim(path)
        if metadata['busca']:
            hits = read_zim(path, query='Brasil OR água OR energia')
            if hits:
                article = read_zim(path, entry=hits[0]['entrada'])
                if article.get('texto', '').strip():
                    continue
        # Coleções sem índice textual continuam válidas: abrir a entrada inicial
        # exercita descompressão e extração HTML, além da leitura de cabeçalho.
        from libzim.reader import Archive
        arc = Archive(path)
        entry = arc.main_entry
        if entry.is_redirect:
            entry = entry.get_redirect_entry()
        article = read_zim(path, entry=entry.path)
        if not article.get('texto', '').strip():
            raise ValueError('A entrada inicial da enciclopédia não contém texto legível.')
    return f'{len(books)} coleção(ões) ZIM consultada(s), com artigo local aberto para leitura.'


def _map(store):
    if not store.active_map_id():
        raise Pending('Escolha e instale ou importe um mapa para testar a leitura local.')
    path = store.map_path()
    metadata = store.map_metadata()
    if path.suffix.lower() == '.ulmap':
        # O centro geográfico pode não conter ruas. Ler uma feição real evita
        # considerar um tile vazio como prova de que as geometrias funcionam.
        with mapa_vetor.connect(path) as db:
            row = db.execute('SELECT geom FROM feat ORDER BY id LIMIT 1').fetchone()
        if row is None or not mapa_vetor.decode(row[0]):
            raise ValueError('O mapa escolhido não contém geometria local legível.')
    else:
        with sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True, factory=Connection) as db:
            row = db.execute('SELECT zoom_level,tile_column,tile_row FROM tiles ORDER BY zoom_level LIMIT 1').fetchone()
        if row is None:
            raise ValueError('O mapa escolhido não contém imagens locais.')
        z, x, tms_y = map(int, row)
        if not map_tile(path, z, x, 2**z - 1 - tms_y):
            raise ValueError('Não foi possível ler uma imagem do mapa escolhido.')
    return f'Metadados e conteúdo do mapa “{metadata["nome"]}” lidos localmente.'


def _ia(store):
    if (store.choices() or {}).get('modelo') == 'sem-ia':
        return 'ignorado', 'IA desativada nas suas escolhas. A biblioteca funciona sem IA.'
    spec = store.model_spec()
    if not store.package_path(spec).is_file() or not store.runner():
        raise Pending('Instale o motor local e o modelo escolhido para testar a IA. A biblioteca funciona sem IA.')
    model, runner = store.ready_model(spec)
    command = [runner, '-m', str(model), '-c', '256', '-n', '8', '-t', '2', '-ngl', '0',
               '--temp', '0', '--seed', '42', '-p', 'Responda apenas: OK /no_think',
               '--no-conversation', '--no-display-prompt', '--simple-io']
    with store.lock:
        if store.closing.is_set():
            raise ValueError('O aplicativo está fechando.')
        if store.proc is not None:
            raise ValueError('O motor de IA já está em uso. Aguarde e tente novamente.')
        proc = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='replace',
                                **plataforma.subprocess_options())
        store.proc = proc
    try:
        try:
            stdout, _ = proc.communicate(timeout=90)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.communicate()
            raise ValueError('O teste da IA excedeu 90 segundos. Tente um modelo menor.') from None
        if proc.returncode:
            raise ValueError('O motor local falhou no teste de inferência. A biblioteca continua disponível.')
        if not stdout.replace('[end of text]', '').strip():
            raise ValueError('O motor local não produziu texto no teste de inferência.')
    finally:
        with store.lock:
            if store.proc is proc:
                store.proc = None
    return 'ok', 'Modelo verificado e inferência curta concluída no motor local, sem usar ou salvar a conversa.'


def check(store):
    """Executa provas independentes; uma falha não impede as outras verificações."""
    results = []
    for ident, title, operation in (
        ('pdf', 'Guia PDF incluído', _pdf),
        ('zim', 'Enciclopédias locais', _zim),
        ('mapa', 'Mapa escolhido', _map),
        ('ia', 'Inteligência artificial local', _ia),
    ):
        try:
            outcome = operation(store)
            state, message = outcome if isinstance(outcome, tuple) else ('ok', outcome)
        except Pending as error:
            state, message = 'pendente', str(error)
        except (ValueError, OSError, RuntimeError, ImportError, sqlite3.Error, zlib.error) as error:
            state, message = 'erro', str(error)[:600]
        results.append({'id': ident, 'titulo': title, 'estado': state, 'mensagem': message})
    return {'resultados': results, 'verificacao_offline': results,
            'mensagem': 'Verificação local concluída. Confira o resultado de cada recurso.'}
