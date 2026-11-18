"""Curadoria brasileira de ações e leituras disponíveis na instalação."""

GUIDE_SITE_ID = 'ultimo-livro-preparacao'
GUIDE_SITE_URL = 'https://ultimo-livro-brasil.genuineoffer32.chatgpt.site/#preparacao'
REVIEW_DATE = '2026-11-18'

SOURCES = {
    GUIDE_SITE_ID: ('O Último Livro · Se prepare enquanto há tempo', GUIDE_SITE_URL),
    'situacao-energia': ('O Último Livro · Energia e luz', GUIDE_SITE_URL.replace('#preparacao', '#energia-emergencia')),
    'situacao-chuvas': ('Ministério da Saúde · Enchentes e inundações',
                       'https://miniapps.saude.gov.br/guia-clima/como-podemos-contribuir/populacao-em-geral/enchentes-e-inundacoes'),
    'situacao-agua': ('Ministério da Saúde · Cuidados com a água',
                     'https://www.gov.br/saude/pt-br/assuntos/saude-de-a-a-z/e/enchentes/cuidados-com-a-agua/cuidados-com-a-agua'),
    'situacao-calor': ('Ministério da Saúde · Ondas de calor',
                      'https://www.gov.br/saude/pt-br/assuntos/saude-de-a-a-z/o/ondas-de-calor'),
    'situacao-alimentos': ('Ministério da Saúde · Cuidados com os alimentos em enchentes',
                          'https://www.gov.br/saude/pt-br/assuntos/saude-de-a-a-z/e/enchentes/cuidados-com-os-alimentos'),
}

SITUACOES = (
    {
        'id': 'apagao',
        'titulo': 'Apagão',
        'resumo': 'Separe lanternas e pilhas. Carregue o celular e priorize os aparelhos essenciais. Guarde contatos em papel.',
        'leituras': [{'id': 'energia', 'pagina': 1}, {'id': 'offline', 'pagina': 1}],
        'fontes': ['situacao-energia'],
    },
    {
        'id': 'enchente',
        'titulo': 'Enchente e saída de casa',
        'resumo': 'Combine um ponto de encontro e deixe documentos e medicamentos de uso contínuo ao alcance. Siga a Defesa Civil e evite contato com água de inundação.',
        'leituras': [{'id': 'preparacao', 'pagina': 1}],
        'fontes': ['situacao-chuvas'],
    },
    {
        'id': 'agua',
        'titulo': 'Falta de água segura',
        'resumo': 'Separe uma reserva de água potável em recipientes limpos e fechados. Priorize água de fonte segura e evite usar água de inundação para beber, preparar alimentos ou fazer higiene.',
        'leituras': [{'id': 'preparacao', 'pagina': 1}],
        'fontes': ['situacao-agua', 'situacao-chuvas'],
    },
    {
        'id': 'calor',
        'titulo': 'Calor intenso',
        'resumo': 'Combine como verificar se crianças, pessoas idosas e quem mora sozinho estão bem. Procure sombra ou um local mais fresco, evite esforço nos horários mais quentes e beba água regularmente conforme sua orientação de saúde.',
        'leituras': [{'id': 'preparacao', 'pagina': 1}],
        'fontes': ['situacao-calor'],
    },
    {
        'id': 'alimentos',
        'titulo': 'Alimentos depois de uma enchente',
        'resumo': 'Separe e descarte alimentos que tiveram contato com água ou lama de enchente. Planeje uma reserva de alimentos estáveis que sua família costuma consumir.',
        'leituras': [{'id': 'preparacao', 'pagina': 1}],
        'fontes': ['situacao-alimentos'],
    },
)


def catalog():
    return [
        dict(situation, revisado=REVIEW_DATE,
             fontes=[{'id': ident, 'titulo': SOURCES[ident][0]} for ident in situation['fontes']])
        for situation in SITUACOES
    ]
