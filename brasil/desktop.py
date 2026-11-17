"""Integração nativa com macOS/WebKit e Windows/WebView2."""
import json
import os
from pathlib import Path
import sys
import threading
import webbrowser
from .fontes import resource_url

TITLE='O Último Livro'


def run(server,base):
    if sys.platform=='darwin':return run_mac(server,base)
    return run_windows(server,base)


def finish_import(server,kind,path):
    if not path:return {'cancelado':True}
    return server.STORE.import_plan(path) if kind=='plano' else server.STORE.import_file(kind,path)


def run_mac(server,base):
    import bridge
    import shell_macos as shell
    import AppKit,Foundation
    from PyObjCTools import AppHelper
    shell.STOPPED='Uma página parou de funcionar e foi fechada.'
    shell.TOO_BIG='Uma página usou memória demais e foi fechada.'
    shell.STUCK='Uma página parou de responder e foi fechada.'
    shell.NO_NETWORK_REFUSED='Não foi possível isolar a janela da rede. Reinicie o aplicativo.'
    current={}
    def on_ui(function,timeout=300):
        event=threading.Event();result={}
        def call():
            try:result['value']=function()
            except Exception as e:result['error']=e
            finally:event.set()
        AppHelper.callAfter(call)
        if not event.wait(timeout):raise ValueError('A operação expirou. Tente novamente.')
        if 'error' in result:raise ValueError('Não foi possível concluir a operação no macOS.') from result['error']
        return result.get('value')
    def pick(kind):
        if kind not in ('zim','mapa','plano'):raise ValueError('Tipo de arquivo inválido.')
        def choose():
            panel=AppKit.NSOpenPanel.openPanel();panel.setCanChooseDirectories_(False);panel.setCanChooseFiles_(True);panel.setAllowsMultipleSelection_(False)
            panel.setTitle_({'zim':'Abrir enciclopédia ZIM','mapa':'Abrir mapa local','plano':'Importar plano JSON'}[kind]);panel.setPrompt_('Abrir')
            return str(panel.URL().path()) if panel.runModal()==AppKit.NSModalResponseOK else None
        return finish_import(server,kind,on_ui(choose))
    server.PICK_FILE=pick
    def external(ident):
        url=resource_url(ident)
        if not on_ui(lambda:AppKit.NSWorkspace.sharedWorkspace().openURL_(Foundation.NSURL.URLWithString_(url)),15):raise ValueError('Não foi possível abrir o navegador.')
        return {'mensagem':'Endereço aberto no navegador. A página externa precisa de conexão.'}
    server.OPEN_RESOURCE=external
    original_build=shell.Shell.build
    def build(self):
        current['shell']=self;original_build(self);self.window.setTitle_(TITLE)
        if '--autoteste' in sys.argv:
            from .smoke_desktop import attach_mac
            attach_mac(self,server)
    shell.Shell.build=build
    # O menu original contém rotas e atualizações do LastBook, não desta edição.
    def menu(app,go=None):
        bar=AppKit.NSMenu.alloc().init()
        for name,items in [(TITLE,[(f'Sobre {TITLE}','orderFrontStandardAboutPanel:',''),('Sair','terminate:','q')]),('Editar',[('Desfazer','undo:','z'),('Refazer','redo:','Z'),('Recortar','cut:','x'),('Copiar','copy:','c'),('Colar','paste:','v'),('Selecionar tudo','selectAll:','a')]),('Janela',[('Minimizar','performMiniaturize:','m'),('Fechar','performClose:','w')])]:bar.addItem_(shell._menu(name,items))
        app.setMainMenu_(bar)
    shell.install_menu=menu
    original_terminate=shell.AppDelegate.applicationWillTerminate_
    def terminate(self,note):server.STORE.close();original_terminate(self,note)
    shell.AppDelegate.applicationWillTerminate_=terminate
    if '--autoteste' in sys.argv:
        from .smoke_desktop import seed
        seed(server)
    shell.run(bridge.Bridge(server,'stream',bridge.ORIGIN_MAC))


def run_windows(server,base):
    import shell_windows as shell
    shell.TITLE=TITLE
    shell.NO_RUNTIME='O aplicativo precisa do Microsoft Edge WebView2 Runtime. Execute novamente o instalador para incluir esse componente.'
    shell.TOO_BIG='Uma página usou memória demais e foi fechada.'
    failure=shell.preflight()
    if failure:raise RuntimeError(failure)
    current={}
    def on_ui(function,timeout=300):
        event=threading.Event();result={}
        def call():
            try:result['value']=function()
            except Exception as e:result['error']=e
            finally:event.set()
        if not current['shell'].ui(call) or not event.wait(timeout):raise ValueError('A operação expirou. Tente novamente.')
        if 'error' in result:raise ValueError('Não foi possível concluir a operação no Windows.') from result['error']
        return result.get('value')
    def pick(kind):
        if kind not in ('zim','mapa','plano'):raise ValueError('Tipo de arquivo inválido.')
        def choose():
            dialog=shell.net().Forms.OpenFileDialog();dialog.Title={'zim':'Abrir enciclopédia ZIM','mapa':'Abrir mapa local','plano':'Importar plano JSON'}[kind]
            dialog.Filter={'zim':'Enciclopédia ZIM|*.zim','mapa':'Mapa offline|*.ulmap;*.mbtiles','plano':'Plano JSON|*.json'}[kind];dialog.Multiselect=False
            try:return str(dialog.FileName) if dialog.ShowDialog(current['shell'].form)==shell.net().Forms.DialogResult.OK else None
            finally:dialog.Dispose()
        return finish_import(server,kind,on_ui(choose))
    server.PICK_FILE=pick
    def external(ident):
        os.startfile(resource_url(ident))
        return {'mensagem':'Endereço aberto no navegador. A página externa precisa de conexão.'}
    server.OPEN_RESOURCE=external
    original_build=shell.Shell.build
    def build(self):
        current['shell']=self
        original_build(self)
    shell.Shell.build=build
    original_ready=shell.Shell.on_ready
    def ready(self,sender,args):
        original_ready(self,sender,args)
        if '--autoteste' in sys.argv:
            from .smoke_desktop import attach_windows
            attach_windows(self,server)
        self.form.FormClosing+=lambda sender,event:server.STORE.close()
    shell.Shell.on_ready=ready
    # O desenho de faixa do produto original pressupõe um cabeçalho que não existe aqui.
    shell.band_ok=lambda:False
    if '--autoteste' in sys.argv:
        from .smoke_desktop import seed
        seed(server)
    shell.run(server,str(base))
