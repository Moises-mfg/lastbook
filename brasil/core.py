"""Dados locais, seleção conservadora e IA opcional. Nenhuma conexão automática."""
import hashlib
import json
import os
import re
from pathlib import Path
import shutil
import sqlite3
import subprocess
import threading
import unicodedata

from engine.setup import hardware, download
from .arquivos import read_zim, map_info
from . import pacotes, mapa_vetor
from .mapas import MapSupport
from .fontes import RECURSOS
from . import plataforma
from .sqlite_local import Connection
from .conversa import build_prompt, OUTPUT_TOKENS
from .catalogo import PERFIS, MODELOS, ESTADOS, WIKIS, MAPAS, GUIAS, COMPRAS

GiB = 2**30


class AnswerStopped(Exception):
    """A pessoa interrompeu a resposta atual."""


def normalize(text):
    return ''.join(c for c in unicodedata.normalize('NFD', text.casefold()) if not unicodedata.combining(c))


def recommend(ram):
    # A RAM indicada pelo kernel é um pouco menor que a instalada. Reservas
    # e disponibilidade são verificadas novamente antes de executar o modelo.
    if not ram:
        return 'leve'
    return 'parruda' if ram >= 30 * GiB else 'moderada' if ram >= 15 * GiB else 'leve'


def validate_choices(body):
    profile = body.get('perfil', 'leve')
    if not isinstance(profile, str) or profile not in PERFIS:
        raise ValueError('Escolha um perfil válido.')
    base = PERFIS[profile]
    model = body.get('modelo', base['modelo'])
    wiki = body.get('wikis', [base['wiki']])
    states = body.get('estados', [])
    map_kind = body.get('mapa', base['mapa'])
    if not isinstance(model, str) or not isinstance(map_kind, str) or model not in MODELOS or map_kind not in MAPAS:
        raise ValueError('Modelo ou abrangência de mapa inválidos.')
    if not isinstance(wiki, list) or len(wiki) > len(WIKIS) or any(not isinstance(w, str) or w not in WIKIS for w in wiki):
        raise ValueError('Seleção de enciclopédias inválida.')
    if not isinstance(states, list) or len(states) > 27 or any(not isinstance(s, str) or s not in ESTADOS for s in states):
        raise ValueError('Seleção de estados inválida.')
    cities=body.get('municipios',[])
    if not isinstance(cities,list) or len(cities)>6000 or any(not isinstance(code,str) or 'map-city-'+code not in pacotes.maps_catalog() for code in cities):
        raise ValueError('Seleção de municípios inválida.')
    return {'versao': 1, 'perfil': profile, 'modelo': model, 'wikis': sorted(set(wiki)),
            'estados': sorted(set(states)), 'mapa': map_kind, 'municipios': sorted(set(cities))}


