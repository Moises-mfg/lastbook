#!/usr/bin/env python3
"""Gera o recorte municipal offline a partir do CSV oficial, sem dependências.

Baixe a URL em SOURCE_URL e execute:
    python tools/build_historico_atlas.py /caminho/BD_Atlas_1991_2025.csv

O SHA-256 fixa a edição importada. Atualizar edição exige revisar os metadados e
os códigos COBRADE abaixo. Nenhuma coluna descritiva de danos ou dado pessoal
é copiada; somente município, UF, categoria, contagem e anos são publicados.
"""
import argparse
import csv
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile

SOURCE_PAGE = 'https://atlasdigital.mdr.gov.br/paginas/downloads.xhtml'
SOURCE_URL = 'https://atlasdigital.mdr.gov.br/arquivos/2026/BD_Atlas_1991_2025_v1.1_2026.08.06_Consolidado.csv'
SOURCE_SHA256 = '78f7efd2d853021678ff4af891e938375b9fd0ce77026cbe052a53dae12bf425'
COBRADE_URL = 'https://www.gov.br/mdr/pt-br/centrais-de-conteudo/publicacoes/protecao-e-defesa-civil-sedec/DOCU_cobrade2.pdf'
PERIODO = {'inicio': 1991, 'fim': 2025}
CATEGORIAS = (
    {'id': 'enchentes', 'nome': 'Inundações, enxurradas e alagamentos', 'cobrade': ['12100', '12200', '12300']},
    {'id': 'movimentos_de_massa', 'nome': 'Movimentos de massa',
     'cobrade': ['11311', '11312', '11313', '11314', '11321', '11331', '11332', '11340']},
    {'id': 'seca', 'nome': 'Estiagem e seca', 'cobrade': ['14110', '14120']},
    {'id': 'incendios', 'nome': 'Incêndios florestais', 'cobrade': ['14131', '14132']},
    {'id': 'calor', 'nome': 'Ondas de calor', 'cobrade': ['13310']},
)
REQUIRED = {'Protocolo_S2iD', 'Nome_Municipio', 'Sigla_UF', 'Data_Evento', 'Cod_Cobrade', 'Cod_IBGE_Mun'}


def agregar(stream):
    """Agrega CSV já decodificado; falha em linhas inválidas ou duplicadas."""
    reader = csv.DictReader(stream, delimiter=';', strict=True)
    if not reader.fieldnames or not REQUIRED <= set(reader.fieldnames) or len(reader.fieldnames) != len(set(reader.fieldnames)):
        raise ValueError('Cabeçalho incompatível com a edição do Atlas.')
    codes = {code: index for index, category in enumerate(CATEGORIAS) for code in category['cobrade']}
    municipalities, protocols = {}, set()
    total, included = 0, 0
    for row in reader:
        if None in row or any(row.get(key) is None for key in REQUIRED):
            raise ValueError(f'Linha {reader.line_num}: colunas incompletas ou excedentes.')
        protocol = row['Protocolo_S2iD'].strip()
        ibge, name, uf = (row[key].strip() for key in ('Cod_IBGE_Mun', 'Nome_Municipio', 'Sigla_UF'))
        # A edição oficial contém seis UFs 'pa'; a normalização não altera a chave IBGE.
        uf = uf.upper()
        code = row['Cod_Cobrade'].strip()
        if (not protocol or protocol in protocols or not re.fullmatch(r'[0-9]{7}', ibge)
                or not name or not re.fullmatch(r'[A-Z]{2}', uf) or not re.fullmatch(r'[0-9]{5}', code)):
            raise ValueError(f'Linha {reader.line_num}: identificação inválida ou protocolo repetido.')
        protocols.add(protocol)
        try:
            date = datetime.datetime.strptime(row['Data_Evento'], '%d/%m/%Y').date()
        except ValueError as error:
            raise ValueError(f'Linha {reader.line_num}: data do evento inválida.') from error
        if not PERIODO['inicio'] <= date.year <= PERIODO['fim']:
            raise ValueError(f'Linha {reader.line_num}: evento fora do intervalo da edição.')
        total += 1
        # Os vetores seguem a ordem das categorias e contêm [registros, primeiro_ano, ultimo_ano].
        municipality = municipalities.setdefault(ibge, [name, uf, [[0, None, None] for _ in CATEGORIAS]])
        if municipality[1] != uf:
            raise ValueError(f'Linha {reader.line_num}: código IBGE com UFs conflitantes.')
        index = codes.get(code)
        if index is None:
            continue
        values = municipality[2][index]
        values[0] += 1
        values[1] = date.year if values[1] is None else min(values[1], date.year)
        values[2] = date.year if values[2] is None else max(values[2], date.year)
        included += 1
    if not total:
        raise ValueError('O arquivo do Atlas não contém registros.')
    return {'municipios': dict(sorted(municipalities.items())), 'registros_fonte': total, 'registros_recorte': included}


def construir(source):
    source = Path(source)
    digest = hashlib.sha256()
    with source.open('rb') as contents:
        for block in iter(lambda: contents.read(1024 * 1024), b''):
            digest.update(block)
    if digest.hexdigest() != SOURCE_SHA256:
        raise ValueError('SHA-256 diferente da edição oficial fixada; confira o arquivo antes de atualizar.')
    # O CSV oficial desta edição utiliza caracteres Windows-1252 e separador ponto e vírgula.
    with source.open('r', encoding='cp1252', newline='') as contents:
        result = agregar(contents)
    return {
        'schema': 1, 'fonte': 'Atlas Digital de Desastres no Brasil — MIDR',
        'url': SOURCE_PAGE, 'arquivo_url': SOURCE_URL, 'sha256': digest.hexdigest(),
        'versao': '1991–2025 v1.1 (2026-08-06)', 'data_edicao': '2026-08-06',
        'periodo': PERIODO, 'categorias': CATEGORIAS, 'cobrade_url': COBRADE_URL,
        'unidade': 'registros municipais do Atlas',
        'metodo': 'Uma linha por protocolo do CSV; agregação pelo Cod_IBGE_Mun e Cod_Cobrade, ano de Data_Evento. Inclui status Registro e Reconhecido. Sem inferência de risco ou deduplicação entre municípios.',
        'observacao': 'Calor inclui somente COBRADE 13310; baixa umidade (14140) não é contada como onda de calor. Categorias fora do recorte não entram nas contagens.',
        'formato_municipio': '[nome, uf, categorias na ordem declarada: [registros, primeiro_ano, ultimo_ano]]',
        **result,
    }


def escrever(destination, contents):
    destination = Path(destination)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=destination.parent,
                                         prefix='.atlas-', suffix='.tmp', delete=False) as output:
            temporary = Path(output.name)
            json.dump(contents, output, ensure_ascii=False, separators=(',', ':'), allow_nan=False)
            output.write('\n')
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, destination)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('csv', type=Path)
    parser.add_argument('--output', type=Path, default=Path(__file__).resolve().parents[1] / 'brasil' / 'regiao_atlas.json')
    args = parser.parse_args()
    result = construir(args.csv)
    escrever(args.output, result)
    print(f"{len(result['municipios'])} municípios; {result['registros_recorte']} registros no recorte de {result['registros_fonte']} registros oficiais.")


if __name__ == '__main__':
    main()
