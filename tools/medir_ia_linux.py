#!/usr/bin/env python3
"""Mede duas perguntas reais pelo Store e motor da raiz Linux selecionada.

Não baixa arquivos, não abre dados pessoais e não simula outro processador.
O diretório descartável é removido ao terminar; o modelo existente é ligado
por symlink, sem cópia nem alteração de permissões. Não mede a janela gráfica.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import sys
import tempfile
import time


ROOT = Path(__file__).resolve().parents[1]
QUESTIONS = (
    'Como preparar iluminação para uma falta de energia em casa?',
    'E como devo guardar os cabos e as lanternas mencionados?',
)


def memory():
    values = {}
    for line in Path('/proc/meminfo').read_text(encoding='utf-8').splitlines():
        key, value = line.split(':', 1)
        if key in ('MemTotal', 'MemAvailable', 'SwapTotal', 'SwapFree'):
            values[key] = int(value.split()[0]) * 1024
    return values


def host():
    cpu = None
    for line in Path('/proc/cpuinfo').read_text(encoding='utf-8').splitlines():
        if line.startswith(('model name', 'Hardware')) and ':' in line:
            cpu = line.split(':', 1)[1].strip()
            break
    return {'cpu': cpu, 'arquitetura': platform.machine(), 'nucleos_logicos': os.cpu_count(),
            'kernel': platform.release(), 'memoria_antes_bytes': memory()}


def sample_engine(proc):
    """Somente o PID do motor; não percorre processos externos ou filhos."""
    try:
        fields = {}
        for line in Path(f'/proc/{proc.pid}/status').read_text(encoding='utf-8').splitlines():
            if line.startswith(('VmRSS:', 'VmHWM:')):
                key, value = line.split(':', 1)
                fields[key] = int(value.split()[0]) * 1024
        return max(fields.values()) if fields else None
    except (OSError, ValueError):
        # O processo pode terminar entre a observação e a leitura de /proc.
        return None


def measure(store, question, interval, timeout):
    result = {'pergunta': question, 'memoria_antes_bytes': memory(),
              'pico_rss_motor_bytes': None, 'amostras_motor': 0, 'pids_motor': []}
    start = time.monotonic()
    store.ask({'pergunta': question})
    deadline = start + timeout
    while True:
        with store.lock:
            proc = store.proc
            job = dict(store.job)
        if proc is not None:
            if proc.pid not in result['pids_motor']:
                result['pids_motor'].append(proc.pid)
            rss = sample_engine(proc)
            if rss is not None:
                result['amostras_motor'] += 1
                result['pico_rss_motor_bytes'] = max(result['pico_rss_motor_bytes'] or 0, rss)
        if job['estado'] != 'executando':
            break
        if time.monotonic() >= deadline:
            store.close()
            job = {'estado': 'erro', 'mensagem': 'A medição excedeu o limite de tempo informado.'}
            break
        time.sleep(interval)
    result.update(latencia_segundos=round(time.monotonic() - start, 6), estado=job['estado'],
                  resposta=job.get('resposta'), fontes=job.get('fontes', []), erro=job.get('mensagem'))
    result['ok'] = (job['estado'] == 'concluido' and bool(job.get('resposta'))
                    and result['amostras_motor'] > 0)
    return result


def run(args, report):
    root, model = args.raiz.resolve(), args.modelo.resolve(strict=True)
    runner = root / 'brasil/runtime/llama-completion'
    for path in (root/'brasil/core.py', runner):
        if not path.is_file():
            raise ValueError('Arquivo obrigatório ausente na raiz selecionada: ' + str(path))
    if not os.access(runner, os.X_OK):
        raise ValueError('O motor empacotado não está executável; permissões não serão alteradas.')
    sys.path.insert(0, str(root))
    from brasil.core import Store
    from brasil import core
    if not Path(core.__file__).resolve().is_relative_to(root):
        raise ValueError('O Store foi importado de fora da raiz selecionada.')
    with model.open('rb') as source:
        if source.read(4) != b'GGUF':
            raise ValueError('O modelo informado não é GGUF.')
    if args.diretorio_teste:
        args.diretorio_teste.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='medicao-ia-', dir=args.diretorio_teste) as directory:
        store = Store(Path(directory)/'dados')
        try:
            store.save_choices({'perfil': 'personalizada', 'modelo': 'qwen3-0.6b', 'wikis': [], 'mapa': 'sem-mapas'})
            if Path(store.runner() or '').resolve() != runner.resolve():
                raise ValueError('O Store não selecionou o motor da raiz informada.')
            spec = store.model_spec()
            if model.stat().st_size != spec['size']:
                raise ValueError('O tamanho não corresponde ao Qwen3 0.6B do catálogo da raiz selecionada.')
            target = store.model_path()
            target.parent.mkdir(parents=True)
            try:
                target.symlink_to(model)
            except OSError as error:
                raise ValueError('A pasta de teste não aceita symlinks. Use --diretorio-teste /tmp; o modelo não será copiado.') from error
            report.update(raiz=str(root), motor=str(runner), modelo=str(model),
                          modelo_id=spec['id'], modelo_bytes=spec['size'],
                          contexto=spec['context'], threads_motor=2,
                          verificacao_modelo='Tamanho e SHA-256 pelo Store normal em cada pergunta.',
                          ligacao_modelo='symlink; nenhuma cópia ou alteração do arquivo original')
            for question in QUESTIONS:
                measured = measure(store, question, args.intervalo_ms/1000, args.limite_segundos)
                report['perguntas'].append(measured)
                if not measured['ok']:
                    break
        finally:
            store.close()
    report['ok'] = len(report['perguntas']) == 2 and all(p['ok'] for p in report['perguntas'])


def main():
    parser = argparse.ArgumentParser(description=__doc__, add_help=False)
    parser._optionals.title = 'opções'
    parser.add_argument('-h', '--help', action='help', help='Mostra esta ajuda e termina.')
    parser.add_argument('--raiz', type=Path, default=ROOT,
                        help='Raiz fonte ou opt/ultimo-livro de um pacote Linux extraído.')
    parser.add_argument('--modelo', type=Path, required=True, help='GGUF Qwen3 0.6B Q8_0 já presente.')
    parser.add_argument('--diretorio-teste', type=Path,
                        help='Base para dados descartáveis; padrão: pasta temporária do sistema. Deve aceitar symlinks. Subdiretório próprio será removido.')
    parser.add_argument('--saida', type=Path, help='Novo arquivo JSON; recusa sobrescrever. JSON também vai ao stdout.')
    parser.add_argument('--intervalo-ms', type=int, default=20, help='Amostragem do motor: 5–1000 ms (padrão 20).')
    parser.add_argument('--limite-segundos', type=int, default=900,
                        help='Limite por pergunta, incluindo hash: 1–3600 s (padrão 900). O motor mantém seu timeout normal.')
    args = parser.parse_args()
    if not sys.platform.startswith('linux'):
        parser.error('Esta medição usa /proc e requer Linux; não simula Linux em outros sistemas.')
    if not 5 <= args.intervalo_ms <= 1000 or not 1 <= args.limite_segundos <= 3600:
        parser.error('Intervalo ou limite fora da faixa permitida.')
    if args.saida and args.saida.exists():
        parser.error('--saida deve indicar um novo arquivo JSON.')
    report = {'ok': False, 'data_utc': datetime.now(timezone.utc).isoformat(), 'perguntas': [],
              'intervalo_amostragem_ms': args.intervalo_ms,
              'limite_segundos_por_pergunta': args.limite_segundos,
              'criterio_ok': 'Duas respostas não vazias, concluídas pelo motor, com RSS observado. Não avalia correção, qualidade ou adequação das respostas.',
              'escopo': 'Store e motor reais; sem interface gráfica e sem simulação de CPU.',
              'latencia': 'Tempo monotônico de ask até conclusão; inclui hash, fontes, carga do modelo, geração e persistência. Segunda pergunta usa histórico da primeira. Cache do SO não é esvaziado.',
              'rss': 'Maior VmHWM/VmRSS observado em /proc/PID/status. Limite inferior amostrado do pico do motor; pode perder o final. Exclui Python, interface e filhos. Não representa memória total do aplicativo.'}
    try:
        report['host'] = host()
        run(args, report)
    except (OSError, ValueError, RuntimeError, ImportError) as error:
        report['erro'] = str(error)
    except KeyboardInterrupt:
        report['erro'] = 'Medição interrompida pela pessoa.'
    serialized = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    if args.saida:
        try:
            with args.saida.open('x', encoding='utf-8') as output:
                output.write(serialized)
        except OSError as error:
            print('Não foi possível gravar o relatório: ' + str(error), file=sys.stderr)
            print(serialized, end='')
            return 1
    print(serialized, end='')
    return 0 if report['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
