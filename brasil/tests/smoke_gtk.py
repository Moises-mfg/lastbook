"""Teste da nossa janela WebKitGTK, com dados descartáveis e sem servidor HTTP."""
import os
from pathlib import Path
import sys
import tempfile

ROOT = Path(os.environ.get('ULTIMO_LIVRO_TEST_ROOT') or Path(__file__).resolve().parents[2])
sys.path[:0] = [str(ROOT), str(ROOT/'app')]
import gi
gi.require_version('Gtk','3.0')
gi.require_version('WebKit2','4.1')
from gi.repository import GLib, WebKit2
import shell_linux

folder=tempfile.TemporaryDirectory(prefix='ultimo-livro-gtk-')
os.environ['XDG_DATA_HOME']=folder.name
os.environ['XDG_CACHE_HOME']=folder.name
shell_linux.quit_app=lambda: None
original=shell_linux.Shell.build
result={'ok':False}

def build(self, app):
    original(self,app)
    def inspect():
        js="""JSON.stringify({title: document.querySelector('h1')?.textContent, cards:document.querySelectorAll('[data-guide]').length})"""
        def done(view, task, data):
            try:
                value=view.evaluate_javascript_finish(task).to_string()
                print(value,flush=True)
                import json
                d=json.loads(value)
                assert d['cards']==5, d
                assert 'essencial' in d['title'],d
                result['ok']=True
                view.get_snapshot(WebKit2.SnapshotRegion.VISIBLE, WebKit2.SnapshotOptions.NONE, None, snapshot, None)
            except Exception as e:
                print('FALHA:',e,flush=True);app.quit()
        self.view.evaluate_javascript(js,-1,None,None,None,done,None)
        return False
    def snapshot(view, task, data):
        try:
            image=view.get_snapshot_finish(task)
            image.write_to_png('/tmp/ultimo-livro-app.png')
            print('Snapshot: /tmp/ultimo-livro-app.png',flush=True)
        except Exception as e: print('Snapshot indisponível:',e,flush=True)
        app.quit()
    GLib.timeout_add_seconds(6,inspect)
    GLib.timeout_add_seconds(20,lambda:(app.quit(),False)[1])

shell_linux.Shell.build=build
from brasil import main
main.main()
folder.cleanup()
raise SystemExit(0 if result['ok'] else 1)
