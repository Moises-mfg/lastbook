"""Autoteste explícito dos binários: dados descartáveis, janela real e IA local.

Ativado somente pela opção de linha de comando --autoteste CAMINHO.
"""
import json
import os
from pathlib import Path
import shutil
import sqlite3
import sys
import threading
import time
import traceback


def output_path():return Path(sys.argv[sys.argv.index('--autoteste')+1])


def seed(server):
    from libzim.writer import Creator,Item,StringProvider,Hint
    from . import mapa_vetor
    folder=server.STORE.folder
    class Article(Item):
        def get_path(self):return 'Brasil'
        def get_title(self):return 'Brasil'
        def get_mimetype(self):return 'text/html'
        def get_contentprovider(self):return StringProvider('<html><h1>Brasil</h1><p>A capital do Brasil é Brasília.</p></html>')
        def get_hints(self):return {Hint.FRONT_ARTICLE:1}
    book=folder/'teste.zim'
    with Creator(book).config_indexing(True,'por') as c:c.add_item(Article());c.set_mainpath('Brasil')
    server.STORE.import_file('zim',book)
    path=folder/'teste.ulmap';db=sqlite3.connect(path);mapa_vetor.create(db)
    mapa_vetor.add_feature(db,1,'land','teste','',2,[[(-48.1,-16.1),(-47.9,-16.1),(-47.9,-15.9),(-48.1,-15.9),(-48.1,-16.1)]])
    mapa_vetor.add_feature(db,2,'poi','hospital','Hospital de Teste',12,[[(-48,-16)]])
    mapa_vetor.add_feature(db,3,'road','primary','Avenida Brasil',7,[[(-48.01,-16.01),(-47.99,-15.99)]])
    mapa_vetor.finish(db,{'name':'Mapa de teste','bounds':[-48.02,-16.02,-47.98,-15.98],'attribution':'Dados sintéticos do autoteste'});db.close()
    server.STORE.import_file('mapa',path)
    plan=folder/'plano.json';plan.write_text(json.dumps({'versao':1,'perfil':'personalizada','modelo':'sem-ia','wikis':['pt-mini'],'mapa':'municipio','municipios':['3509502'],'estados':['SP']}),encoding='utf-8')
    server.STORE.import_plan(plan)

STEPS=[
    ("document.querySelectorAll('[data-guide]').length===5","location.hash='instalacao'",'biblioteca'),
    ("document.querySelectorAll('[name=perfil]').length===4&&document.querySelectorAll('[name=wiki]').length===5","document.querySelector('#escolhas').requestSubmit()",'quatro perfis e cinco Wikipedias'),
    ("document.querySelector('#status').textContent.includes('Escolhas salvas')","location.hash='enciclopedias'",'preferências persistentes'),
    ("!!document.querySelector('#buscarZim button')&&!document.querySelector('#buscarZim button').disabled","document.querySelector('#termoZim').value='Brasil';document.querySelector('#buscarZim').requestSubmit()",'leitor ZIM'),
    ("document.querySelector('[data-zim]')?.textContent==='Brasil'","document.querySelector('[data-zim]').click()",'busca ZIM'),
    ("document.querySelector('#conteudo h1')?.textContent==='Brasil'&&document.querySelector('.resposta')?.textContent.includes('Brasília')","location.hash='mapas'",'artigo ZIM'),
    ("document.querySelector('#mapaEstado')?.textContent.includes('consulta local')","document.querySelector('#mapaTermo').value='Hospital';document.querySelector('#mapaBusca').requestSubmit()",'desenho de mapa'),
    ("document.querySelector('#mapaResultados button')?.textContent==='Hospital de Teste'","document.querySelector('#mapaResultados button').click();document.querySelector('#mapaMais').click()",'busca no mapa'),
    ("document.querySelector('#mapaEstado')?.textContent.includes('Nível 16')","document.querySelector('[data-map-layer=water]').click();location.hash='compras'",'zoom e camadas'),
    ("document.querySelectorAll('[data-item]').length===10","document.querySelector('[data-item=luz]').click()",'checklist'),
    ("document.querySelector('[data-item=luz]')?.checked===true","location.hash='fontes'",'gravação do checklist'),
    ("document.querySelectorAll('[data-resource]').length===11","document.querySelector('#buscaFonte').value='MeshCore';document.querySelector('#buscaFonte').dispatchEvent(new Event('input'))",'diretório de fontes'),
    ("document.querySelectorAll('[data-resource]').length===1&&document.querySelector('[data-resource]')?.dataset.resource==='meshcore-docs'","location.hash='downloads'",'busca de comunidades'),
    ("document.querySelectorAll('[data-package]').length===10","location.hash='mapas'",'catálogo de downloads e município'),
    ("document.querySelector('#mapaEstado')?.textContent.includes('consulta local')","document.querySelector('#mapaCanvas').scrollIntoView({block:'center'})",'mapa disponível ao retornar'),
]


