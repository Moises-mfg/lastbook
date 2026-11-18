#!/usr/bin/env python3
"""Constrói o aplicativo nativo no próprio sistema de destino."""
import base64
import hashlib
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import urllib.request
import zipfile
ROOT=Path(__file__).resolve().parents[1]
VERSION='0.4.0-alpha6'

def webview():
    version='1.0.4314.35';target=ROOT/'derived/webview2';target.mkdir(parents=True,exist_ok=True)
    url=f'https://api.nuget.org/v3-flatcontainer/microsoft.web.webview2/{version}/microsoft.web.webview2.{version}.nupkg'
    archive=ROOT/'derived/webview2-sdk.nupkg'
    with urllib.request.urlopen(url,timeout=120) as response,archive.open('wb') as file:shutil.copyfileobj(response,file)
    paths=['lib/net462/Microsoft.Web.WebView2.Core.dll','lib/net462/Microsoft.Web.WebView2.WinForms.dll','runtimes/win-x64/native/WebView2Loader.dll']
    with zipfile.ZipFile(archive) as z:
        for path in paths:(target/Path(path).name).write_bytes(z.read(path))
        (target/'LICENSE.txt').write_bytes(z.read('LICENSE.txt'))
    return {'componente':'Microsoft.Web.WebView2 SDK','versao':version,'url':url,'sha256_pacote':hashlib.sha256(archive.read_bytes()).hexdigest()}


