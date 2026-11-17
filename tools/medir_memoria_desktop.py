#!/usr/bin/env python3
"""Mede uma inferência real do motor empacotado, sem alterar reservas do produto.

O pico é RSS/working set do processo do motor, não o consumo de todo o aplicativo
nem uma recomendação de memória mínima. Execute em um processo Python novo.
"""
import argparse
import ctypes
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
PROMPT = (
    '<|im_start|>system\nResponda em português brasileiro, de forma breve, '
    'usando apenas a fonte fornecida. Não explique seu raciocínio.<|im_end|>\n'
    '<|im_start|>user\nFONTE: A capital do Brasil é Brasília.\n'
    'PERGUNTA: Qual é a capital do Brasil?\n/no_think<|im_end|>\n'
    '<|im_start|>assistant\n<think>\n\n</think>\n\n'
)


class WindowsPeak:
    """Mantém um handle válido, inclusive na última leitura após a saída."""

    def __init__(self, pid):
        from ctypes import wintypes as w

        class Counters(ctypes.Structure):
            _fields_ = [('cb', w.DWORD), ('PageFaultCount', w.DWORD)] + [
                (name, ctypes.c_size_t) for name in (
                    'PeakWorkingSetSize', 'WorkingSetSize',
                    'QuotaPeakPagedPoolUsage', 'QuotaPagedPoolUsage',
                    'QuotaPeakNonPagedPoolUsage', 'QuotaNonPagedPoolUsage',
                    'PagefileUsage', 'PeakPagefileUsage',
                )
            ]

        self.counters = Counters()
        self.counters.cb = ctypes.sizeof(self.counters)
        self.kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        self.psapi = ctypes.WinDLL('psapi', use_last_error=True)
        self.kernel.OpenProcess.argtypes = (w.DWORD, w.BOOL, w.DWORD)
        self.kernel.OpenProcess.restype = w.HANDLE
        self.kernel.CloseHandle.argtypes = (w.HANDLE,)
        self.kernel.CloseHandle.restype = w.BOOL
        self.psapi.GetProcessMemoryInfo.argtypes = (
            w.HANDLE, ctypes.POINTER(Counters), w.DWORD,
        )
        self.psapi.GetProcessMemoryInfo.restype = w.BOOL
        self.handle = self.kernel.OpenProcess(0x0400 | 0x0010, False, pid)
        if not self.handle:
            raise ctypes.WinError(ctypes.get_last_error())
        self.peak = 0
        self.error = None

    def sample(self):
        if self.psapi.GetProcessMemoryInfo(
            self.handle, ctypes.byref(self.counters), self.counters.cb,
        ):
            self.peak = max(self.peak, int(self.counters.PeakWorkingSetSize))
        else:
            self.error = str(ctypes.WinError(ctypes.get_last_error()))

    def close(self):
        self.kernel.CloseHandle(self.handle)