class Store(MapSupport):
    def __init__(self, folder):
        self.folder = Path(folder)
        self.folder.mkdir(parents=True, exist_ok=True)
        with self.db() as db:
            db.execute('CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS maps (id TEXT PRIMARY KEY, path TEXT NOT NULL, name TEXT NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS encyclopedias (id TEXT PRIMARY KEY, path TEXT NOT NULL, name TEXT NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS checklist (id TEXT PRIMARY KEY, done INTEGER NOT NULL)')
            db.execute('''CREATE TABLE IF NOT EXISTS chat_turns (
                id INTEGER PRIMARY KEY AUTOINCREMENT, pergunta TEXT NOT NULL,
                resposta TEXT NOT NULL, fontes TEXT NOT NULL,
                criado_em TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')))''')
        self.lock = threading.Lock()
        self.job = {'estado': 'parado'}
        self.control = None
        self.proc = None
        self.answer_stop = None
        self.closing = threading.Event()
        with self.db() as db:
            pending = db.execute("SELECT value FROM settings WHERE key='pending-install'").fetchone()
        if pending:
            self.job = {'estado': 'pausado', 'mensagem': 'Há downloads pendentes. Retome quando quiser.'}

    def db(self):
        return sqlite3.connect(self.folder / 'dados.sqlite', timeout=10,factory=Connection)

    def chat_history(self):
        with self.db() as db:
            rows = db.execute('SELECT id,pergunta,resposta,fontes,criado_em FROM chat_turns ORDER BY id DESC LIMIT 100').fetchall()
        return [dict(id=row[0], pergunta=row[1], resposta=row[2], fontes=json.loads(row[3]), criado_em=row[4]) for row in reversed(rows)]

    def clear_chat(self):
        # A mesma trava que admite os jobs impede limpar entre leitura e commit.
        with self.lock:
            if self.job['estado'] in ('executando', 'baixando'):
                raise ValueError('Aguarde a operação atual terminar antes de iniciar uma nova conversa.')
            with self.db() as db:
                db.execute('DELETE FROM chat_turns')
            if 'resposta' in self.job:
                self.job = {'estado': 'parado'}
        return {'history': []}

    def remember_chat(self, question, answer, sources):
        with self.db() as db:
            db.execute('INSERT INTO chat_turns (pergunta,resposta,fontes) VALUES (?,?,?)',
                       (question, answer, json.dumps(sources, ensure_ascii=False)))
        return {'resposta': answer, 'fontes': sources}

    def choices(self):
        with self.db() as db:
            row = db.execute("SELECT value FROM settings WHERE key='choices'").fetchone()
        return json.loads(row[0]) if row else None

    def save_choices(self, body):
        choices = validate_choices(body)
        with self.db() as db:
            db.execute('INSERT OR REPLACE INTO settings VALUES (?,?)', ('choices', json.dumps(choices)))
        return choices

    def checklist(self):
        with self.db() as db:
            done = dict(db.execute('SELECT id,done FROM checklist'))
        return [dict(item, feito=bool(done.get(item['id']))) for item in COMPRAS]

    def check(self, body):
        if body.get('id') not in {x['id'] for x in COMPRAS} or type(body.get('feito')) is not bool:
            raise ValueError('Item inválido.')
        with self.db() as db:
            db.execute('INSERT OR REPLACE INTO checklist VALUES (?,?)', (body['id'], int(body['feito'])))
        return self.checklist()

    def state(self):
        h = hardware.detect([str(self.folder)])
        return {'versao': '0.4.0-alpha.7', 'hardware': {'ram_bytes': h.get('ram_bytes'), 'arch': h['arch'], 'os': h['os'],
                 'livre_bytes': shutil.disk_usage(self.folder).free,
                 'ram_disponivel_bytes': plataforma.available_memory()}, 'recomendado': recommend(h.get('ram_bytes')),
                'escolhas': self.choices(), 'perfis': PERFIS, 'modelos': MODELOS, 'wikis': WIKIS, 'estados': ESTADOS,
                'mapas': MAPAS, 'catalogo': self.package_state(), 'plano': self.install_plan(), 'enciclopedias': self.encyclopedias(), 'guias': GUIAS, 'compras': self.checklist(), 'ia': {'motor': bool(self.runner()),
                'modelo': self.model_path().is_file(), 'ram_necessaria_gib': self.model_spec()['available_gib'], 'download_bytes': self.model_spec()['size'], 'nome': self.model_spec()['file']},
                'recursos': RECURSOS, 'mapas_instalados': self.installed_maps(), 'mapa_ativo': self.active_map_id(), 'mapas_disponiveis': bool(pacotes.maps_catalog()), 'arquivos': self.files(), 'aviso': 'Modelos, enciclopédias e mapas locais. Nenhum download ocorre ao abrir o aplicativo.'}

    def files(self):
        with self.db() as db:
            rows = db.execute("SELECT key,value FROM settings WHERE key LIKE 'arquivo:%'").fetchall()
        return {k.split(':',1)[1]: json.loads(v)['nome'] for k,v in rows}

    def file_path(self, kind):
        with self.db() as db:
            row = db.execute('SELECT value FROM settings WHERE key=?', ('arquivo:'+kind,)).fetchone()
        if not row:
            raise ValueError('Selecione primeiro um arquivo local.')
        path = Path(json.loads(row[0])['caminho'])
        if not path.is_file():
            raise ValueError('Arquivo não encontrado. Reconecte o disco ou selecione novamente.')
        return path

    def import_plan(self, path):
        path = Path(path)
        if path.suffix.lower() != '.json' or path.stat().st_size > 16384:
            raise ValueError('Escolha um plano JSON de até 16 KB exportado pelo site.')
        try:
            body = json.loads(path.read_text(encoding='utf-8'))
        except (ValueError, UnicodeError) as error:
            raise ValueError('Não foi possível ler o plano.') from error
        if not isinstance(body, dict):
            raise ValueError('Plano inválido.')
        if body.get('versao') != 1:
            raise ValueError('Versão de plano não suportada.')
        self.save_choices(body)
        return {'mensagem': 'Plano importado. Nenhum download foi iniciado.'}

    def import_file(self, kind, path):
        path = Path(path).resolve()
        if kind not in ('zim','mapa') or not path.is_file():
            raise ValueError('Arquivo inválido.')
        if kind == 'zim':
            if path.suffix.lower() != '.zim': raise ValueError('Escolha um arquivo .zim.')
            read_zim(path)
        else:
            if path.suffix.lower() not in ('.mbtiles','.ulmap'): raise ValueError('Escolha um arquivo .mbtiles ou .ulmap.')
            (mapa_vetor.info if path.suffix.lower()=='.ulmap' else map_info)(path)
        with self.db() as db:
            db.execute('INSERT OR REPLACE INTO settings VALUES (?,?)', ('arquivo:'+kind,json.dumps({'nome':path.name,'caminho':str(path)})))
            if kind == 'mapa':
                ident='local-'+hashlib.sha256(str(path).encode()).hexdigest()[:20]
                db.execute('INSERT OR REPLACE INTO maps VALUES (?,?,?)',(ident,str(path),path.name))
                db.execute('INSERT OR REPLACE INTO settings VALUES (?,?)',('active-map',ident))
            if kind == 'zim':
                ident = 'local-' + hashlib.sha256(str(path).encode()).hexdigest()[:20]
                db.execute('INSERT OR REPLACE INTO encyclopedias VALUES (?,?,?)', (ident, str(path), path.name))
        return {'nome':path.name}

    def encyclopedias(self):
        with self.db() as db:
            rows = db.execute('SELECT id,path,name FROM encyclopedias ORDER BY name').fetchall()
        items = [{'id': ident, 'nome': name, 'disponivel': Path(path).is_file()} for ident, path, name in rows]
        # Importações da primeira alpha continuam consultáveis.
        if 'zim' in self.files():
            try:
                path = self.file_path('zim')
                if not any(path == Path(row[1]) for row in rows):
                    items.insert(0, {'id': 'importado', 'nome': path.name, 'disponivel': True})
            except ValueError:
                pass
        return items

    def zim_path(self, ident):
        if ident == 'importado':
            return self.file_path('zim')
        with self.db() as db:
            row = db.execute('SELECT path FROM encyclopedias WHERE id=?', (ident,)).fetchone()
        if not row or not Path(row[0]).is_file():
            raise ValueError('Enciclopédia não encontrada. Reconecte o disco ou instale novamente.')
        return Path(row[0])

    def search_zim(self, body):
        query = body.get('busca', '')
        if not isinstance(query, str) or not 1 <= len(query.strip()) <= 200:
            raise ValueError('Escreva uma busca de até 200 caracteres.')
        selected = body.get('colecao')
        if selected is not None and not isinstance(selected, str):
            raise ValueError('Coleção inválida.')
        books = self.encyclopedias()
        if selected:
            books = [book for book in books if book['id'] == selected]
        if not books:
            raise ValueError('Instale ou importe uma enciclopédia primeiro.')
        matches, errors = [], []
        for book in books:
            try:
                found = read_zim(self.zim_path(book['id']), query=query)
                matches.extend(dict(hit, colecao=book['id'], nome_colecao=book['nome']) for hit in found)
            except ValueError:
                errors.append(book['nome'])
        return {'resultados': matches, 'indisponiveis': errors}

    def article_zim(self, body):
        entry = body.get('entrada', '')
        if not isinstance(entry, str) or not 1 <= len(entry) <= 2000:
            raise ValueError('Artigo inválido.')
        ident = body.get('colecao') or (self.encyclopedias()[0]['id'] if self.encyclopedias() else 'importado')
        if not isinstance(ident, str):
            raise ValueError('Coleção inválida.')
        return dict(read_zim(self.zim_path(ident), entry=entry), colecao=ident, entrada=entry)

    def package_path(self, item):
        return self.folder / ({'model':'models','zim':'encyclopedias','map':'maps'}[item['kind']]) / item['file']

    def package_state(self, choices=None):
        selected_maps = set(self.chosen_map_ids(choices))
        with self.db() as db:
            installed = {k.split(':', 1)[1]: v for k, v in db.execute("SELECT key,value FROM settings WHERE key LIKE 'verified:%'")}
        result = {}
        for ident, item in pacotes.all_catalog().items():
            if item['kind'] == 'map' and ident not in selected_maps:
                continue
            path = self.package_path(item)
            try:
                verified = item['sha256'] == installed.get(ident) and path.stat().st_size == item['size'] and path.is_file()
                partial = 0 if verified else pacotes.partial_bytes(path, item)
            except FileNotFoundError:
                verified = False
                partial = 0
            result[ident] = dict(item, instalado=verified, parcial_bytes=partial)
        return result

    def storage_plan(self, items):
        pending = [item for item in items if not item['instalado']]
        remaining = sum(max(0, item['size'] - item['parcial_bytes']) for item in pending)
        assembly = sum(item['size'] for item in pending if 'parts' in item)
        reserve = GiB if pending else 0
        free = shutil.disk_usage(self.folder).free
        required = remaining + assembly + reserve
        return {'download_bytes': remaining, 'montagem_bytes': assembly, 'reserva_bytes': reserve,
                'livre_bytes': free, 'necessario_bytes': required, 'espaco_suficiente': free >= required}

    def install_plan(self, choices=None):
        choices = choices or self.choices() or validate_choices({'perfil': 'leve'})
        ids = list(choices['wikis'])
        if choices['modelo'] != 'sem-ia':
            ids.insert(0, choices['modelo'])
        ids += self.chosen_map_ids(choices)
        known = self.package_state(choices)
        items = [known[ident] for ident in ids]
        return dict(self.storage_plan(items), pacotes=items,
                    aviso_mapas='Mapas regionais selecionados incluídos no total.' if pacotes.maps_catalog()
                    else 'Mapas ainda não publicados para esta versão.')

    def preview_install(self, body):
        plan = self.install_plan(validate_choices(body))
        fields = ('id', 'kind', 'name', 'size', 'instalado', 'parcial_bytes')
        plan['pacotes'] = [{key: item[key] for key in fields if key in item}
                           for item in plan['pacotes']]
        return plan

    def install_packages(self, ids):
        known=pacotes.all_catalog()
        if not isinstance(ids, list) or not ids or len(ids) > len(known) or any(not isinstance(i, str) or i not in known for i in ids):
            raise ValueError('Selecione pacotes válidos.')
        ids = list(dict.fromkeys(ids))
        items = [known[ident] for ident in ids]
        def work():
            with self.db() as db:
                db.execute('INSERT OR REPLACE INTO settings VALUES (?,?)', ('pending-install', json.dumps(ids)))
            self.control = download.Control()
            if self.closing.is_set():
                self.control.stop('paused')
            pending = []
            for item in items:
                target = self.package_path(item)
                if not target.is_file() or target.stat().st_size != item['size']:
                    pending.append(dict(item, instalado=False, parcial_bytes=pacotes.partial_bytes(target, item)))
            if not self.storage_plan(pending)['espaco_suficiente']:
                raise ValueError('Espaço insuficiente. Libere espaço antes de baixar os pacotes escolhidos.')
            for index, item in enumerate(items):
                self.control.check()
                def progress(done, total, phase):
                    with self.lock:
                        self.job = {'estado': 'baixando', 'feito': done, 'total': total,
                                    'fase': 'Verificando' if phase == 'verifying' else 'Baixando',
                                    'pacote': item['id'], 'nome': item['file'], 'indice': index + 1, 'quantidade': len(items)}
                path = pacotes.obtain(item, self.package_path(item), self.control, progress)
                if item['kind'] == 'zim':
                    read_zim(path)
                elif item['kind']=='map':mapa_vetor.info(path)
                self.control.check()
                with self.db() as db:
                    if item['kind'] == 'zim':
                        db.execute('INSERT OR REPLACE INTO encyclopedias VALUES (?,?,?)', (item['id'], str(path), item['file']))
                    if item['kind']=='map':
                        db.execute('INSERT OR REPLACE INTO maps VALUES (?,?,?)',(item['id'],str(path),item['name']))
                        db.execute('INSERT OR REPLACE INTO settings VALUES (?,?)',('active-map',item['id']))
                    db.execute('INSERT OR REPLACE INTO settings VALUES (?,?)', ('verified:' + item['id'], item['sha256']))
            with self.db() as db:
                db.execute("DELETE FROM settings WHERE key='pending-install'")
            return {'mensagem': 'Pacotes verificados e ativados. A consulta funciona sem internet.'}
        return self.start_job(work)

    def install_selected(self, body):
        plan = self.install_plan()
        if not plan['espaco_suficiente']:
            raise ValueError('O espaço livre não cobre os componentes escolhidos. Reduza a seleção ou libere espaço.')
        pending = [item['id'] for item in plan['pacotes'] if not item['instalado']]
        if not pending:
            raise ValueError('Todos os componentes escolhidos já estão instalados.')
        return self.install_packages(pending)

    def resume_install(self, body):
        with self.db() as db:
            row = db.execute("SELECT value FROM settings WHERE key='pending-install'").fetchone()
        if not row:
            raise ValueError('Não há instalação pendente.')
        return self.install_packages(json.loads(row[0]))

    def pause_install(self, body):
        if self.control and self.job['estado'] == 'baixando':
            self.control.stop('paused')
            return {'mensagem': 'Pausa solicitada. O arquivo parcial será preservado.'}
        raise ValueError('Não há download em andamento.')

    def model_spec(self):
        ident = (self.choices() or {}).get('modelo', 'qwen3-0.6b')
        return pacotes.catalog().get(ident, pacotes.catalog()['qwen3-0.6b'])

    def runner(self):
        bundled = Path(__file__).parent / 'runtime' / ('llama-completion.exe' if os.name=='nt' else 'llama-completion')
        return str(bundled) if bundled.is_file() else shutil.which('llama-completion')

    def model_path(self):
        return self.package_path(self.model_spec())

    def start_job(self, work, *, answer_stop=None):
        with self.lock:
            if self.job['estado'] in ('executando', 'baixando'):
                raise ValueError('Aguarde a operação atual terminar.')
            self.answer_stop = answer_stop
            self.job = {'estado': 'executando', 'cancelavel': answer_stop is not None}
        def run():
            try:
                result = work()
                with self.lock:
                    self.job = {'estado': 'concluido', **result}
            except AnswerStopped:
                with self.lock:
                    self.job = {'estado': 'cancelado', 'mensagem': 'Resposta interrompida. Você pode editar e enviar a pergunta novamente.'}
            except download.Stopped:
                with self.lock:
                    self.job = {'estado': 'pausado', 'mensagem': 'Download pausado. Você pode retomar depois.'}
            except download.Failed as e:
                with self.lock:
                    message = 'O arquivo não passou na verificação. Tente baixar novamente.' if e.code == 'checksum' else 'Não foi possível concluir o download. Confira a conexão e o espaço disponível e retome quando quiser.'
                    self.job = {'estado': 'erro', 'mensagem': message}
            except Exception as e:
                with self.lock:
                    self.job = {'estado': 'erro', 'mensagem': str(e)[:600]}
        threading.Thread(target=run, daemon=True).start()
        return {'iniciado': True}

    def stop_answer(self):
        with self.lock:
            if not self.job.get('cancelavel') or self.answer_stop is None:
                raise ValueError('Não há resposta em andamento.')
            self.answer_stop.stop('paused')
            self.job['cancelavel'] = False
            if self.proc is not None and self.proc.poll() is None:
                self.proc.kill()
        return {'mensagem': 'Interrompendo a resposta…'}

    def close(self):
        self.closing.set()
        if self.control:
            self.control.stop('paused')
        with self.lock:
            if self.answer_stop:
                self.answer_stop.stop('paused')
            proc = self.proc
        if proc is not None and proc.poll() is None:
            proc.terminate()
            try: proc.wait(timeout=3)
            except subprocess.TimeoutExpired: proc.kill(); proc.wait(timeout=3)

    def download_model(self):
        selected = (self.choices() or {}).get('modelo', 'qwen3-0.6b')
        if selected == 'sem-ia':
            raise ValueError('Escolha um modelo em Minha instalação antes de baixá-lo.')
        return self.install_packages([selected])

    def sources_for(self, question, history=None):
        ignored = {'como','para','uma','com','que','qual','quais','posso','meu','minha','meus','minhas','por','dos','das','sobre','mais','ser','sao','voce','isso','isto','onde','quando','porque','tem','ter','fazer','devo'}
        context = ' '.join(item['pergunta'] + ' ' + ' '.join(source['titulo'] for source in item['fontes'])
                           for item in (history or [])[-2:])
        words = [w for w in re.findall(r'[^\W_]+', normalize(question + ' ' + context)) if len(w) > 2 and w not in ignored]
        terms = set(words)
        ranked = sorted(GUIAS, key=lambda g: len(terms & set(normalize(g['titulo'] + ' ' + g['texto']).split())), reverse=True)
        sources = [{'tipo': 'guia', 'id': g['id'], 'titulo': g['titulo'], 'texto': g['texto'][:1000]}
                   for g in ranked[:2] if terms & set(normalize(g['titulo'] + ' ' + g['texto']).split())]
        if words and self.encyclopedias():
            query = ' OR '.join(dict.fromkeys(words[:6]))[:200]
            hits = self.search_zim({'busca': query})['resultados']
            for hit in hits[:2]:
                try:
                    article = self.article_zim(hit)
                    sources.append({'tipo': 'zim', 'titulo': hit['titulo'], 'colecao': hit['colecao'],
                                    'nome_colecao': hit['nome_colecao'], 'entrada': hit['entrada'], 'texto': article['texto'][:1000]})
                except ValueError:
                    continue
        sources.sort(key=lambda source: source['tipo'] != 'zim')
        return [dict(source, ref=f'F{index + 1}') for index, source in enumerate(sources)]

    def ready_model(self, spec, control=None):
        model, runner = self.package_path(spec), self.runner()
        if not runner or not model.is_file():
            raise ValueError('Instale o motor local e baixe o modelo antes de usar a IA. A busca funciona sem eles.')
        if model.stat().st_size != spec['size']:
            raise ValueError('Arquivo de modelo incompleto.')
        available = plataforma.available_memory()
        if available is None or available < spec['available_gib'] * GiB:
            minimum = f'{spec["available_gib"]:g}'.replace('.', ',')
            raise ValueError(f'É preciso ao menos {minimum} GiB de memória disponível para este modelo. Feche outros programas ou escolha um modelo menor.')
        if not pacotes.verified_file(model, spec, control):
            raise ValueError('O modelo não passou na verificação de integridade.')
        return model, runner

    def ask(self, body):
        selected = (self.choices() or {}).get('modelo', 'qwen3-0.6b')
        if selected == 'sem-ia':
            raise ValueError('A IA está desativada nas suas escolhas. A biblioteca continua disponível.')
        question = body.get('pergunta', '')
        if not isinstance(question, str) or not question.strip() or len(question) > 1500:
            raise ValueError('Escreva uma pergunta de até 1.500 caracteres.')
        spec = pacotes.catalog()[selected]
        control = download.Control()
        def check_stop():
            try:
                control.check()
            except download.Stopped as error:
                raise AnswerStopped() from error

        def work():
            try:
                model, runner = self.ready_model(spec, control)
            except download.Stopped as error:
                raise AnswerStopped() from error
            check_stop()
            history = self.chat_history()
            references = self.sources_for(question, history)
            prompt, references = build_prompt(question, history, references, spec['context'])
            command = [runner, '-m', str(model), '-c', str(spec['context']), '-n', str(OUTPUT_TOKENS), '-t', '2', '-ngl', '0',
                       '--temp', '0.2', '--seed', '42', '-p', prompt, '--no-conversation', '--no-display-prompt', '--simple-io']
            with self.lock:
                check_stop()
                if self.closing.is_set(): raise AnswerStopped()
                proc = self.proc = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='replace', **plataforma.subprocess_options())
            try:
                stdout, stderr = proc.communicate(timeout=180)
            except subprocess.TimeoutExpired:
                proc.kill(); proc.communicate()
                check_stop()
                raise ValueError('A resposta demorou demais. Use a busca ou tente uma pergunta menor.')
            finally:
                with self.lock: self.proc = None
            check_stop()
            if proc.returncode:
                raise ValueError('O motor de IA não conseguiu responder. A biblioteca continua disponível.')
            answer = stdout.replace('[end of text]', '').strip()[-12000:]
            if not answer:
                raise ValueError('O motor de IA não produziu uma resposta. Tente uma pergunta menor.')
            with self.lock:
                check_stop()
                self.job['cancelavel'] = False
                return self.remember_chat(question, answer, [{k: v for k, v in source.items() if k != 'texto'} for source in references])
        return self.start_job(work, answer_stop=control)
