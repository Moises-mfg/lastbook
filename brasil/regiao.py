"""Leituras locais e referências públicas para preparação no município."""

FONTES = {
    'alertas-cadastro': ('Defesa Civil Nacional · Cadastro de alertas',
        'https://www.gov.br/pt-br/servicos/solicitar-cadastro-para-recebimento-de-avisos-e-alertas-de-desastres'),
    'defesa-civil-alerta': ('MIDR · Defesa Civil Alerta',
        'https://www.gov.br/mdr/pt-br/assuntos/protecao-e-defesa-civil/defesa-civil-alerta'),
    'atlas-desastres': ('MIDR · Atlas Digital de Desastres',
        'https://atlasdigital.mdr.gov.br/paginas/downloads.xhtml'),
    'sgb-riscos': ('Serviço Geológico do Brasil · Cartografia de riscos',
        'https://www.sgb.gov.br/cartografia-de-riscos-geologicos'),
    'sgb-setores': ('Serviço Geológico do Brasil · Serviço de setores de risco',
        'https://geoportal.sgb.gov.br/server/rest/services/Hosted/risco_total/FeatureServer/0/query'),
    'cnes-estabelecimentos': ('Ministério da Saúde · Cadastro de estabelecimentos',
        'https://dadosabertos.saude.gov.br/dataset/cnes-cadastro-nacional-de-estabelecimentos-de-saude'),
    'clima-seca': ('Ministério da Saúde · Estiagem, seca e chuvas intensas',
        'https://www.gov.br/saude/pt-br/assuntos/saude-de-a-z/e/el-nino'),
    'clima-queimadas': ('Ministério da Saúde · Exposição à fumaça',
        'https://www.gov.br/saude/pt-br/assuntos/saude-de-a-z/q/queimadas'),
    'pos-enchente': ('Ministério da Saúde · Cuidados no pós-enchente',
        'https://www.gov.br/aids/pt-br/assuntos/noticias/2024/maio/ministerio-da-saude-orienta-sobre-cuidados-essenciais-a-populacao-no-pos-enchente'),
}

GUIAS = (
    ('enchentes', 'Enchentes e enxurradas', 'Guarde contatos, documentos e medicamentos essenciais para a família. Confirme com a Defesa Civil os pontos de encontro e evite contato com a água de inundação.', 'situacao-chuvas'),
    ('movimentos_de_massa', 'Encostas e deslizamentos', 'Conheça o plano de saída e procure os mapas e as orientações da Defesa Civil municipal. Siga as instruções de evacuação emitidas pelas autoridades.', 'sgb-riscos'),
    ('seca', 'Estiagem e isolamento', 'Planeje água potável, reposição de medicamentos e um contato de fora da comunidade. Guarde os contatos da prefeitura e do serviço de abastecimento antes de ficar sem conexão.', 'clima-seca'),
    ('incendios', 'Fumaça e queimadas', 'Acompanhe a orientação oficial e combine um local com ar mais limpo para pessoas sensíveis à fumaça. Reveja como avisar vizinhos ou familiares que morem sozinhos.', 'clima-queimadas'),
    ('calor', 'Calor intenso', 'Combine horários para verificar crianças, pessoas idosas e quem mora sozinho. Planeje acesso a sombra, ambiente fresco e água potável.', 'situacao-calor'),
)


def municipio_ativo(store):
    with store.db() as db:
        row = db.execute("SELECT value FROM settings WHERE key='regiao-municipio'").fetchone()
    return row[0] if row else None


def selecionar_municipio(store, ibge):
    from .pacotes import maps_catalog
    item = maps_catalog().get('map-city-' + ibge) if isinstance(ibge, str) else None
    if item is None:
        raise ValueError('Selecione um município do catálogo.')
    with store.db() as db:
        db.execute("INSERT OR REPLACE INTO settings VALUES ('regiao-municipio',?)", (ibge,))
    return {'ibge': ibge, 'name': item['name']}


def servicos_catalogados(ibge):
    import json
    from pathlib import Path
    path = Path(__file__).with_name('regiao_servicos.json')
    return json.loads(path.read_text(encoding='utf-8')).get(ibge, {}) if path.is_file() else {}
