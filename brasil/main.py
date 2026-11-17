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
from engine.setup.api import SetupHandler, _send_json

WEB = Path(__file__).parent / 'web'
STORE = None
PICK_FILE = None
OPEN_RESOURCE = None


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
            return _send_json(self, STORE.state())
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
            if not 0 < size <= 128*1024:
                raise ValueError('Pedido inválido.')
            body = json.loads(self.rfile.read(size))
            if not isinstance(body, dict):
                raise ValueError('Pedido inválido.')
            routes = {'/api/brasil/open-resource':lambda b:OPEN_RESOURCE(b.get('id')), '/api/brasil/map-catalog': STORE.map_catalog_search, '/api/brasil/select-map': STORE.select_map, '/api/brasil/map-search': STORE.search_map, '/api/brasil/install-selected': STORE.install_selected, '/api/brasil/install-package': lambda b: STORE.install_packages([b.get('id')]), '/api/brasil/resume': STORE.resume_install, '/api/brasil/pause': STORE.pause_install, '/api/brasil/import': lambda b: PICK_FILE(b.get('tipo')), '/api/brasil/search-zim': STORE.search_zim, '/api/brasil/article-zim': STORE.article_zim, '/api/brasil/choices': STORE.save_choices, '/api/brasil/check': STORE.check,
                      '/api/brasil/ask': STORE.ask, '/api/brasil/download-model': lambda b: STORE.download_model()}
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
    global STORE, PICK_FILE, OPEN_RESOURCE
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
    def pick_file(kind):
        if kind not in ('zim','mapa','plano'): raise ValueError('Tipo de arquivo inválido.')
        event=threading.Event();out={}
        def choose():
            dialog=Gtk.FileChooserNative.new({'zim':'Abrir enciclopédia ZIM','mapa':'Abrir mapa .ulmap ou MBTiles','plano':'Importar plano JSON'}[kind],shell_linux.SHELL.window,Gtk.FileChooserAction.OPEN,'Abrir','Cancelar')
            try:
                if dialog.run()==Gtk.ResponseType.ACCEPT: out['path']=dialog.get_filename()
            finally: dialog.destroy();event.set()
            return False
        GLib.idle_add(choose)
        if not event.wait(300): raise ValueError('A seleção de arquivo expirou. Tente novamente.')
        if not out.get('path'): return {'cancelado':True}
        return STORE.import_plan(out['path']) if kind=='plano' else STORE.import_file(kind,out['path'])
    PICK_FILE=pick_file
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
