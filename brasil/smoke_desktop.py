"""Autoteste explícito dos binários: dados descartáveis, janela real e IA local.

Ativado somente pela opção de linha de comando --autoteste CAMINHO.
"""
import json
import os
from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile
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
    # O escritor libzim Windows usa caminhos ANSI; o produto só lê ZIM.
    # Criar a amostra em ASCII preserva o teste do leitor na pasta com acentos.
    with tempfile.TemporaryDirectory(prefix='ul-zim-source-') as temporary:
        source=Path(temporary)/'teste.zim'
        with Creator(source).config_indexing(True,'por') as c:c.add_item(Article());c.set_mainpath('Brasil')
        shutil.copyfile(source,book)
    server.STORE.import_file('zim',book)
    path=folder/'teste.ulmap';db=sqlite3.connect(path);mapa_vetor.create(db)
    mapa_vetor.add_feature(db,1,'land','teste','',2,[[(-48.1,-16.1),(-47.9,-16.1),(-47.9,-15.9),(-48.1,-15.9),(-48.1,-16.1)]])
    mapa_vetor.add_feature(db,2,'poi','hospital','Hospital de Teste',12,[[(-48,-16)]])
    mapa_vetor.add_feature(db,3,'road','primary','Avenida Brasil',7,[[(-48.01,-16.01),(-47.99,-15.99)]])
    mapa_vetor.finish(db,{'name':'Mapa de teste','bounds':[-48.02,-16.02,-47.98,-15.98],'attribution':'Dados sintéticos do autoteste'});db.close()
    server.STORE.import_file('mapa',path)


