#!/usr/bin/env python3
"""Aplicativo brasileiro nativo, sem servidor HTTP, para Linux, macOS e Windows."""
import json
import sqlite3
import zlib
import os
from pathlib import Path
import sys
import urllib.parse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'app'))
sys.path.insert(0, str(ROOT / 'lib'))
ABI=f'cp{sys.version_info.major}{sys.version_info.minor}'
sys.path.insert(0,str(ROOT/'lib'/ABI))
sys.path.insert(0,str(ROOT/'brasil/vendor'/ABI))
from brasil.core import Store
from brasil import guias_pdf, preparo_local, regiao
from engine.setup.api import SetupHandler, _send_json

WEB = Path(__file__).parent / 'web'
STORE = None
PICK_FILE = None
OPEN_RESOURCE = None
BACKUP_FILE = None
PREPARO_FILE = None


class Handler(SetupHandler):
    def do_GET(self):
        path = self._path()
        if path in ('/', '/index.html'):
            return self._static(WEB / 'index.html')
        if path.startswith('/ui/'):
            p = (WEB / path[4:]).resolve()
            if WEB.resolve() in p.parents and p.is_file():
                return self._static(p)
        if path == '/api/brasil/mapa':
            try: return _send_json(self,STORE.map_metadata())
            except ValueError as e: return _send_json(self,{'error':str(e)},400)
        if path == '/api/brasil/tile':
            try:
                q=urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query)
                tile=STORE.raster_tile(*(int(q[k][0]) for k in ('z','x','y')))
                if tile is None: return _send_json(self,{'error':'Sem cobertura.'},404)
                data,mime=tile
                self.send_response(200);self.send_header('Content-Type',mime);self.send_header('Content-Length',str(len(data)));self.end_headers()
                if self.command != 'HEAD': self.wfile.write(data)
                return
            except (ValueError,KeyError,IndexError): return _send_json(self,{'error':'Imagem não disponível.'},400)
        if path == '/api/brasil/vector-tile':
            try:
                q=urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query)
                return _send_json(self,STORE.vector_tile(*(int(q[k][0]) for k in ('z','x','y'))))
            except (ValueError,KeyError,IndexError,sqlite3.Error,zlib.error):return _send_json(self,{'error':'Mapa não disponível.'},400)
        if path == '/api/brasil/state':
            state = STORE.state()
            state['guias_pdf'] = guias_pdf.catalog()
            state['hardware']['processadores_logicos'] = os.cpu_count()
            state['backup_disponivel'] = BACKUP_FILE is not None
            return _send_json(self, state)
        if path == '/api/brasil/memory':
            from brasil.plataforma import available_memory
            return _send_json(self, {'ram_disponivel_bytes': available_memory()})
        if path == '/api/brasil/regiao':
            from brasil import regiao_camadas
            ibge = regiao.municipio_ativo(STORE)
            return _send_json(self, {'guias': regiao.GUIAS, 'ibge': ibge,
                                     'camadas': regiao_camadas.listar(STORE, ibge) if ibge else []})
        if path == '/api/brasil/preparo':
            return _send_json(self, preparo_local.dados(STORE))
        if path.startswith('/api/brasil/preparo-foto/'):
            try:
                foto = preparo_local.foto_bytes(STORE, path.rsplit('/', 1)[-1])
            except (ValueError, OSError):
                foto = None
            if foto:
                data, mime = foto
                self.send_response(200)
                self.send_header('Content-Type', mime)
                self.send_header('Content-Length', str(len(data)))
                self.send_header('Cache-Control', 'no-store')
                self.send_header('X-Content-Type-Options', 'nosniff')
                self.end_headers()
                if self.command != 'HEAD':
                    self.wfile.write(data)
                return
            return _send_json(self, {'error': 'Foto não encontrada.'}, 404)
        if path == '/api/brasil/chat':
            return _send_json(self, {'history': STORE.chat_history()})
        if path == '/api/brasil/job':
            with STORE.lock:
                return _send_json(self, dict(STORE.job))
        return _send_json(self, {'error': 'Página não encontrada.'}, 404)

    do_HEAD = do_GET

    def do_POST(self):
        if self.client_address[0] != '127.0.0.1':
            return _send_json(self, {'error': 'Acesso somente neste computador.'}, 403)
        try:
            size = int(self.headers.get('Content-Length', '0'))
            limit = 2*1024*1024 if self._path() == '/api/brasil/preparo-exportar-mapa' else 128*1024
            if not 0 < size <= limit:
                raise ValueError('Pedido inválido.')
            body = json.loads(self.rfile.read(size))
            if not isinstance(body, dict):
                raise ValueError('Pedido inválido.')
            routes = {'/api/brasil/open-resource':lambda b:OPEN_RESOURCE(b.get('id')), '/api/brasil/map-catalog': STORE.map_catalog_search, '/api/brasil/select-map': STORE.select_map, '/api/brasil/map-search': STORE.search_map, '/api/brasil/install-selected': STORE.install_selected, '/api/brasil/install-package': lambda b: STORE.install_packages([b.get('id')]), '/api/brasil/resume': STORE.resume_install, '/api/brasil/pause': STORE.pause_install, '/api/brasil/import': lambda b: PICK_FILE(b.get('tipo')), '/api/brasil/search-zim': STORE.search_zim, '/api/brasil/article-zim': STORE.article_zim, '/api/brasil/choices': STORE.save_choices, '/api/brasil/check': STORE.check,
                      '/api/brasil/ask': STORE.ask, '/api/brasil/clear-chat': lambda b: STORE.clear_chat(),
                      '/api/brasil/open-pdf': lambda b: guias_pdf.open_pdf(b.get('id')),
                      '/api/brasil/download-model': lambda b: STORE.download_model()}
            routes['/api/brasil/install-preview'] = STORE.preview_install
            routes['/api/brasil/stop-answer'] = lambda b: STORE.stop_answer()
            if self._path() == '/api/brasil/search-offline':
                from brasil.busca_offline import search
                return _send_json(self, search(STORE, body))
            if self._path() == '/api/brasil/check-offline':
                from brasil.verificar_offline import check
                return _send_json(self, STORE.start_job(lambda: check(STORE)))
            if self._path() == '/api/brasil/backup':
                if BACKUP_FILE is None:
                    raise ValueError('O seletor de arquivos para backup está indisponível.')
                return _send_json(self, BACKUP_FILE(body))
            if self._path() == '/api/brasil/preparo':
                return _send_json(self, preparo_local.salvar(STORE, body))
            if self._path() == '/api/brasil/map-at':
                return _send_json(self, STORE.map_at(body))
            if self._path() == '/api/brasil/regiao-municipio':
                from brasil import regiao_camadas, regiao_dados
                ibge = body.get('ibge')
                municipio = regiao.selecionar_municipio(STORE, ibge)
                return _send_json(self, {'municipio': municipio, 'historico': regiao_dados.historico(ibge),
                                         'servicos': regiao.servicos_catalogados(ibge),
                                         'camadas': regiao_camadas.listar(STORE, ibge)})
            if self._path() == '/api/brasil/regiao-excluir':
                from brasil import regiao_camadas
                return _send_json(self, regiao_camadas.excluir(STORE, body))
            if self._path() == '/api/brasil/regiao-importar':
                from brasil import regiao_camadas
                if PREPARO_FILE is None:
                    raise ValueError('O seletor de arquivos está indisponível.')
                path = PREPARO_FILE('Importar camada GeoJSON', False, 'camada.geojson')
                return _send_json(self, regiao_camadas.importar(STORE, body, path))
            if self._path() == '/api/brasil/preparo-exportar-mapa':
                from brasil.regiao_mapa import exportar_recorte
                if PREPARO_FILE is None:
                    raise ValueError('O seletor de arquivos está indisponível.')
                path = PREPARO_FILE('Salvar recorte para impressão', True, 'mapa-offline.html')
                if not path:
                    return _send_json(self, {'cancelado': True})
                return _send_json(self, exportar_recorte(STORE, body, path))
            if self._path() in ('/api/brasil/preparo-exportar', '/api/brasil/preparo-foto'):
                if PREPARO_FILE is None:
                    raise ValueError('O seletor de arquivos está indisponível.')
                exportar = self._path().endswith('-exportar')
                path = PREPARO_FILE('Exportar plano familiar' if exportar else 'Adicionar foto',
                                    exportar, 'plano-familiar.html' if exportar else None)
                if not path:
                    return _send_json(self, {'cancelado': True})
                if exportar:
                    return _send_json(self, preparo_local.exportar_plano(STORE, body, path))
                return _send_json(self, preparo_local.adicionar_foto(STORE, body.get('id'), path))
            fn = routes.get(self._path())
            if not fn:
                return _send_json(self, {'error': 'Operação não encontrada.'}, 404)
            return _send_json(self, fn(body))
        except (ValueError, TypeError) as e:
            return _send_json(self, {'error': str(e)}, 400)
        except (sqlite3.Error,zlib.error):
            return _send_json(self, {'error':'Não foi possível ler o arquivo local. Confira o mapa ou importe outra cópia.'},400)
        except OSError:
            return _send_json(self, {'error': 'Não foi possível salvar. Verifique o espaço e as permissões da pasta.'}, 500)


