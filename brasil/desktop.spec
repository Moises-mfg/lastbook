# Aplicativos brasileiros autocontidos: Python, leitor ZIM e motor local.
import sys
import json
from pathlib import Path
from PyInstaller.utils.hooks import collect_all,collect_submodules,copy_metadata
ROOT=Path(SPECPATH).parent
MAC=sys.platform=='darwin'
datas=[(str(ROOT/'brasil/web'),'brasil/web'),(str(ROOT/'engine/setup/roots.pem'),'engine/setup'),(str(ROOT/'LICENSE'),'.'),(str(ROOT/'THIRD_PARTY_NOTICES.md'),'.')]
legal=ROOT/'derived/desktop-licenses'
if not (legal/'MANIFESTO.json').is_file():raise ValueError('As licenças/fontes precisam ser coletadas antes do empacotamento.')
datas.append((str(legal),'licenses'))
for package in json.loads((legal/'DISTRIBUICOES-PYTHON.json').read_text(encoding='utf-8')):datas+=copy_metadata(package)
for name in ('pacotes.json','mapas_catalogo.json','regiao_atlas.json','regiao_servicos.json'):datas.append((str(ROOT/'brasil'/name),'brasil'))
binaries=[]
for file in (ROOT/'brasil/runtime').iterdir():
    (binaries if file.suffix in ('.exe','.dll','.dylib') or '.so' in file.name or file.name=='llama-completion' else datas).append((str(file),'brasil/runtime'))
hidden=['bridge','brasil.desktop','brasil.smoke_desktop','brasil.plataforma','libzim.reader','libzim.writer','libzim.search']
d,b,h=collect_all('libzim');datas+=d;binaries+=b;hidden+=h
excludes=['shell_linux','gi','tkinter','pytest','numpy','onnxruntime','tokenizers','pypdfium2']
if MAC:
    hidden+=['shell_macos','PyObjCTools.AppHelper']
    for package in ('objc','CoreFoundation','Foundation','AppKit','WebKit'):hidden+=collect_submodules(package)
    excludes+=['shell_windows','clr','pythonnet']
else:
    hidden+=['shell_windows','clr','clr_loader','pythonnet','_cffi_backend']
    excludes+=['shell_macos','objc']
    for file in (ROOT/'derived/webview2').iterdir():datas.append((str(file),'webview2'))
a=Analysis([str(ROOT/'brasil/launch.py')],pathex=[str(ROOT),str(ROOT/'app')],binaries=binaries,datas=datas,hiddenimports=hidden,excludes=excludes,noarchive=False)
pyz=PYZ(a.pure)
exe=EXE(pyz,a.scripts,[],exclude_binaries=True,name='UltimoLivro',console=False,debug=False,argv_emulation=False,strip=False,upx=False,codesign_identity=None,entitlements_file=None)
coll=COLLECT(exe,a.binaries,a.datas,strip=False,upx=False,name='UltimoLivro')
if MAC:
    app=BUNDLE(coll,name='O Último Livro.app',bundle_identifier='br.org.ultimolivro.App',version='0.4.0',info_plist={'CFBundleDisplayName':'O Último Livro','CFBundleName':'O Último Livro','LSMinimumSystemVersion':'13.3','NSHighResolutionCapable':True,'NSHumanReadableCopyright':'Projeto aberto baseado no LastBook. Consulte LICENSE e THIRD_PARTY_NOTICES.md.'})
