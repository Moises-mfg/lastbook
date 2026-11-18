"""Consulta exclusivamente local ao recorte oficial do Atlas Digital do MIDR."""
from functools import lru_cache
import json
from pathlib import Path
import re

ARQUIVO = Path(__file__).with_name('regiao_atlas.json')
AVISO = ('Este histórico reúne registros municipais do Atlas; não é previsão nem classificação de risco. '
         'Ausência de registros neste recorte não significa ausência de risco. '
         'As contagens não representam eventos independentes entre municípios.')


@lru_cache(maxsize=1)
def _base():
    with ARQUIVO.open(encoding='utf-8') as source:
        value = json.load(source)
    if value.get('schema') != 1:
        raise ValueError('Versão do histórico regional não suportada.')
    return value


def historico(ibge):
    """Retorna resumo isolado por código IBGE de sete dígitos, sem acesso à rede.

    ``disponivel`` indica registros nas cinco categorias selecionadas, e não
    cobertura ou segurança do município. Códigos ausentes ou inválidos retornam
    ausência explícita; alterações no resultado não afetam consultas seguintes.
    """
    base = _base()
    code = str(ibge) if type(ibge) in (str, int) else ''
    valid = bool(re.fullmatch(r'[0-9]{7}', code))
    municipality = base['municipios'].get(code) if valid else None
    categories = []
    for index, category in enumerate(base['categorias']):
        count, first, last = municipality[2][index] if municipality else (0, None, None)
        categories.append({'id': category['id'], 'nome': category['nome'], 'registros': count,
                           'primeiro_ano': first, 'ultimo_ano': last, 'cobrade': list(category['cobrade'])})
    total = sum(category['registros'] for category in categories)
    return {
        'disponivel': total > 0, 'ibge': code if valid else None,
        'municipio': municipality[0] if municipality else None,
        'uf': municipality[1] if municipality else None,
        'fonte': base['fonte'], 'url': base['url'], 'arquivo_url': base['arquivo_url'],
        'versao': base['versao'], 'data_edicao': base['data_edicao'],
        'periodo': dict(base['periodo']), 'sha256': base['sha256'],
        'categorias': categories, 'total_registros': total, 'unidade': base['unidade'],
        'aviso': AVISO,
        'mensagem': ('Registros históricos disponíveis neste recorte.' if total else
                     'Sem registros disponíveis neste recorte do Atlas para este município.'),
    }
