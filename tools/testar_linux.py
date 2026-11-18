#!/usr/bin/env python3
"""Valida janela, IA pelo formulário e referências da raiz Linux selecionada.

Use /usr/bin/python3 e um display real ou xvfb-run. Não baixa modelos nem usa
os dados do usuário; --raiz pode apontar para opt/ultimo-livro de um .deb extraído.
"""
import argparse
import json
import os
from pathlib import Path
import sys
import tempfile
import traceback

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / 'derived/desktop-results/linux-empacotado.json'
LIMIT_SECONDS = 360


def write_result(result):
    REPORT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')


def run(root, model, temporary):
    # Todos os módulos do produto e o motor precisam vir da raiz sob teste.
    sys.path[:0] = [str(root), str(root / 'app')]
    os.environ['ULTIMO_LIVRO_DATA'] = str(temporary / 'Dados da ação com espaços')
    os.environ['XDG_CACHE_HOME'] = str(temporary / 'Cache da ação com espaços')
    os.environ['ULTIMO_LIVRO_TEST_MODEL'] = str(model)
    sys.argv = ['ultimo-livro', '--autoteste', str(REPORT)]

    import gi
    gi.require_version('Gtk', '3.0')
    gi.require_version('WebKit2', '4.1')
    # Pycairo fornece Surface; o conversor GI separado é necessário para receber
    # a imagem real de WebKit2.get_snapshot_finish (pacote python3-gi-cairo).
    try:
        gi.require_foreign('cairo')
    except ImportError as error:
        raise RuntimeError('A captura requer python3-gi-cairo, além de python3-cairo.') from error
    from gi.repository import GLib, WebKit2
    import shell_linux
    from brasil import main
    from brasil.smoke_desktop import Check, seed

    for module in (main, shell_linux, sys.modules[Check.__module__]):
        if not Path(module.__file__).resolve().is_relative_to(root):
            raise RuntimeError('Um módulo foi carregado fora da raiz selecionada: ' + module.__file__)
    original_build = shell_linux.Shell.build
    original_quit = shell_linux.quit_app
    # O encerramento normal do shell usa os._exit; o teste precisa coletar o
    # relatório, capturar a janela e fechar o motor antes de limpar seus dados.
    shell_linux.quit_app = lambda: None
    state = {'finishing': False}

    def later(seconds, function):
        GLib.timeout_add(max(1, int(seconds * 1000)), lambda: (function(), False)[1])

    def build(shell, app):
        def finish(path):
            if state['finishing']:
                return
            state['finishing'] = True
            result = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {'ok': False}
            result.update(raiz=str(root), modelo=str(model), captura_da_janela=False)

            def complete(error=None):
                if state.get('completed'):
                    return
                state['completed'] = True
                if error:
                    result.update(ok=False, erro_captura=str(error))
                write_result(result)
                app.quit()

            def snapshot(view, task, data):
                try:
                    image = view.get_snapshot_finish(task)
                    image.write_to_png(str(REPORT.with_suffix('.png')))
                    result['captura_da_janela'] = True
                    complete()
                except Exception as error:
                    complete(error)

            later(10, lambda: complete('A captura da janela excedeu 10 segundos.'))
            if shell.view is None:
                complete('A janela não foi criada.')
            else:
                try:
                    shell.view.get_snapshot(WebKit2.SnapshotRegion.VISIBLE, WebKit2.SnapshotOptions.NONE, None, snapshot, None)
                except Exception as error:
                    complete(error)

        def evaluate(script, done):
            def completed(view, task, data):
                try:
                    value = view.evaluate_javascript_finish(task).to_boolean()
                except Exception as error:
                    done(None, error)
                else:
                    done(bool(value), None)
            shell.view.evaluate_javascript(script, -1, None, None, None, completed, None)

        def fail(message):
            if state['finishing']:
                return
            if hasattr(shell, 'linux_check'):
                shell.linux_check.finished = True
            write_result({'ok': False, 'erro': message})
            finish(REPORT)

        try:
            original_build(shell, app)
            expected_runner = (root / 'brasil/runtime/llama-completion').resolve()
            if Path(main.STORE.runner() or '').resolve() != expected_runner:
                raise RuntimeError('O motor não pertence à raiz selecionada.')
            seed(main)
            shell.linux_check = Check(main, evaluate, later, finish)
            later(3, shell.linux_check.tick)
            later(LIMIT_SECONDS, lambda: fail(f'A validação excedeu {LIMIT_SECONDS} segundos.'))
        except Exception:
            fail(traceback.format_exc())

    shell_linux.Shell.build = build
    try:
        main.main()
    finally:
        if main.STORE is not None:
            main.STORE.close()
        shell_linux.Shell.build = original_build
        shell_linux.quit_app = original_quit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--raiz', type=Path, default=ROOT, help='Raiz fonte ou opt/ultimo-livro do pacote extraído.')
    parser.add_argument('--modelo', type=Path, required=True, help='Modelo GGUF real Qwen3 0.6B Q8_0 já disponível.')
    args = parser.parse_args()
    root, model = args.raiz.resolve(), args.modelo.resolve()
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    for old in (REPORT, REPORT.with_suffix('.png')):
        old.unlink(missing_ok=True)
    try:
        for relative in ('brasil/main.py', 'brasil/smoke_desktop.py', 'app/shell_linux.py', 'brasil/runtime/llama-completion'):
            if not (root / relative).is_file():
                raise ValueError('Arquivo obrigatório ausente: ' + str(root / relative))
        if not os.access(root / 'brasil/runtime/llama-completion', os.X_OK):
            raise ValueError('O motor da raiz selecionada não é executável.')
        with model.open('rb') as source:
            if source.read(4) != b'GGUF':
                raise ValueError('O modelo informado não é GGUF.')
        with tempfile.TemporaryDirectory(prefix='Último Livro teste ação com espaços-') as temporary:
            run(root, model, Path(temporary))
        if not REPORT.exists():
            raise RuntimeError('O aplicativo não produziu relatório.')
        result = json.loads(REPORT.read_text(encoding='utf-8'))
        required = ('ok', 'ia_pela_interface', 'referencia_abrivel', 'chat_contextual', 'captura_da_janela')
        if not all(result.get(field) is True for field in required) or not result.get('ia'):
            raise RuntimeError('A janela, IA, referência ou captura não passou na validação.')
        if not REPORT.with_suffix('.png').is_file():
            raise RuntimeError('A captura da janela não foi produzida.')
    except Exception:
        result = json.loads(REPORT.read_text(encoding='utf-8')) if REPORT.exists() else {}
        result.update(ok=False, erro_validacao=traceback.format_exc(), raiz=str(root), modelo=str(model))
        write_result(result)
        print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
