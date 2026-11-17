#!/usr/bin/env python3
"""Aplicativo Linux sem servidor HTTP: reutiliza bridge e shell do LastBook."""
import json
import os
from pathlib import Path
import sys
import urllib.parse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'app'))
from brasil.core import Store
from engine.setup.api import SetupHandler, _send_json

WEB = Path(__file__).parent / 'web'
STORE = None


class Handler(SetupHandler):
    def do_GET(self):
        path = self._path()
        if path in ('/', '/index.html'):
            return self._static(WEB / 'index.html')
        if path.startswith('/ui/'):
            p = (WEB / path[4:]).resolve()
            if WEB.resolve() in p.parents and p.is_file():
                return self._static(p)
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
            if not 0 < size <= 16384:
                raise ValueError('Pedido inválido.')
            body = json.loads(self.rfile.read(size))
            if not isinstance(body, dict):
                raise ValueError('Pedido inválido.')
            routes = {'/api/brasil/choices': STORE.save_choices, '/api/brasil/check': STORE.check,
                      '/api/brasil/ask': STORE.ask, '/api/brasil/download-model': lambda b: STORE.download_model()}
            fn = routes.get(self._path())
            if not fn:
                return _send_json(self, {'error': 'Operação não encontrada.'}, 404)
            return _send_json(self, fn(body))
        except (ValueError, TypeError) as e:
            return _send_json(self, {'error': str(e)}, 400)
        except OSError:
            return _send_json(self, {'error': 'Não foi possível salvar. Verifique o espaço e as permissões da pasta.'}, 500)


def main():
    global STORE
    base = Path(os.environ.get('XDG_DATA_HOME', Path.home() / '.local/share')) / 'ultimo-livro'
    STORE = Store(base)
    if '--diagnostico' in sys.argv:
        print(json.dumps(STORE.state(), ensure_ascii=False, indent=2))
        return
    import bridge
    import shell_linux
    shell_linux.APP_ID = 'br.org.ultimolivro.App'
    shell_linux.APP_TITLE = 'O Último Livro'
    shell_linux.GO = [('Biblioteca', '#biblioteca'), ('Preparação', '#compras'), ('Assistente', '#ia')]
    shell_linux.MEMORY_LIMIT_MB = 768
    if not shell_linux.claim(str(base)):
        return
    cache = Path(os.environ.get('XDG_CACHE_HOME', Path.home() / '.cache')) / 'ultimo-livro'
    module = sys.modules[__name__]
    shell_linux.run(bridge.Bridge(module, 'stream', bridge.ORIGIN_MAC), (str(base / 'webview'), str(cache)))


if __name__ == '__main__':
    main()
