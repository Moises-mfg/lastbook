"""Entrada dos aplicativos empacotados, com registro local de falhas."""
import json
import sys
import traceback
from pathlib import Path

def launch():
    try:
        from brasil.plataforma import data_folder
        folder=data_folder();folder.mkdir(parents=True,exist_ok=True)
        if getattr(sys,'frozen',False):
            log=(folder/'aplicativo.log').open('a',encoding='utf-8',buffering=1)
            sys.stdout=sys.stderr=log
        from brasil.main import main
        main()
    except Exception:
        error=traceback.format_exc()
        if '--autoteste' in sys.argv:
            path=Path(sys.argv[sys.argv.index('--autoteste')+1]);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps({'ok':False,'erro':error},ensure_ascii=False),encoding='utf-8')
        else:
            try:
                from brasil.plataforma import data_folder
                (data_folder()/'falha.log').write_text(error,encoding='utf-8')
                if sys.platform=='win32':
                    import ctypes
                    ctypes.windll.user32.MessageBoxW(None,'Não foi possível abrir O Último Livro. Consulte falha.log na pasta de dados.','O Último Livro',0x10)
                elif sys.platform=='darwin':
                    import AppKit
                    alert=AppKit.NSAlert.alloc().init();alert.setMessageText_('O Último Livro');alert.setInformativeText_('Não foi possível abrir. Consulte falha.log na pasta de dados.');alert.runModal()
            except Exception:pass
        raise SystemExit(1)

if __name__=='__main__':launch()
