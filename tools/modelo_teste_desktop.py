#!/usr/bin/env python3
"""Download explícito do modelo usado somente pelo teste de mantenedor/CI."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from brasil import pacotes
from engine.setup.download import Control
if __name__=='__main__':
    target=ROOT/'derived/desktop-model.gguf';last=[-1]
    def progress(done,total,phase):
        percent=int(done/max(1,total)*100)//10*10
        if percent!=last[0]:print(phase,percent,'%',flush=True);last[0]=percent
    pacotes.obtain(pacotes.catalog()['qwen3-0.6b'],target,Control(),progress)