class Check:
    def __init__(self,server,evaluate,later,finish):
        self.server=server;self.evaluate=evaluate;self.later=later;self.finish=finish;self.index=0;self.attempts=0;self.finished=False;self.labels=[];self.started=time.monotonic()
    def tick(self):
        if self.finished:return
        if self.index==len(STEPS):
            self.finished=True;threading.Thread(target=self.ai,daemon=True).start();return
        condition,action,label=STEPS[self.index]
        def done(value,error):
            if error or value is not True:
                self.attempts+=1
                if self.attempts>80:return self.save(False,{'erro':str(error or 'A condição da janela não foi satisfeita.'),'etapa':label})
                self.later(.3,self.tick);return
            self.labels.append(label);self.index+=1;self.attempts=0
            self.evaluate(action,lambda value,error:self.later(.35,self.tick))
        self.evaluate('Boolean('+condition+')',done)
    def ai(self):
        try:
            from .core import Store
            from .plataforma import available_memory
            persisted=Store(self.server.STORE.folder)
            assert persisted.choices()['modelo']=='sem-ia'
            assert next(i for i in persisted.checklist() if i['id']=='luz')['feito']
            available=available_memory();assert available and available>0
            result={'sistema':sys.platform,'memoria_disponivel':available,'interfaces':self.labels,'segundos':round(time.monotonic()-self.started,2)}
            if model:=os.environ.get('ULTIMO_LIVRO_TEST_MODEL'):
                store=self.server.STORE;store.save_choices({'perfil':'leve'});target=store.package_path(store.model_spec());target.parent.mkdir(parents=True,exist_ok=True)
                try:os.link(model,target)
                except OSError:shutil.copyfile(model,target)
                store.ask({'pergunta':'Qual é a capital do Brasil?'})
                deadline=time.monotonic()+210
                while time.monotonic()<deadline:
                    with store.lock:job=dict(store.job)
                    if job['estado'] not in ('executando','baixando'):break
                    time.sleep(.1)
                assert job['estado']=='concluido',job
                assert 'Brasília' in job['resposta'],job
                assert job['fontes'] and job['fontes'][0]['tipo']=='zim'
                result['ia']=job;result['motor']=str(store.runner())
            self.save(True,result)
        except Exception:self.save(False,{'erro':traceback.format_exc()})
    def save(self,ok,result):
        self.finished=True
        path=output_path();path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps({'ok':ok,**result},ensure_ascii=False,indent=2),encoding='utf-8')
        self.later(.1,lambda:self.finish(path))


def attach_mac(shell,server):
    from PyObjCTools import AppHelper
    import AppKit
    def evaluate(script,done):shell.view.evaluateJavaScript_completionHandler_(script,lambda value,error:done(value,error))
    def finish(path):
        def captured(image,error):
            if image is not None:
                rep=AppKit.NSBitmapImageRep.imageRepWithData_(image.TIFFRepresentation())
                rep.representationUsingType_properties_(AppKit.NSBitmapImageFileTypePNG,{}).writeToFile_atomically_(str(path.with_suffix('.png')),True)
            AppKit.NSApplication.sharedApplication().terminate_(None)
        shell.view.takeSnapshotWithConfiguration_completionHandler_(None,captured)
    shell.br_check=Check(server,evaluate,AppHelper.callLater,finish)
    AppHelper.callLater(3,shell.br_check.tick)


def attach_windows(shell,server):
    n=shell.n;timers=[]
    def later(seconds,function):
        def start():
            timer=n.Forms.Timer();timer.Interval=max(1,int(seconds*1000));timers.append(timer)
            def tick(sender,args):timer.Stop();timer.Dispose();timers.remove(timer);function()
            timer.Tick+=tick;timer.Start()
        shell.ui(start)
    def evaluate(script,done):
        task=shell.core.ExecuteScriptAsync(script)
        def collect():
            if not task.IsCompleted:return later(.02,collect)
            if task.IsFaulted:return done(None,str(task.Exception))
            try:done(json.loads(str(task.Result)),None)
            except Exception as error:done(None,str(error))
        later(.02,collect)
    def finish(path):
        stream=n.IO.FileStream(str(path.with_suffix('.png')),n.IO.FileMode.Create)
        task=shell.core.CapturePreviewAsync(n.Core.CoreWebView2CapturePreviewImageFormat.Png,stream)
        def completed():
            if not task.IsCompleted:return later(.05,completed)
            stream.Dispose();shell.form.Close()
        later(.05,completed)
    shell.br_check=Check(server,evaluate,later,finish)
    later(3,shell.br_check.tick)