def windows_motor_runtime():
    """O subprocesso precisa do CRT compartilhado ao lado de seu próprio EXE."""
    import pefile
    internal=ROOT/'derived/desktop-dist/UltimoLivro/_internal'
    target=internal/'brasil/runtime'
    def is_crt(name):
        return name.lower().endswith('.dll') and name.lower().startswith(('msvcp140','vcruntime140','concrt140','ucrtbase'))
    files=sorted(file for file in internal.iterdir() if file.is_file() and is_crt(file.name))
    if not files:raise RuntimeError('O empacotamento não coletou o CRT Microsoft do motor.')
    # Usar apenas as dependências oficiais já coletadas pelo PyInstaller,
    # verificadas antes da cópia; não há download de DLL avulsa.
    literals=','.join("'"+str(file).replace("'","''")+"'" for file in files)
    script=("$ErrorActionPreference='Stop'; foreach ($file in @("+literals+")) { "
            "$sig=Get-AuthenticodeSignature -LiteralPath $file; "
            "if ($sig.Status -ne 'Valid' -or $sig.SignerCertificate.Subject -notmatch 'Microsoft Corporation') "
            "{ throw ('CRT sem assinatura Microsoft válida: '+$file) } }")
    subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-EncodedCommand',base64.b64encode(script.encode('utf-16le')).decode('ascii')],check=True)
    for file in files:shutil.copy2(file,target/file.name)
    records=[]
    present={file.name.lower() for file in target.iterdir() if file.is_file()}
    for file in target.iterdir():
        if file.suffix.lower() not in ('.dll','.exe'):continue
        with pefile.PE(str(file),fast_load=True) as pe:
            pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_IMPORT'],pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_DELAY_IMPORT']])
            imports=list(getattr(pe,'DIRECTORY_ENTRY_IMPORT',[]))+list(getattr(pe,'DIRECTORY_ENTRY_DELAY_IMPORT',[]))
            missing={entry.dll.decode('ascii').lower() for entry in imports if is_crt(entry.dll.decode('ascii'))}-present
            if missing:raise RuntimeError(f'CRT ausente ao lado de {file.name}: {sorted(missing)}')
        if is_crt(file.name):
            with pefile.PE(str(file)) as pe:
                fixed=pe.VS_FIXEDFILEINFO[0]
                version='.'.join(str(v) for v in (fixed.FileVersionMS>>16,fixed.FileVersionMS&65535,fixed.FileVersionLS>>16,fixed.FileVersionLS&65535))
            records.append({'arquivo':file.name,'versao':version,'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'origem':'Dependência Microsoft coletada pelo PyInstaller, assinatura Authenticode Microsoft validada antes da cópia.'})
    return {'componente':'Microsoft Visual C++/UCRT redistribuíveis','arquivos':records,'termos':'Termos Microsoft próprios; consulte também Python/PC/crtlicense.txt nos avisos do Python. As permissões MIT/GPL dos outros componentes não relicenciam estes arquivos.','documentacao':'https://learn.microsoft.com/cpp/windows/redistributing-visual-cpp-files'}


def main():
    from coletar_licencas import collect
    sdk=webview() if sys.platform=='win32' else None
    licenses=collect(VERSION)
    if sdk:
        sdk['avisos']=[licenses.put('WebView2-SDK','LICENSE.txt',(ROOT/'derived/webview2/LICENSE.txt').read_bytes())]
        licenses.items.append(sdk)
        runtime=ROOT/'derived/webview-runtime.exe'
        if not runtime.is_file():raise FileNotFoundError('O instalador oficial WebView2 Runtime está ausente.')
        licenses.items.append({'componente':'Microsoft WebView2 Runtime Evergreen standalone','url':'https://go.microsoft.com/fwlink/?linkid=2124701','sha256_instalador':hashlib.sha256(runtime.read_bytes()).hexdigest(),'distribuicao':'Instalador oficial Microsoft inalterado, somente no instalador Windows; termos próprios Microsoft.','documentacao':'https://learn.microsoft.com/microsoft-edge/webview2/concepts/distribution'})
    licenses.finish(VERSION,source_archive=False)
    subprocess.run([sys.executable,'-m','PyInstaller','--noconfirm','--distpath',str(ROOT/'derived/desktop-dist'),'--workpath',str(ROOT/'derived/desktop-build'),str(ROOT/'brasil/desktop.spec')],check=True,cwd=ROOT)
    if sys.platform=='win32':
        licenses.items.append(windows_motor_runtime())
    licenses.finish(VERSION)
    if sys.platform=='win32':shutil.copytree(licenses.directory,ROOT/'derived/desktop-dist/UltimoLivro/_internal/licenses',dirs_exist_ok=True)
    out=ROOT/'derived/desktop-release';out.mkdir(parents=True,exist_ok=True)
    if sys.platform=='darwin':
        app=ROOT/'derived/desktop-dist/O Último Livro.app'
        subprocess.run(['codesign','--force','--deep','--sign','-',str(app)],check=True)
        subprocess.run(['codesign','--verify','--deep','--strict',str(app)],check=True)
        stage=ROOT/'derived/dmg';stage.mkdir(parents=True,exist_ok=True)
        shutil.copytree(app,stage/app.name,dirs_exist_ok=True,symlinks=True)
        applications=stage/'Applications'
        if not applications.exists():applications.symlink_to('/Applications')
        arch='arm64' if platform.machine()=='arm64' else 'x64'
        subprocess.run(['hdiutil','create','-volname','O Último Livro','-srcfolder',str(stage),'-ov','-format','UDZO',str(out/f'ultimo-livro_{VERSION}_macos-{arch}.dmg')],check=True)
    else:
        subprocess.run([r'C:\Program Files (x86)\Inno Setup 6\ISCC.exe',f'/DVersion={VERSION}',str(ROOT/'brasil/windows.iss')],check=True)
        shutil.make_archive(str(out/f'ultimo-livro_{VERSION}_windows-x64-portatil'),'zip',ROOT/'derived/desktop-dist','UltimoLivro')
    sums=[]
    for path in sorted(out.iterdir()):
        if path.is_file() and path.name!='SHA256SUMS':
            with path.open('rb') as file:digest=hashlib.file_digest(file,'sha256').hexdigest()
            sums.append(f'{digest}  {path.name}\n')
    (out/'SHA256SUMS').write_text(''.join(sums),encoding='ascii')

if __name__=='__main__':main()
