"""Pastas e recursos do computador, usando os mecanismos de cada sistema."""
import ctypes
import os
from pathlib import Path
import re
import subprocess
import sys
from engine.setup import hardware


def data_folder():
    if value:=os.environ.get('ULTIMO_LIVRO_DATA'):return Path(value)
    if sys.platform=='win32':return Path(os.environ.get('LOCALAPPDATA') or Path.home()/'AppData/Local')/'UltimoLivro'
    if sys.platform=='darwin':return Path.home()/'Library/Application Support/UltimoLivro'
    return Path(os.environ.get('XDG_DATA_HOME') or Path.home()/'.local/share')/'ultimo-livro'


def available_memory():
    if sys.platform=='win32':
        state=hardware._MemoryStatus();state.dwLength=ctypes.sizeof(state)
        return int(state.ullAvailPhys) if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(state)) else None
    if sys.platform=='darwin':
        try:
            text=subprocess.check_output(['/usr/bin/vm_stat'],text=True,timeout=10)
            page=int(re.search(r'page size of (\d+)',text).group(1))
            counts=dict((k.strip(),int(v)) for k,v in re.findall(r'^([^:\n]+):\s+(\d+)\.',text,re.M))
            return page*sum(counts.get(k,0) for k in ('Pages free','Pages inactive','Pages speculative'))
        except (OSError,ValueError,AttributeError,subprocess.SubprocessError):return None
    try:
        for line in Path('/proc/meminfo').read_text().splitlines():
            if line.startswith('MemAvailable:'):return int(line.split()[1])*1024
    except (OSError,ValueError):pass
    return None


def subprocess_options():
    return {'creationflags':subprocess.CREATE_NO_WINDOW} if sys.platform=='win32' else {}
