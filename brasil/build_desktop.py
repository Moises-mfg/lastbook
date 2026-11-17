#!/usr/bin/env python3
"""Constrói o aplicativo nativo no próprio sistema de destino."""
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
VERSION='0.4.0-alpha4'

def webview():
    version='1.0.4314.35';target=ROOT/'derived/webview2';target.mkdir(parents=True,exist_ok=True)
    url=f'https://api.nuget.org/v3-flatcontainer/microsoft.web.webview2/{version}/microsoft.web.webview2.{version}.nupkg'
    archive=ROOT/'derived/webview2-sdk.nupkg'
    with urllib.request.urlopen(url,timeout=120) as response,archive.open('wb') as file:shutil.copyfileobj(response,file)
    paths=['lib/net462/Microsoft.Web.WebView2.Core.dll','lib/net462/Microsoft.Web.WebView2.WinForms.dll','runtimes/win-x64/native/WebView2Loader.dll']
    with zipfile.ZipFile(archive) as z:
        for path in paths:(target/Path(path).name).write_bytes(z.read(path))


def main():
    if sys.platform=='win32':webview()
    subprocess.run([sys.executable,'-m','PyInstaller','--noconfirm','--distpath',str(ROOT/'derived/desktop-dist'),'--workpath',str(ROOT/'derived/desktop-build'),str(ROOT/'brasil/desktop.spec')],check=True,cwd=ROOT)
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