STEPS=[
    ("document.querySelector('#somenteGuias')&&document.querySelector('#resumoPacotes')?.textContent.includes('Mini')&&document.querySelector('#recomendacaoInstalacao')&&document.querySelectorAll('[name=perfil]').length===4&&document.querySelectorAll('[name=wiki]').length===5","document.querySelector('#somenteGuias').click()",'primeira abertura em Minha instalação'),
    ("location.hash==='#biblioteca'&&document.querySelectorAll('[data-guide]').length===5&&document.querySelectorAll('[data-pdf]').length===3","document.querySelector('[data-pdf=offline]').click()",'biblioteca sem baixar'),
    ("document.querySelectorAll('.paginas-pdf img').length===2&&document.querySelector('.paginas-pdf img')?.naturalWidth>0","location.hash='instalacao'",'página do guia PDF incluída no pacote'),
    ("document.querySelector('#escolhas')&&document.querySelector('#modelo')?.value==='sem-ia'","const mapa=document.querySelector('#mapa');mapa.value='municipio';mapa.dispatchEvent(new Event('change',{bubbles:true}));const busca=document.querySelector('#buscaMunicipio');busca.value='Campinas';busca.dispatchEvent(new Event('input'))",'configuração sem IA'),
    ("document.querySelector('[data-city=\\\"3509502\\\"]')","document.querySelector('[data-city=\\\"3509502\\\"]').click();document.querySelector('#escolhas').requestSubmit()",'seleção de município'),
    ("document.querySelector('#status').textContent.includes('Escolhas salvas')","location.hash='enciclopedias'",'preferências persistentes'),
    ("!!document.querySelector('#buscarZim button')&&!document.querySelector('#buscarZim button').disabled","document.querySelector('#termoZim').value='Brasil';document.querySelector('#buscarZim').requestSubmit()",'leitor ZIM'),
    ("document.querySelector('[data-zim]')?.textContent==='Brasil'","document.querySelector('[data-zim]').click()",'busca ZIM'),
    ("document.querySelector('#conteudo h1')?.textContent==='Brasil'&&document.querySelector('.resposta')?.textContent.includes('Brasília')","location.hash='mapas'",'artigo ZIM'),
    ("document.querySelector('#mapaEstado')?.textContent.includes('consulta local')&&(()=>{const c=document.querySelector('#mapaCanvas'),p=c.getContext('2d').getImageData(c.width/2,c.height/2,1,1).data;return p[3]===255&&!(p[0]===216&&p[1]===231&&p[2]===233)})()","document.querySelector('#mapaTermo').value='Hospital';document.querySelector('#mapaBusca').requestSubmit()",'desenho de mapa'),
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
    def ui_value(self,script,timeout=20):
        event=threading.Event();box={}
        def done(value,error):box.update(value=value,error=error);event.set()
        self.later(.01,lambda:self.evaluate(script,done))
        if not event.wait(timeout):raise RuntimeError('A janela não respondeu ao autoteste.')
        if box.get('error'):raise RuntimeError(str(box['error']))
        return box.get('value')
    def wait_ui(self,condition,timeout=30):
        deadline=time.monotonic()+timeout;last=None
        while time.monotonic()<deadline:
            try:
                if self.ui_value('Boolean('+condition+')') is True:return
            except RuntimeError as error:last=error
            time.sleep(.15)
        raise RuntimeError('A interface não confirmou: '+condition+'; '+str(last or 'sem erro de avaliação'))
    def ai(self):
        result={'sistema':sys.platform,'interfaces':self.labels}
        try:
            from .core import Store
            from .plataforma import available_memory
            persisted=Store(self.server.STORE.folder)
            assert persisted.choices()['modelo']=='sem-ia'
            assert next(i for i in persisted.checklist() if i['id']=='luz')['feito']
            available=available_memory();assert available and available>0
            result.update(memoria_disponivel=available,segundos=round(time.monotonic()-self.started,2))
            if model:=os.environ.get('ULTIMO_LIVRO_TEST_MODEL'):
                from . import pacotes
                store=self.server.STORE;target=store.package_path(pacotes.catalog()['qwen3-0.6b']);target.parent.mkdir(parents=True,exist_ok=True)
                try:
                    os.link(model, target)
                except OSError:
                    if sys.platform.startswith('linux'):
                        target.symlink_to(Path(model).resolve())
                    else:
                        shutil.copyfile(model, target)
                # A pergunta precisa atravessar a interface e o transporte local.
                self.ui_value("location.hash='instalacao';true")
                self.wait_ui("document.querySelector('#escolhas')&&document.querySelector('#modelo')")
                self.ui_value("document.querySelector('#status').textContent='';document.querySelector('[name=perfil][value=leve]').click();document.querySelector('#escolhas').requestSubmit();true")
                self.wait_ui("document.querySelector('#status').textContent.includes('Escolhas salvas')")
                self.ui_value("location.hash='ia';true")
                self.wait_ui("document.querySelector('#enviar')&&!document.querySelector('#enviar').disabled")
                self.ui_value("document.querySelector('#texto').value='Qual é a capital do Brasil?';document.querySelector('#pergunta').requestSubmit();true")
                deadline=time.monotonic()+210
                while time.monotonic()<deadline:
                    with store.lock:job=dict(store.job)
                    if job['estado'] not in ('parado','executando','baixando'):break
                    time.sleep(.1)
                assert job['estado']=='concluido',job
                assert 'Brasília' in job['resposta'],job
                assert job['fontes'] and job['fontes'][0]['tipo']=='zim'
                self.wait_ui("document.querySelector('.turno-chat .resposta')?.textContent.includes('Brasília')&&document.querySelector('.referencias-chat button')&&!document.querySelector('#enviar').disabled")
                self.ui_value("document.querySelector('#texto').value='Qual é o nome dela?';document.querySelector('#pergunta').requestSubmit();true")
                self.wait_ui("document.querySelectorAll('.turno-chat').length===2&&document.querySelector('.turno-chat:last-child .resposta')?.textContent.includes('Brasília')", timeout=180)
                assert len(Store(store.folder).chat_history()) == 2
                self.ui_value("location.hash='biblioteca';true")
                self.wait_ui("document.querySelector('[data-pdf]')")
                self.ui_value("location.hash='ia';true")
                self.wait_ui("document.querySelectorAll('.turno-chat').length===2&&document.querySelector('.referencias-chat button')")
                self.ui_value("document.querySelector('.referencias-chat button').click();true")
                self.wait_ui("document.querySelector('#conteudo h1')?.textContent==='Brasil'&&document.querySelector('.resposta')?.textContent.includes('Brasília')")
                self.ui_value("location.hash='biblioteca';true")
                self.wait_ui("!!document.querySelector('#buscaBiblioteca')")
                self.ui_value("document.querySelector('#busca').value='Brasil';document.querySelector('#buscaBiblioteca').requestSubmit();true")
                self.wait_ui("[...document.querySelectorAll('#buscaResultados button')].some(b=>b.textContent.startsWith('Brasil · '))")
                self.ui_value("[...document.querySelectorAll('#buscaResultados button')].find(b=>b.textContent.startsWith('Brasil · ')).click();true")
                self.wait_ui("document.querySelector('#conteudo h1')?.textContent==='Brasil'")
                self.ui_value("document.querySelector('#voltarZim').click();true")
                self.wait_ui("document.querySelector('#busca')?.value==='Brasil'&&document.querySelector('#buscaResultados button')")
                self.ui_value("document.querySelector('#busca').value='Hospital';document.querySelector('#buscaBiblioteca').requestSubmit();true")
                self.wait_ui("[...document.querySelectorAll('#buscaResultados button')].some(b=>b.textContent.startsWith('Hospital de Teste · '))")
                self.ui_value("[...document.querySelectorAll('#buscaResultados button')].find(b=>b.textContent.startsWith('Hospital de Teste · ')).click();true")
                self.wait_ui("document.querySelector('#mapaDetalhe')?.textContent.includes('Hospital de Teste')")
                self.ui_value("location.hash='offline';true")
                self.wait_ui("document.querySelector('#verificarOffline')&&!document.querySelector('#verificarOffline').disabled")
                self.ui_value("document.querySelector('#verificarOffline').click();true")
                self.wait_ui("document.querySelectorAll('#resultadoOffline li').length===4", timeout=115)
                assert {item['estado'] for item in store.job['verificacao_offline']} == {'ok'}, store.job
                self.wait_ui("document.querySelector('#exportarBackup')&&document.querySelector('#restaurarBackup')")
                if backup_path := os.environ.get('ULTIMO_LIVRO_TEST_BACKUP'):
                    self.ui_value("document.querySelector('#incluirChat').checked=true;document.querySelector('#exportarBackup').click();true")
                    self.wait_ui("document.querySelector('#status').textContent.includes('Backup exportado')")
                    saved = json.loads(Path(backup_path).read_text(encoding='utf-8'))
                    assert len(saved['conversas']) == 2 and saved['escolhas']['modelo'] == 'qwen3-0.6b'
                    assert {'id': 'luz', 'feito': True} in saved['checklist']
                    store.check({'id':'luz', 'feito':False})
                    store.clear_chat()
                    self.ui_value("window.confirm=()=>true;document.querySelector('#restaurarBackup').click();true")
                    self.wait_ui("document.querySelector('#status').textContent.includes('Backup restaurado')")
                    assert next(i for i in store.checklist() if i['id']=='luz')['feito']
                    assert len(store.chat_history()) == 2
                    result['backup_offline'] = True
                self.ui_value("location.hash='ia';true")
                self.wait_ui("document.querySelector('#memoriaIA')?.textContent.includes('RAM disponível')&&!document.querySelector('#enviar').disabled")
                self.ui_value("document.querySelector('#texto').value='Explique a história da capital do Brasil em detalhes.';document.querySelector('#pergunta').requestSubmit();true")
                self.wait_ui("document.querySelector('#pararResposta')&&!document.querySelector('#pararResposta').disabled")
                self.ui_value("document.querySelector('#pararResposta').click();true")
                self.wait_ui("document.querySelector('#status').textContent.includes('Resposta interrompida')&&document.querySelector('#texto').value.includes('Explique')")
                assert len(Store(store.folder).chat_history()) == 2
                result.update(busca_offline=True, verificacao_offline=True, ia_interrompivel=True)
                self.ui_value("location.hash='mapas';true")
                self.wait_ui("document.querySelector('#mapaCanvas')&&document.querySelector('#mapaEstado')?.textContent.includes('consulta local')")
                result['ia']=job;result['motor']=str(store.runner());result['ia_pela_interface']=True;result['referencia_abrivel']=True;result['chat_contextual']=True
            # A inferência não pode ter fechado/reiniciado a página.
            def verify_view(value,error):
                if error or value is not True:self.save(False,{'erro':'A interface não permaneceu disponível após a IA.','detalhe':str(error)})
                else:self.save(True,result)
            self.later(.1,lambda:self.evaluate("Boolean(document.querySelector('#mapaCanvas')&&document.querySelector('#mapaEstado')?.textContent.includes('consulta local'))",verify_view))
        except Exception:self.save(False,{**result,'erro':traceback.format_exc()})
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
