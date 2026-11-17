"""Catálogo editorial próprio. Pacotes ainda não publicados não viram downloads."""
PERFIS = {
    'leve': {'nome': 'Leve', 'ram_gib': 8, 'modelo': 'qwen3-0.6b', 'wiki': 'pt-mini', 'mapa': 'municipio', 'contexto': 2048},
    'moderada': {'nome': 'Moderada', 'ram_gib': 16, 'modelo': 'qwen3-4b', 'wiki': 'pt-nopic', 'mapa': 'estado', 'contexto': 4096},
    'parruda': {'nome': 'Parruda', 'ram_gib': 32, 'modelo': 'qwen3-14b', 'wiki': 'pt-maxi', 'mapa': 'brasil', 'contexto': 8192},
    'personalizada': {'nome': 'Personalizada', 'ram_gib': 0, 'modelo': 'sem-ia', 'wiki': 'pt-mini', 'mapa': 'municipio', 'contexto': 2048},
}
MODELOS = {
    'sem-ia': {'nome': 'Somente biblioteca', 'ram_gib': 0},
    'qwen3-0.6b': {'nome': 'Qwen3 0.6B · experimental', 'ram_gib': 8},
    'qwen3-4b': {'nome': 'Qwen3 4B · planejado', 'ram_gib': 16},
    'qwen3-14b': {'nome': 'Qwen3 14B · planejado', 'ram_gib': 32},
}
ESTADOS = {'AC':'Acre','AL':'Alagoas','AP':'Amapá','AM':'Amazonas','BA':'Bahia','CE':'Ceará','DF':'Distrito Federal',
           'ES':'Espírito Santo','GO':'Goiás','MA':'Maranhão','MT':'Mato Grosso','MS':'Mato Grosso do Sul','MG':'Minas Gerais',
           'PA':'Pará','PB':'Paraíba','PR':'Paraná','PE':'Pernambuco','PI':'Piauí','RJ':'Rio de Janeiro','RN':'Rio Grande do Norte',
           'RS':'Rio Grande do Sul','RO':'Rondônia','RR':'Roraima','SC':'Santa Catarina','SP':'São Paulo','SE':'Sergipe','TO':'Tocantins'}
WIKIS = {'pt-mini':'Português · introduções', 'pt-nopic':'Português · sem imagens', 'pt-maxi':'Português · completa',
         'en-mini':'Inglês · introduções', 'es-mini':'Espanhol · introduções'}
MAPAS = {'municipio':'Município e entorno', 'estado':'Um estado', 'brasil':'Brasil'}
GUIAS = [
    {'id':'primeiros-passos','titulo':'Prepare sua casa aos poucos','categoria':'Planejamento',
     'texto':'Comece pelos riscos da sua região: apagões, falta de água, enchentes ou necessidade de sair de casa. Faça uma lista das pessoas, dos animais e das necessidades de cada um. Combine contatos e um ponto de encontro. Registre o que já tem antes de comprar. Revise o plano com a família e teste a consulta deste aplicativo sem internet.',
     'fonte':'Defesa Civil do Paraná · Kit de emergência pessoal', 'url':'https://www.defesacivil.pr.gov.br/Pagina/Kit-de-Emergencia-pessoal'},
    {'id':'energia','titulo':'Iluminação, energia e cópias','categoria':'Energia',
     'texto':'Mantenha lanternas e cabos compatíveis em local conhecido. Confira a autonomia real dos equipamentos e carregue os dispositivos enquanto houver energia. Guarde uma cópia independente dos documentos e da biblioteca. Planeje o consumo antes de comprar uma estação de energia. Nunca use geradores ou equipamentos de combustão em ambiente fechado.',
     'fonte':'Defesa Civil · orientações de preparação', 'url':'https://www.defesacivil.pr.gov.br/Pagina/Kit-de-Emergencia-pessoal'},
    {'id':'enchentes','titulo':'Água e enchentes: consulte orientação oficial','categoria':'Água',
     'texto':'Evite contato com água de enchente e não atravesse áreas alagadas. Água aparentemente limpa pode estar contaminada. Guarde água potável em recipientes apropriados. Filtros de trilha não garantem a remoção de todos os contaminantes. Para desinfecção, siga a orientação oficial para o produto e a concentração exatos; não improvise dosagens.',
     'fonte':'Ministério da Saúde · cuidados com a água', 'url':'https://www.gov.br/saude/pt-br/assuntos/saude-de-a-a-z/e/enchentes/cuidados-com-a-agua/cuidados-com-a-agua'},
    {'id':'comunicacao','titulo':'Comunicação e LoRa','categoria':'Comunicação',
     'texto':'Combine previamente contatos e horários de comunicação. Guarde números importantes também em papel. LoRa é uma tecnologia de rádio, não acesso à internet. Meshtastic e MeshCore são ecossistemas diferentes; um nó isolado não cria uma rede. Antes de comprar, verifique a homologação do equipamento e as regras brasileiras. Teste a cobertura com outras pessoas antes de depender dela.',
     'fonte':'Anatel · equipamentos de radiação restrita', 'url':'https://informacoes.anatel.gov.br/legislacao/resolucoes/2017/936-resolucao-680'},
    {'id':'wikipedia','titulo':'Escolha sua Wikipedia offline','categoria':'Conhecimento',
     'texto':'Os arquivos ZIM podem conter enciclopédias inteiras. A variante mini guarda introduções e quadros; nopic guarda artigos sem imagens; maxi inclui imagens. Escolha idiomas e variantes conforme espaço e necessidade. Esta versão registra suas escolhas e permite pesquisar arquivos ZIM locais quando o leitor está instalado. Os pacotes brasileiros ainda não estão publicados.',
     'fonte':'Kiwix · variantes da Wikipedia', 'url':'https://get.kiwix.org/en/faq-items/what-do-mini-nopic-and-maxi-mean-in-the-wikipedia-zim-files/'},
]
COMPRAS = [
    {'id':'agua','titulo':'Água potável e recipientes próprios','grupo':'Essencial'},
    {'id':'comida','titulo':'Alimentos habituais e abridor manual','grupo':'Essencial'},
    {'id':'luz','titulo':'Lanterna e pilhas ou recarga compatível','grupo':'Essencial'},
    {'id':'energia','titulo':'Power bank e cabos dos seus aparelhos','grupo':'Essencial'},
    {'id':'radio','titulo':'Rádio receptor AM/FM','grupo':'Essencial'},
    {'id':'saude','titulo':'Curativos e medicamentos de uso contínuo','grupo':'Essencial'},
    {'id':'higiene','titulo':'Higiene e proteção de documentos','grupo':'Essencial'},
    {'id':'bota','titulo':'Bota, luvas e proteção adequada ao risco','grupo':'Conforme o risco'},
    {'id':'fogo','titulo':'Detector de fumaça e extintor adequado','grupo':'Conforme o risco'},
    {'id':'backup','titulo':'Cópia da biblioteca em SSD ou pendrive','grupo':'Continuidade'},
]
