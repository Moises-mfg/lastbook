"""Teste das interações da nossa janela WebKitGTK, com dados descartáveis."""
import json
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
    steps=[
        ("({cards:document.querySelectorAll('[data-guide]').length})",lambda d: d['cards']==5,"location.hash='instalacao'"),
        ("({profiles:document.querySelectorAll('[name=perfil]').length,wikis:document.querySelectorAll('[name=wiki]').length,install:!!document.querySelector('#instalar')})",lambda d:d=={'profiles':4,'wikis':5,'install':True},"document.querySelector('#modelo').value='sem-ia';document.querySelector('#escolhas').requestSubmit()"),
        ("({saved:document.querySelector('#status').textContent.includes('Escolhas salvas')})",lambda d:d['saved'],"location.hash='downloads'"),
        ("({packages:document.querySelectorAll('[data-package]').length})",lambda d:d['packages']==8,"location.hash='ia'"),
        ("({disabled:document.querySelector('#enviar')?.disabled})",lambda d:d['disabled'],"location.hash='compras'"),
        ("({items:document.querySelectorAll('[data-item]').length})",lambda d:d['items']==10,"document.querySelector('[data-item=luz]').click()"),
    ]
    state={'index':0,'attempts':0}
    def tick():
        index=state['index']
        if index>=len(steps):
            from brasil import main
            try:
                assert main.STORE.choices()['modelo']=='sem-ia'
                assert next(i for i in main.STORE.checklist() if i['id']=='luz')['feito']
                result['ok']=True
                print('Janela: biblioteca, perfis, salvar, catálogo, IA desativada e checklist OK',flush=True)
                self.view.get_snapshot(WebKit2.SnapshotRegion.VISIBLE,WebKit2.SnapshotOptions.NONE,None,snapshot,None)
            except Exception as e:print('FALHA:',e,flush=True);app.quit()
            return False
        expression,check,action=steps[index]
        def done(view,task,data):
            try:
                actual=json.loads(view.evaluate_javascript_finish(task).to_string())
                if not check(actual):
                    state['attempts']+=1
                    if state['attempts']>15:raise AssertionError(f'etapa {index}: {actual}')
                    GLib.timeout_add(300,tick);return
                print('Etapa',index,actual,flush=True)
                state['index']+=1;state['attempts']=0
                view.evaluate_javascript(action,-1,None,None,None,None,None)
                GLib.timeout_add(600,tick)
            except Exception as e:print('FALHA:',e,flush=True);app.quit()
        self.view.evaluate_javascript('JSON.stringify('+expression+')',-1,None,None,None,done,None)
        return False
    def snapshot(view,task,data):
        try:view.get_snapshot_finish(task).write_to_png('/tmp/ultimo-livro-app.png')
        except Exception as e:print('Snapshot indisponível:',e,flush=True)
        app.quit()
    GLib.timeout_add_seconds(3,tick)
    GLib.timeout_add_seconds(35,lambda:(app.quit(),False)[1])

shell_linux.Shell.build=build
from brasil import main
main.main()
folder.cleanup()
raise SystemExit(0 if result['ok'] else 1)
