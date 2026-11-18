"""Guias distribuídos com o aplicativo e abertos sem conexão."""
import os
from pathlib import Path
import shutil
import subprocess
import sys

from .guias_pdf_indice import PDF_TEXT


GUIDES = (
    ('preparacao', 'Organize a preparação da casa', 'Documentos, contatos e um plano que todos conhecem.'),
    ('energia', 'Iluminação e energia durante um apagão', 'Prepare lanternas, pilhas e carregadores para quando faltar luz.'),
    ('offline', 'Prepare sua biblioteca para ficar offline', 'Teste sua biblioteca sem internet e faça cópias dos arquivos importantes.'),
)
GUIDES_PATH = Path(__file__).parent / 'web' / 'guias'


def catalog():
    guides = []
    for ident, title, description in GUIDES:
        pages = sorted(GUIDES_PATH.glob(f'{ident}-[1-9].png'))
        if (GUIDES_PATH / f'{ident}.pdf').is_file() and pages:
            guides.append({'id': ident, 'titulo': title, 'descricao': description,
                           'paginas': [f'/ui/guias/{page.name}' for page in pages],
                           'texto_paginas': list(PDF_TEXT.get(ident, ()))})
    return guides


def open_pdf(ident):
    if ident not in {guide[0] for guide in GUIDES}:
        raise ValueError('Guia PDF não encontrado.')
    pdf = (GUIDES_PATH / f'{ident}.pdf').resolve()
    if not pdf.is_file():
        raise ValueError('Este guia PDF está ausente. A cópia para leitura fica na Biblioteca quando disponível.')
    try:
        if sys.platform == 'win32':
            os.startfile(str(pdf))
        else:
            executable = '/usr/bin/open' if sys.platform == 'darwin' else shutil.which('xdg-open')
            if not executable:
                raise ValueError('Nenhum leitor PDF foi configurado. O guia pode ser lido na Biblioteca.')
            subprocess.Popen([executable, str(pdf)], stdin=subprocess.DEVNULL,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError as error:
        raise ValueError('O sistema não abriu o leitor PDF. Leia o guia pela Biblioteca.') from error
    return {'mensagem': 'Guia PDF enviado ao leitor do sistema. O arquivo está neste computador.'}
