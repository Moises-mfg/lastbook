#!/usr/bin/env python3
"""Executa o pacote, a instalação Windows ou a cópia contida no DMG."""
import argparse
import json
import os
import shutil
from pathlib import Path
import subprocess
import sys
import tempfile
ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--executavel',type=Path);parser.add_argument('--imagem',type=Path);parser.add_argument('--rotulo',choices=('empacotado','instalado','dmg'),default='empacotado');args=parser.parse_args()
    temporary=os.environ.get('RUNNER_TEMP',tempfile.gettempdir())
    # Uma pasta nova por execução evita reaproveitar preferências ou resultados antigos.
    folder=Path(tempfile.mkdtemp(prefix='Ultimo Livro teste ação com espaços-',dir=temporary))
    report=ROOT/f'derived/desktop-results/{args.rotulo}.json';report.parent.mkdir(parents=True,exist_ok=True)
    for old in (report,report.with_suffix('.png')):
        if old.exists():old.unlink()
    exe=args.executavel or ROOT/('derived/desktop-dist/O Último Livro.app/Contents/MacOS/UltimoLivro' if sys.platform=='darwin' else 'derived/desktop-dist/UltimoLivro/UltimoLivro.exe')
    mount=None
    try:
        if args.imagem:
            if sys.platform!='darwin':raise ValueError('O teste de DMG requer macOS.')
            image=args.imagem
            if image.is_dir():
                images=list(image.glob('*.dmg'))
                if len(images)!=1:raise ValueError('Esperado exatamente um DMG para teste.')
                image=images[0]
            mount=Path(tempfile.mkdtemp(prefix='UltimoLivro-imagem-',dir=temporary))
            subprocess.run(['hdiutil','attach','-nobrowse','-readonly','-mountpoint',str(mount),str(image.resolve())],check=True)
            exe=mount/'O Último Livro.app/Contents/MacOS/UltimoLivro'
        env=dict(os.environ,ULTIMO_LIVRO_DATA=str(folder),ULTIMO_LIVRO_TEST_MODEL=str(ROOT/'derived/desktop-model.gguf'))
        process=subprocess.Popen([str(exe),'--autoteste',str(report)],env=env)
        try:code=process.wait(timeout=450)
        except subprocess.TimeoutExpired:
            process.kill();process.wait(timeout=15);raise RuntimeError('O teste da janela excedeu 450 segundos.')
        if not report.exists():
            log=folder/'aplicativo.log';print(log.read_text(encoding='utf-8',errors='replace')[-15000:] if log.exists() else 'Sem registro de inicialização.');raise RuntimeError('O aplicativo não produziu o relatório.')
        result=json.loads(report.read_text(encoding='utf-8'));print(json.dumps(result,ensure_ascii=False,indent=2))
        if code!=0 or not result.get('ok') or not result.get('ia') or not result.get('chat_contextual'):raise RuntimeError('O aplicativo não passou no teste completo.')
        print(args.rotulo+': janela, Wikipedia, mapas, preferências, checklist e IA local aprovados.')
    finally:
        log=folder/'aplicativo.log'
        if log.exists():shutil.copyfile(log,report.with_suffix('.log'))
        if mount:
            result=subprocess.run(['hdiutil','detach',str(mount)],timeout=40)
            if result.returncode:subprocess.run(['hdiutil','detach','-force',str(mount)],check=True,timeout=40)

if __name__=='__main__':main()