def main():
    global STORE, PICK_FILE, OPEN_RESOURCE, BACKUP_FILE, PREPARO_FILE
    from brasil.plataforma import data_folder
    base=data_folder()
    STORE = Store(base)
    if '--diagnostico' in sys.argv:
        print(json.dumps(STORE.state(), ensure_ascii=False, indent=2))
        return
    import bridge
    if sys.platform in ('darwin','win32'):
        from brasil.desktop import run
        return run(sys.modules[__name__],base)
    import shell_linux
    import threading
    from gi.repository import GLib, Gtk
    def choose_path(title, save=False, filename='ultimo-livro-backup.json'):
        event = threading.Event()
        out = {}

        def choose():
            action = Gtk.FileChooserAction.SAVE if save else Gtk.FileChooserAction.OPEN
            dialog = Gtk.FileChooserNative.new(title, shell_linux.SHELL.window,
                                               action, 'Salvar' if save else 'Abrir', 'Cancelar')
            if save:
                dialog.set_current_name(filename)
                dialog.set_do_overwrite_confirmation(True)
            try:
                if dialog.run() == Gtk.ResponseType.ACCEPT:
                    out['path'] = dialog.get_filename()
            finally:
                dialog.destroy()
                event.set()
            return False

        GLib.idle_add(choose)
        if not event.wait(300):
            raise ValueError('A seleção de arquivo expirou. Tente novamente.')
        return out.get('path')

    def pick_file(kind):
        titles = {'zim': 'Abrir enciclopédia ZIM', 'mapa': 'Abrir mapa .ulmap ou MBTiles',
                  'plano': 'Importar plano JSON'}
        if kind not in titles:
            raise ValueError('Tipo de arquivo inválido.')
        path = choose_path(titles[kind])
        if not path:
            return {'cancelado': True}
        return STORE.import_plan(path) if kind == 'plano' else STORE.import_file(kind, path)

    from brasil.backup import transfer
    PICK_FILE = pick_file
    PREPARO_FILE = choose_path
    BACKUP_FILE = lambda body: transfer(STORE, body, choose_path)
    def open_resource(ident):
        from brasil.fontes import resource_url
        url=resource_url(ident);event=threading.Event();result={}
        def launch():
            try:Gtk.show_uri_on_window(shell_linux.SHELL.window,url,0)
            except GLib.Error:result['error']=True
            finally:event.set()
            return False
        GLib.idle_add(launch)
        if not event.wait(15) or result.get('error'):raise ValueError('Não foi possível abrir o navegador. Copie o endereço exibido.')
        return {'mensagem':'Endereço enviado ao navegador. A página externa precisa de conexão.'}
    OPEN_RESOURCE=open_resource
    original_quit = shell_linux.quit_app
    def quit_app():
        STORE.close()
        original_quit()
    shell_linux.quit_app = quit_app
    shell_linux.APP_ID = 'br.org.ultimolivro.App'
    shell_linux.APP_TITLE = 'O Último Livro'
    shell_linux.STOPPED = 'Uma página parou de funcionar e foi fechada.'
    shell_linux.TOO_BIG = 'Uma página usou memória demais e foi fechada.'
    shell_linux.NO_NETWORK_REFUSED = 'Não foi possível isolar a janela da rede. Reinicie o aplicativo.'
    shell_linux.ALREADY_OPEN = 'O Último Livro já está aberto.'
    shell_linux.GO = [('Biblioteca', '#biblioteca'), ('Preparação', '#compras'), ('Assistente', '#ia')]
    def header(self):
        from gi.repository import Gtk
        return Gtk.HeaderBar(title='O Último Livro', subtitle='Edição brasileira · alpha', show_close_button=True)
    shell_linux.Shell.header = header
    shell_linux.MEMORY_LIMIT_MB = 768
    if not shell_linux.claim(str(base)):
        return
    cache = Path(os.environ.get('XDG_CACHE_HOME', Path.home() / '.cache')) / 'ultimo-livro'
    module = sys.modules[__name__]
    shell_linux.run(bridge.Bridge(module, 'stream', bridge.ORIGIN_MAC), (str(base / 'webview'), str(cache)))


if __name__ == '__main__':
    main()
