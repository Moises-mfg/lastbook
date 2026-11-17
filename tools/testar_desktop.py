#!/usr/bin/env python3
"""Abre o binário empacotado, espera o autoteste e confere a IA real."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
ROOT=Path(__file__).resolve().parents[1]

def main():
    folder=Path(os.environ.get('RUNNER_TEMP',tempfile.gettempdir()))/'Ultimo Livro teste ação com espaços'
    folder.mkdir(parents=True,exist_ok=True);report=ROOT/'derived/desktop-results/resultado.json';report.parent.mkdir(parents=True,exist_ok=True)
    exe=ROOT/('derived/desktop-dist/O Último Livro.app/Contents/MacOS/UltimoLivro' if sys.platform=='darwin' else 'derived/desktop-dist/UltimoLivro/UltimoLivro.exe')
    env=dict(os.environ,ULTIMO_LIVRO_DATA=str(folder),ULTIMO_LIVRO_TEST_MODEL=str(ROOT/'derived/desktop-model.gguf'))
    process=subprocess.Popen([str(exe),'--autoteste',str(report)],env=env)
    try:code=process.wait(timeout=360)
    except subprocess.TimeoutExpired:
        process.kill();raise RuntimeError('O teste da janela excedeu 360 segundos.')
    if not report.exists():
        log=folder/'aplicativo.log';print(log.read_text(encoding='utf-8',errors='replace')[-15000:] if log.exists() else 'Sem registro de inicialização.');raise RuntimeError('O aplicativo não produziu o relatório.')
    result=json.loads(report.read_text(encoding='utf-8'));print(json.dumps(result,ensure_ascii=False,indent=2))
    if code!=0 or not result.get('ok') or not result.get('ia'):raise RuntimeError('O aplicativo empacotado não passou no teste completo.')
    print('Aplicativo empacotado: janela, Wikipedia, mapas, preferências, checklist e IA local aprovados.')

if __name__=='__main__':main()
