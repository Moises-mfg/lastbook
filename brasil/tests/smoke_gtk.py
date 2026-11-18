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
    from brasil import main,mapa_vetor
    import sqlite3
    sample=Path(folder.name)/'teste.ulmap';db=sqlite3.connect(sample);mapa_vetor.create(db)
    mapa_vetor.add_feature(db,1,'land','teste','',2,[[(-48.2,-16.2),(-47.8,-16.2),(-47.8,-15.8),(-48.2,-15.8),(-48.2,-16.2)]])
    mapa_vetor.add_feature(db,2,'road','primary','Avenida Brasil',7,[[(-48.01,-16.01),(-47.99,-15.99)]])
    mapa_vetor.add_feature(db,3,'poi','hospital','Hospital de Teste',12,[[(-48,-16)]])
    mapa_vetor.finish(db,{'name':'Mapa de teste','bounds':[-48.02,-16.02,-47.98,-15.98],'attribution':'Dados sintéticos de teste'});db.close()
    actual=os.environ.get('ULTIMO_LIVRO_TEST_MAP')
    main.STORE.import_file('mapa',Path(actual) if actual else sample)
    actual_zim=os.environ.get('ULTIMO_LIVRO_TEST_ZIM')
    if actual_zim:book=Path(actual_zim)
    else:
        from libzim.writer import Creator,Item,StringProvider,Hint
        class TestArticle(Item):
            def get_path(self):return 'Brasil'
            def get_title(self):return 'Brasil'
            def get_mimetype(self):return 'text/html'
            def get_contentprovider(self):return StringProvider('<html><h1>Brasil</h1><p>Brasília é a capital do Brasil. Artigo de teste do leitor.</p></html>')
            def get_hints(self):return {Hint.FRONT_ARTICLE:1}
        book=Path(folder.name)/'teste.zim'
        with Creator(book).config_indexing(True,'por') as creator:creator.add_item(TestArticle());creator.set_mainpath('Brasil')
    main.STORE.import_file('zim',book)
    from base64 import b64decode
    photo = Path(folder.name)/'teste.png'
    photo.write_bytes(b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jhG0AAAAASUVORK5CYII='))
    def escolher_exportacao(title, saving, filename):
        if not saving and title == 'Adicionar foto':
            return photo
        assert saving and filename in ('plano-familiar.html', 'mapa-offline.html')
        return Path(folder.name)/filename
    main.PREPARO_FILE = escolher_exportacao
    search='Campinas' if actual else 'Hospital'
    place='Campinas' if actual else 'Hospital de Teste'
    zoom='Nível 13' if actual else 'Nível 16'
    steps=[
        ("({first:!!document.querySelector('#somenteGuias')})",lambda d:d['first'],"true"),
        ("({profiles:document.querySelectorAll('[name=perfil]').length,wikis:document.querySelectorAll('[name=wiki]').length,install:!!document.querySelector('#instalar')})",lambda d:d=={'profiles':4,'wikis':5,'install':True},"document.querySelector('#modelo').value='sem-ia';document.querySelector('#escolhas').requestSubmit()"),
        ("({saved:document.querySelector('#status').textContent.includes('Escolhas salvas')})",lambda d:d['saved'],"location.hash='downloads'"),
        ("({packages:document.querySelectorAll('[data-package]').length})",lambda d:d['packages']>=8,"location.hash='ia'"),
        ("({disabled:document.querySelector('#enviar')?.disabled})",lambda d:d['disabled'],"location.hash='compras'"),
        ("({items:document.querySelectorAll('[data-item]').length})",lambda d:d['items']==10,"document.querySelector('[data-item=luz]').click()"),
        ("({checked:document.querySelector('[data-item=luz]')?.checked})",lambda d:d['checked'],"location.hash='mapas'"),
        ("({canvas:!!document.querySelector('#mapaCanvas'),local:document.querySelector('#mapaEstado')?.textContent})",lambda d:d['canvas'] and 'consulta local' in (d['local'] or ''),f"document.querySelector('#mapaTermo').value={json.dumps(search)};document.querySelector('#mapaBusca').requestSubmit()"),
        ("({place:document.querySelector('#mapaResultados button')?.textContent})",lambda d:d['place']==place,"document.querySelector('#mapaResultados button').click();document.querySelector('#mapaMais').click()"),
        ("({zoom:document.querySelector('#mapaEstado')?.textContent})",lambda d:zoom in (d['zoom'] or ''),"document.querySelector('[data-map-layer=water]').click();document.querySelector('#mapaCanvas').scrollIntoView({block:'center'})"),
        ("({local:document.querySelector('#mapaEstado')?.textContent})",lambda d:'consulta local' in (d['local'] or ''),"location.hash='fontes'"),
        ("({sources:document.querySelectorAll('[data-resource]').length})",lambda d:d['sources']==11,"document.querySelector('#categoriaFonte').value='LoRa e redes mesh';document.querySelector('#categoriaFonte').dispatchEvent(new Event('change'));document.querySelector('#buscaFonte').value='MeshCore';document.querySelector('#buscaFonte').dispatchEvent(new Event('input'))"),
        ("({source:document.querySelector('[data-resource]')?.dataset.resource})",lambda d:d['source']=='meshcore-docs',"location.hash='enciclopedias'"),
        ("({ready:!!document.querySelector('#buscarZim button')&&!document.querySelector('#buscarZim button').disabled})",lambda d:d['ready'],"document.querySelector('#termoZim').value='Brasil';document.querySelector('#buscarZim').requestSubmit()"),
        ("({title:document.querySelector('[data-zim]')?.textContent})",lambda d:d['title']=='Brasil',"document.querySelector('[data-zim]').click()"),
        ("({title:document.querySelector('#conteudo h1')?.textContent,contains:document.querySelector('.resposta')?.textContent.includes('Brasília')})",lambda d:d['title']=='Brasil' and d['contains'],"location.hash='plano-familiar'"),
        ("({loaded:!!document.querySelector('#preparo-form')})",lambda d:d['loaded'],"document.querySelector('[name=encontro1]').value='Ponto de teste';document.querySelector('[name=contato]').value='Contato reservado';document.querySelector('#preparo-form').requestSubmit()"),
        ("({saved:document.querySelector('#status').textContent.includes('salvo')})",lambda d:d['saved'],"document.querySelector('[name=campos][value=encontro1]').click();document.querySelector('#preparo-exportar').requestSubmit()"),
        ("({exported:document.querySelector('#status').textContent.includes('exportado')})",lambda d:d['exported'],"location.hash='rapido'"),
        ("({actions:document.querySelectorAll('.preparo-quatro article').length,plan:document.querySelector('.preparo-quatro')?.textContent.includes('Ponto de teste')})",lambda d:d['actions']==4 and d['plan'],"document.querySelector('[data-ensaio=plano]').click();location.hash='regiao'"),
        ("({alerts:document.querySelector('#regiao-page')?.textContent.includes('40199')})",lambda d:d['alerts'],"document.querySelector('#regiao-termo').value='Itajaí';document.querySelector('#regiao-busca').requestSubmit()"),
        ("({city:document.querySelector('#regiao-resultados button')?.textContent})",lambda d:'Itajaí' in (d['city'] or ''),"document.querySelector('#regiao-resultados button').click()"),
        ("({history:document.querySelector('#regiao-detalhe')?.textContent.includes('registros')})",lambda d:d['history'],"location.hash='recuperacao'"),
        ("({ready:!!document.querySelector('#preparo-form [name=descricao]')})",lambda d:d['ready'],"document.querySelector('[name=descricao]').value='Registro de teste';document.querySelector('#preparo-form').requestSubmit()"),
        ("({record:!!document.querySelector('[data-photo]')})",lambda d:d['record'],"document.querySelector('[data-photo]').click()"),
        ("({photo:document.querySelector('.preparo-fotos img')?.naturalWidth})",lambda d:d['photo']==1,"location.hash='mapas'"),
        ("({local:document.querySelector('#mapaEstado')?.textContent})",lambda d:'consulta local' in (d['local'] or ''),"document.querySelector('#mapaExportar').click()"),
        ("({crop:document.querySelector('#status').textContent.includes('Recorte salvo')})",lambda d:d['crop'],"location.hash='rapido'"),
        ("({rehearsed:document.querySelector('#ensaio-status')?.textContent.includes('1 de 4')})",lambda d:d['rehearsed'],"true"),
    ]
    state={'index':0,'attempts':0}
    def tick():
        index=state['index']
        if index>=len(steps):
            from brasil import main
            try:
                assert main.STORE.choices()['modelo']=='sem-ia'
                assert next(i for i in main.STORE.checklist() if i['id']=='luz')['feito']
                plan = (Path(folder.name)/'plano-familiar.html').read_text(encoding='utf-8')
                assert 'Ponto de teste' in plan and 'Contato reservado' not in plan
                assert 'data:image/jpeg;base64,' in (Path(folder.name)/'mapa-offline.html').read_text(encoding='utf-8')
                result['ok']=True
                print('Janela: biblioteca, perfis, catálogo, checklist, mapas, ZIM, plano familiar, acesso rápido, região e recuperação OK',flush=True)
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
    GLib.timeout_add_seconds(50,lambda:(app.quit(),False)[1])

shell_linux.Shell.build=build
from brasil import main
main.main()
folder.cleanup()
raise SystemExit(0 if result['ok'] else 1)