def default_motor():
    dist = ROOT / 'derived/desktop-dist'
    if sys.platform == 'darwin':
        return dist / 'O Último Livro.app/Contents/Frameworks/brasil/runtime/llama-completion'
    if sys.platform == 'win32':
        return dist / 'UltimoLivro/_internal/brasil/runtime/llama-completion.exe'
    return ROOT / 'brasil/runtime/llama-completion'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--motor', type=Path, default=default_motor())
    parser.add_argument('--modelo', type=Path, default=ROOT / 'derived/desktop-model.gguf')
    args = parser.parse_args()
    command = [
        str(args.motor.resolve()), '-m', str(args.modelo.resolve()),
        '-c', '2048', '-n', '256', '-t', '2', '-ngl', '0',
        '--seed', '42', '--temp', '0.2', '--no-conversation',
        '--no-display-prompt', '--simple-io', '-p', PROMPT,
    ]
    result = {
        'sistema': sys.platform, 'argv': command, 'retorno': None,
        'resposta': '', 'pico_bytes': None, 'memoria_disponivel_antes': None,
        'medicao_indisponivel': None, 'timeout': False, 'ok': False,
        'metrica': 'PeakWorkingSetSize' if os.name == 'nt' else 'ru_maxrss',
    }
    sys.path.insert(0, str(ROOT))
    try:
        from brasil.plataforma import available_memory
        result['memoria_disponivel_antes'] = available_memory()
        if result['memoria_disponivel_antes'] is None:
            result['memoria_disponivel_motivo'] = 'Consulta do sistema indisponível.'
    except Exception as error:
        result['memoria_disponivel_motivo'] = str(error)

    resource = None
    baseline = None
    if os.name != 'nt':
        try:
            import resource
            baseline = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
        except (ImportError, OSError) as error:
            result['medicao_indisponivel'] = str(error)

    started = time.monotonic()
    stderr = ''
    tracker = None
    process = None
    try:
        with tempfile.TemporaryDirectory(prefix='ultimo-livro-memoria-') as tmp:
            stdout_path, stderr_path = Path(tmp) / 'stdout', Path(tmp) / 'stderr'
            try:
                with stdout_path.open('wb') as out, stderr_path.open('wb') as err:
                    options = {'creationflags': subprocess.CREATE_NO_WINDOW} if os.name == 'nt' else {}
                    process = subprocess.Popen(
                        command, stdin=subprocess.DEVNULL, stdout=out, stderr=err, **options,
                    )
                    if os.name == 'nt':
                        try:
                            tracker = WindowsPeak(process.pid)
                        except OSError as error:
                            result['medicao_indisponivel'] = str(error)
                    deadline = time.monotonic() + 180
                    while True:
                        if tracker:
                            tracker.sample()
                        if process.poll() is not None:
                            break
                        if time.monotonic() >= deadline:
                            result['timeout'] = True
                            process.kill()
                            process.wait(timeout=15)
                            break
                        time.sleep(.05)
                    result['retorno'] = process.wait(timeout=15)
                    if tracker:
                        tracker.sample()
            finally:
                if process is not None and process.poll() is None:
                    process.kill()
                    process.wait(timeout=15)
                result['resposta'] = stdout_path.read_text(encoding='utf-8', errors='replace') if stdout_path.exists() else ''
                stderr = stderr_path.read_text(encoding='utf-8', errors='replace') if stderr_path.exists() else ''
        if tracker:
            result['pico_bytes'] = tracker.peak or None
            if tracker.error:
                result['amostragem_aviso'] = tracker.error
        elif resource is not None and baseline is not None and process is not None:
            peak = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
            result['pico_filhos_antes'] = baseline * (1 if sys.platform == 'darwin' else 1024)
            if peak > baseline:
                result['pico_bytes'] = int(peak * (1 if sys.platform == 'darwin' else 1024))
            else:
                result['medicao_indisponivel'] = 'O pico acumulado de filhos anteriores impede atribuir o valor ao motor.'
    except Exception as error:
        result['erro'] = f'{type(error).__name__}: {error}'
    finally:
        if tracker:
            tracker.close()

    if not result['pico_bytes'] and not result['medicao_indisponivel']:
        result['medicao_indisponivel'] = 'Nenhum pico positivo foi obtido para o processo do motor.'
    result['segundos'] = round(time.monotonic() - started, 3)
    result['resposta_correta'] = (
        result['retorno'] == 0 and not result['timeout'] and 'brasília' in result['resposta'].casefold()
    )
    result['ok'] = result['resposta_correta'] and result['pico_bytes'] is not None and 'erro' not in result
    directory = ROOT / 'derived/desktop-results'
    directory.mkdir(parents=True, exist_ok=True)
    (directory / 'memoria-motor.stderr.log').write_text(stderr, encoding='utf-8')
    report = directory / 'memoria-motor.json'
    report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(report)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
